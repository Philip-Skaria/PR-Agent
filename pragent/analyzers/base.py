"""
Base classes for code analyzers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class IssueSeverity(Enum):
    """Issue severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueType(Enum):
    """Issue types"""
    BUG = "bug"
    SECURITY = "security"
    STYLE = "style"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"


@dataclass
class Issue:
    """Represents a code issue found during analysis"""
    file_path: str
    line_number: int
    column_number: Optional[int]
    severity: IssueSeverity
    issue_type: IssueType
    message: str
    rule_id: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class AnalysisResult:
    """Result of code analysis"""
    file_path: str
    issues: List[Issue]
    metrics: Dict[str, Any]
    score: float  # 0-100
    summary: str


class Analyzer(ABC):
    """Abstract base class for code analyzers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def analyze(self, file_path: str, content: str) -> AnalysisResult:
        """Analyze a file and return results"""
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        pass
    
    def _calculate_score(self, issues: List[Issue]) -> float:
        """Calculate quality score based on issues"""
        if not issues:
            return 100.0
        
        # Weight issues by severity
        severity_weights = {
            IssueSeverity.LOW: 1,
            IssueSeverity.MEDIUM: 3,
            IssueSeverity.HIGH: 7,
            IssueSeverity.CRITICAL: 15
        }
        
        total_weight = sum(severity_weights[issue.severity] for issue in issues)
        max_possible_weight = len(issues) * 15  # All critical issues
        
        if max_possible_weight == 0:
            return 100.0
        
        score = max(0, 100 - (total_weight / max_possible_weight) * 100)
        return round(score, 2)
    
    def _create_issue(self, file_path: str, line_number: int, 
                     severity: IssueSeverity, issue_type: IssueType,
                     message: str, rule_id: str, 
                     suggestion: Optional[str] = None,
                     column_number: Optional[int] = None,
                     code_snippet: Optional[str] = None) -> Issue:
        """Helper method to create issues"""
        return Issue(
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            severity=severity,
            issue_type=issue_type,
            message=message,
            rule_id=rule_id,
            suggestion=suggestion,
            code_snippet=code_snippet
        )

