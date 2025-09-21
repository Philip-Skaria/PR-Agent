"""
GitHub adapter for PR Agent
"""

import asyncio
from typing import List, Optional, Dict, Any
from github import Github, PullRequest
from github.GithubException import GithubException

from .base import GitAdapter, PRInfo, FileChange, PRStatus


class GitHubAdapter(GitAdapter):
    """GitHub adapter implementation"""
    
    async def connect(self) -> None:
        """Establish connection to GitHub"""
        token = self.config.get('token')
        if not token:
            raise ValueError("GitHub token is required")
        
        self._client = Github(token)
        # Test connection
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.get_user().login
            )
        except GithubException as e:
            raise ConnectionError(f"Failed to connect to GitHub: {e}")
    
    async def fetch_pr(self, repo: str, pr_number: int) -> PRInfo:
        """Fetch a specific pull request"""
        if not self._client:
            await self.connect()
        
        try:
            repository = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.get_repo(repo)
            )
            
            pr = await asyncio.get_event_loop().run_in_executor(
                None, lambda: repository.get_pull(pr_number)
            )
            
            # Get file changes
            files = await asyncio.get_event_loop().run_in_executor(
                None, lambda: pr.get_files()
            )
            
            file_changes = []
            for file in files:
                file_changes.append(FileChange(
                    file_path=file.filename,
                    change_type=file.status,
                    additions=file.additions,
                    deletions=file.deletions,
                    diff=file.patch or '',
                    old_path=file.previous_filename
                ))
            
            return PRInfo(
                id=str(pr.number),
                title=pr.title,
                description=pr.body or '',
                author=pr.user.login,
                status=PRStatus(pr.state.lower()),
                source_branch=pr.head.ref,
                target_branch=pr.base.ref,
                created_at=pr.created_at.isoformat(),
                updated_at=pr.updated_at.isoformat(),
                file_changes=file_changes,
                url=pr.html_url,
                raw_data=pr.raw_data
            )
            
        except GithubException as e:
            raise RuntimeError(f"Failed to fetch PR {pr_number}: {e}")
    
    async def fetch_prs(self, repo: str, state: str = "open", limit: int = 10) -> List[PRInfo]:
        """Fetch multiple pull requests"""
        if not self._client:
            await self.connect()
        
        try:
            repository = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.get_repo(repo)
            )
            
            prs = await asyncio.get_event_loop().run_in_executor(
                None, lambda: repository.get_pulls(state=state)[:limit]
            )
            
            pr_infos = []
            for pr in prs:
                pr_info = await self.fetch_pr(repo, pr.number)
                pr_infos.append(pr_info)
            
            return pr_infos
            
        except GithubException as e:
            raise RuntimeError(f"Failed to fetch PRs: {e}")
    
    async def post_comment(self, repo: str, pr_number: int, comment: str, 
                          file_path: Optional[str] = None, line_number: Optional[int] = None) -> str:
        """Post a comment to a pull request"""
        if not self._client:
            await self.connect()
        
        try:
            repository = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.get_repo(repo)
            )
            
            pr = await asyncio.get_event_loop().run_in_executor(
                None, lambda: repository.get_pull(pr_number)
            )
            
            if file_path and line_number:
                # Create inline comment
                comment_obj = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: pr.create_review_comment(comment, pr.get_commits()[0], file_path, line_number)
                )
            else:
                # Create general comment
                comment_obj = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: pr.create_issue_comment(comment)
                )
            
            return comment_obj.html_url
            
        except GithubException as e:
            raise RuntimeError(f"Failed to post comment: {e}")
    
    async def get_file_content(self, repo: str, file_path: str, ref: str) -> str:
        """Get file content at a specific reference"""
        if not self._client:
            await self.connect()
        
        try:
            repository = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.get_repo(repo)
            )
            
            content = await asyncio.get_event_loop().run_in_executor(
                None, lambda: repository.get_contents(file_path, ref=ref)
            )
            
            import base64
            return base64.b64decode(content.content).decode('utf-8')
            
        except GithubException as e:
            raise RuntimeError(f"Failed to get file content: {e}")
    
    async def create_review(self, repo: str, pr_number: int, 
                           comments: List[Dict[str, Any]], 
                           event: str = "COMMENT") -> str:
        """Create a review with multiple comments"""
        if not self._client:
            await self.connect()
        
        try:
            repository = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._client.get_repo(repo)
            )
            
            pr = await asyncio.get_event_loop().run_in_executor(
                None, lambda: repository.get_pull(pr_number)
            )
            
            # Convert comments to GitHub format
            github_comments = []
            for comment in comments:
                github_comment = {
                    'path': comment['file_path'],
                    'position': comment.get('line_number', 1),
                    'body': comment['body']
                }
                github_comments.append(github_comment)
            
            review = await asyncio.get_event_loop().run_in_executor(
                None, lambda: pr.create_review(
                    body="Automated code review",
                    event=event,
                    comments=github_comments
                )
            )
            
            return review.html_url
            
        except GithubException as e:
            raise RuntimeError(f"Failed to create review: {e}")
