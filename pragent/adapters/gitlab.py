"""
GitLab adapter for PR Agent
"""

import asyncio
import aiohttp
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

from .base import GitAdapter, PRInfo, FileChange, PRStatus


class GitLabAdapter(GitAdapter):
    """GitLab adapter implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://gitlab.com')
        self.token = config.get('token')
        self.session = None
    
    async def connect(self) -> None:
        """Establish connection to GitLab"""
        if not self.token:
            raise ValueError("GitLab token is required")
        
        self.session = aiohttp.ClientSession(
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        # Test connection
        try:
            async with self.session.get(f"{self.base_url}/api/v4/user") as response:
                if response.status != 200:
                    raise ConnectionError(f"Failed to connect to GitLab: {response.status}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to GitLab: {e}")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request to GitLab"""
        if not self.session:
            await self.connect()
        
        url = urljoin(f"{self.base_url}/api/v4/", endpoint)
        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                raise RuntimeError(f"GitLab API error: {response.status}")
            return await response.json()
    
    async def fetch_pr(self, repo: str, pr_number: int) -> PRInfo:
        """Fetch a specific merge request"""
        try:
            # GitLab uses merge requests instead of pull requests
            mr_data = await self._make_request(f"projects/{repo.replace('/', '%2F')}/merge_requests/{pr_number}")
            
            # Get file changes
            changes_data = await self._make_request(f"projects/{repo.replace('/', '%2F')}/merge_requests/{pr_number}/changes")
            
            file_changes = []
            for change in changes_data.get('changes', []):
                file_changes.append(FileChange(
                    file_path=change['new_path'],
                    change_type=change['new_file'] and 'added' or 'modified',
                    additions=change.get('additions', 0),
                    deletions=change.get('deletions', 0),
                    diff=change.get('diff', ''),
                    old_path=change.get('old_path')
                ))
            
            return PRInfo(
                id=str(mr_data['iid']),
                title=mr_data['title'],
                description=mr_data.get('description', ''),
                author=mr_data['author']['username'],
                status=PRStatus(mr_data['state']),
                source_branch=mr_data['source_branch'],
                target_branch=mr_data['target_branch'],
                created_at=mr_data['created_at'],
                updated_at=mr_data['updated_at'],
                file_changes=file_changes,
                url=mr_data['web_url'],
                raw_data=mr_data
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch MR {pr_number}: {e}")
    
    async def fetch_prs(self, repo: str, state: str = "opened", limit: int = 10) -> List[PRInfo]:
        """Fetch multiple merge requests"""
        try:
            params = {'state': state, 'per_page': limit}
            mrs_data = await self._make_request(f"projects/{repo.replace('/', '%2F')}/merge_requests", params)
            
            mr_infos = []
            for mr in mrs_data:
                mr_info = await self.fetch_pr(repo, mr['iid'])
                mr_infos.append(mr_info)
            
            return mr_infos
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch MRs: {e}")
    
    async def post_comment(self, repo: str, pr_number: int, comment: str, 
                          file_path: Optional[str] = None, line_number: Optional[int] = None) -> str:
        """Post a comment to a merge request"""
        try:
            data = {
                'body': comment,
                'noteable_type': 'MergeRequest'
            }
            
            if file_path and line_number:
                data.update({
                    'position': {
                        'base_sha': '',  # Would need to get from MR
                        'head_sha': '',  # Would need to get from MR
                        'start_sha': '',  # Would need to get from MR
                        'position_type': 'text',
                        'new_path': file_path,
                        'new_line': line_number
                    }
                })
            
            url = f"{self.base_url}/api/v4/projects/{repo.replace('/', '%2F')}/merge_requests/{pr_number}/notes"
            async with self.session.post(url, json=data) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to post comment: {response.status}")
                
                result = await response.json()
                return result.get('web_url', '')
                
        except Exception as e:
            raise RuntimeError(f"Failed to post comment: {e}")
    
    async def get_file_content(self, repo: str, file_path: str, ref: str) -> str:
        """Get file content at a specific reference"""
        try:
            params = {'ref': ref}
            data = await self._make_request(f"projects/{repo.replace('/', '%2F')}/repository/files/{file_path.replace('/', '%2F')}", params)
            
            import base64
            return base64.b64decode(data['content']).decode('utf-8')
            
        except Exception as e:
            raise RuntimeError(f"Failed to get file content: {e}")
    
    async def create_review(self, repo: str, pr_number: int, 
                           comments: List[Dict[str, Any]], 
                           event: str = "COMMENT") -> str:
        """Create a review with multiple comments"""
        # GitLab doesn't have a direct review concept like GitHub
        # We'll post individual comments
        comment_urls = []
        for comment in comments:
            url = await self.post_comment(
                repo, pr_number, comment['body'], 
                comment.get('file_path'), comment.get('line_number')
            )
            comment_urls.append(url)
        
        return f"Posted {len(comment_urls)} comments"
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()

