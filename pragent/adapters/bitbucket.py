"""
Bitbucket adapter for PR Agent
"""

import asyncio
import aiohttp
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

from .base import GitAdapter, PRInfo, FileChange, PRStatus


class BitbucketAdapter(GitAdapter):
    """Bitbucket adapter implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.bitbucket.org/2.0')
        self.username = config.get('username')
        self.password = config.get('password')
        self.session = None
    
    async def connect(self) -> None:
        """Establish connection to Bitbucket"""
        if not self.username or not self.password:
            raise ValueError("Bitbucket username and password are required")
        
        auth = aiohttp.BasicAuth(self.username, self.password)
        self.session = aiohttp.ClientSession(auth=auth)
        
        # Test connection
        try:
            async with self.session.get(f"{self.base_url}/user") as response:
                if response.status != 200:
                    raise ConnectionError(f"Failed to connect to Bitbucket: {response.status}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Bitbucket: {e}")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request to Bitbucket"""
        if not self.session:
            await self.connect()
        
        url = urljoin(f"{self.base_url}/", endpoint)
        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                raise RuntimeError(f"Bitbucket API error: {response.status}")
            return await response.json()
    
    async def fetch_pr(self, repo: str, pr_number: int) -> PRInfo:
        """Fetch a specific pull request"""
        try:
            pr_data = await self._make_request(f"repositories/{repo}/pullrequests/{pr_number}")
            
            # Get file changes
            changes_data = await self._make_request(f"repositories/{repo}/pullrequests/{pr_number}/diff")
            
            file_changes = []
            # Parse diff to extract file changes
            # This is a simplified implementation
            for line in changes_data.get('lines', []):
                if line.startswith('diff --git'):
                    # Extract file paths from diff header
                    parts = line.split()
                    if len(parts) >= 4:
                        old_path = parts[2].replace('a/', '')
                        new_path = parts[3].replace('b/', '')
                        
                        file_changes.append(FileChange(
                            file_path=new_path,
                            change_type='modified',
                            additions=0,  # Would need to parse diff
                            deletions=0,  # Would need to parse diff
                            diff='',  # Would need to parse diff
                            old_path=old_path if old_path != new_path else None
                        ))
            
            return PRInfo(
                id=str(pr_data['id']),
                title=pr_data['title'],
                description=pr_data.get('description', {}).get('raw', ''),
                author=pr_data['author']['display_name'],
                status=PRStatus(pr_data['state'].lower()),
                source_branch=pr_data['source']['branch']['name'],
                target_branch=pr_data['destination']['branch']['name'],
                created_at=pr_data['created_on'],
                updated_at=pr_data['updated_on'],
                file_changes=file_changes,
                url=pr_data['links']['html']['href'],
                raw_data=pr_data
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch PR {pr_number}: {e}")
    
    async def fetch_prs(self, repo: str, state: str = "OPEN", limit: int = 10) -> List[PRInfo]:
        """Fetch multiple pull requests"""
        try:
            params = {'state': state, 'pagelen': limit}
            prs_data = await self._make_request(f"repositories/{repo}/pullrequests", params)
            
            pr_infos = []
            for pr in prs_data.get('values', []):
                pr_info = await self.fetch_pr(repo, pr['id'])
                pr_infos.append(pr_info)
            
            return pr_infos
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch PRs: {e}")
    
    async def post_comment(self, repo: str, pr_number: int, comment: str, 
                          file_path: Optional[str] = None, line_number: Optional[int] = None) -> str:
        """Post a comment to a pull request"""
        try:
            data = {
                'content': {
                    'raw': comment
                }
            }
            
            if file_path and line_number:
                # Create inline comment
                data['inline'] = {
                    'path': file_path,
                    'line': line_number
                }
            
            url = f"{self.base_url}/repositories/{repo}/pullrequests/{pr_number}/comments"
            async with self.session.post(url, json=data) as response:
                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to post comment: {response.status}")
                
                result = await response.json()
                return result.get('links', {}).get('html', {}).get('href', '')
                
        except Exception as e:
            raise RuntimeError(f"Failed to post comment: {e}")
    
    async def get_file_content(self, repo: str, file_path: str, ref: str) -> str:
        """Get file content at a specific reference"""
        try:
            params = {'ref': ref}
            data = await self._make_request(f"repositories/{repo}/src/{ref}/{file_path}", params)
            
            # Bitbucket returns file content directly
            return data
            
        except Exception as e:
            raise RuntimeError(f"Failed to get file content: {e}")
    
    async def create_review(self, repo: str, pr_number: int, 
                           comments: List[Dict[str, Any]], 
                           event: str = "COMMENT") -> str:
        """Create a review with multiple comments"""
        # Bitbucket doesn't have a direct review concept like GitHub
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

