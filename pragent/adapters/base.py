"""
Base classes for git server adapters
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class PRStatus(Enum):
    """Pull request status"""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    DRAFT = "draft"


@dataclass
class FileChange:
    """Represents a file change in a PR"""
    file_path: str
    change_type: str  # added, modified, deleted, renamed
    additions: int
    deletions: int
    diff: str
    old_path: Optional[str] = None  # for renamed files


@dataclass
class PRInfo:
    """Represents a pull request"""
    id: str
    title: str
    description: str
    author: str
    status: PRStatus
    source_branch: str
    target_branch: str
    created_at: str
    updated_at: str
    file_changes: List[FileChange]
    url: str
    raw_data: Dict[str, Any]


class GitAdapter(ABC):
    """Abstract base class for git server adapters"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._client = None
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the git server"""
        pass
    
    @abstractmethod
    async def fetch_pr(self, repo: str, pr_number: int) -> PRInfo:
        """Fetch a specific pull request"""
        pass
    
    @abstractmethod
    async def fetch_prs(self, repo: str, state: str = "open", limit: int = 10) -> List[PRInfo]:
        """Fetch multiple pull requests"""
        pass
    
    @abstractmethod
    async def post_comment(self, repo: str, pr_number: int, comment: str, 
                          file_path: Optional[str] = None, line_number: Optional[int] = None) -> str:
        """Post a comment to a pull request"""
        pass
    
    @abstractmethod
    async def get_file_content(self, repo: str, file_path: str, ref: str) -> str:
        """Get file content at a specific reference"""
        pass
    
    @abstractmethod
    async def create_review(self, repo: str, pr_number: int, 
                           comments: List[Dict[str, Any]], 
                           event: str = "COMMENT") -> str:
        """Create a review with multiple comments"""
        pass
    
    def _parse_file_changes(self, raw_changes: List[Dict[str, Any]]) -> List[FileChange]:
        """Parse raw file changes into FileChange objects"""
        changes = []
        for change in raw_changes:
            changes.append(FileChange(
                file_path=change.get('filename', ''),
                change_type=change.get('status', 'modified'),
                additions=change.get('additions', 0),
                deletions=change.get('deletions', 0),
                diff=change.get('patch', ''),
                old_path=change.get('previous_filename')
            ))
        return changes

