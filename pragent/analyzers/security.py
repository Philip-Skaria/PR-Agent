"""
Security analyzer using bandit and custom security checks
"""

import ast
import subprocess
import tempfile
import os
import re
from typing import List, Dict, Any

from .base import Analyzer, AnalysisResult, Issue, IssueSeverity, IssueType


class SecurityAnalyzer(Analyzer):
    """Security analyzer using bandit and custom checks"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.enable_bandit = config.get('enable_bandit', True)
        self.severity_threshold = config.get('severity_threshold', 'medium')
    
    async def analyze(self, file_path: str, content: str) -> AnalysisResult:
        """Analyze security issues"""
        issues = []
        metrics = {}
        
        # Run bandit if enabled and file is Python
        if self.enable_bandit and file_path.endswith('.py'):
            bandit_issues = await self._run_bandit(file_path, content)
            issues.extend(bandit_issues)
        
        # Custom security checks
        custom_issues = self._custom_security_checks(file_path, content)
        issues.extend(custom_issues)
        
        # Calculate security score
        score = self._calculate_security_score(issues)
        metrics['security_score'] = score
        
        # Generate summary
        summary = self._generate_security_summary(issues, metrics)
        
        return AnalysisResult(
            file_path=file_path,
            issues=issues,
            metrics=metrics,
            score=score,
            summary=summary
        )
    
    async def _run_bandit(self, file_path: str, content: str) -> List[Issue]:
        """Run bandit security analysis"""
        issues = []
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            # Run bandit
            result = subprocess.run([
                'bandit', temp_file, '-f', 'json', '-q'
            ], capture_output=True, text=True, timeout=30)
            
            # Parse bandit output
            if result.stdout:
                import json
                try:
                    bandit_results = json.loads(result.stdout)
                    for item in bandit_results.get('results', []):
                        severity_map = {
                            'HIGH': IssueSeverity.HIGH,
                            'MEDIUM': IssueSeverity.MEDIUM,
                            'LOW': IssueSeverity.LOW
                        }
                        
                        issues.append(self._create_issue(
                            file_path=file_path,
                            line_number=item['line_number'],
                            severity=severity_map.get(item['issue_severity'], IssueSeverity.MEDIUM),
                            issue_type=IssueType.SECURITY,
                            message=item['issue_text'],
                            rule_id=item['test_id'],
                            suggestion=item.get('issue_confidence', ''),
                            column_number=item.get('col_offset', None)
                        ))
                except json.JSONDecodeError:
                    pass
            
            # Clean up
            os.unlink(temp_file)
            
        except Exception as e:
            # If bandit fails, continue without it
            pass
        
        return issues
    
    def _custom_security_checks(self, file_path: str, content: str) -> List[Issue]:
        """Custom security checks"""
        issues = []
        lines = content.split('\n')
        
        # Check for hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'Hardcoded token'),
            (r'private_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded private key'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, message in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(self._create_issue(
                        file_path=file_path,
                        line_number=i,
                        severity=IssueSeverity.HIGH,
                        issue_type=IssueType.SECURITY,
                        message=message,
                        rule_id="hardcoded-secret",
                        suggestion="Use environment variables or secure configuration management",
                        code_snippet=line.strip()
                    ))
        
        # Check for SQL injection vulnerabilities
        sql_patterns = [
            (r'execute\s*\(\s*["\'].*%s.*["\']', 'Potential SQL injection'),
            (r'query\s*\(\s*["\'].*\+.*["\']', 'String concatenation in SQL query'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, message in sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(self._create_issue(
                        file_path=file_path,
                        line_number=i,
                        severity=IssueSeverity.HIGH,
                        issue_type=IssueType.SECURITY,
                        message=message,
                        rule_id="sql-injection",
                        suggestion="Use parameterized queries or ORM methods",
                        code_snippet=line.strip()
                    ))
        
        # Check for unsafe file operations
        unsafe_file_patterns = [
            (r'open\s*\(\s*[^,)]+\)', 'Unsafe file operation'),
            (r'os\.system\s*\(', 'Unsafe system call'),
            (r'eval\s*\(', 'Unsafe eval usage'),
            (r'exec\s*\(', 'Unsafe exec usage'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, message in unsafe_file_patterns:
                if re.search(pattern, line):
                    issues.append(self._create_issue(
                        file_path=file_path,
                        line_number=i,
                        severity=IssueSeverity.MEDIUM,
                        issue_type=IssueType.SECURITY,
                        message=message,
                        rule_id="unsafe-operation",
                        suggestion="Use safer alternatives and validate inputs",
                        code_snippet=line.strip()
                    ))
        
        # Check for missing input validation
        validation_patterns = [
            (r'request\.args\[', 'Direct access to request arguments'),
            (r'request\.form\[', 'Direct access to form data'),
            (r'request\.json\[', 'Direct access to JSON data'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, message in validation_patterns:
                if re.search(pattern, line):
                    issues.append(self._create_issue(
                        file_path=file_path,
                        line_number=i,
                        severity=IssueSeverity.MEDIUM,
                        issue_type=IssueType.SECURITY,
                        message=message,
                        rule_id="missing-validation",
                        suggestion="Add input validation and sanitization",
                        code_snippet=line.strip()
                    ))
        
        return issues
    
    def _calculate_security_score(self, issues: List[Issue]) -> float:
        """Calculate security score (higher is better)"""
        if not issues:
            return 100.0
        
        # Weight security issues more heavily
        security_weights = {
            IssueSeverity.LOW: 2,
            IssueSeverity.MEDIUM: 5,
            IssueSeverity.HIGH: 10,
            IssueSeverity.CRITICAL: 20
        }
        
        total_weight = sum(security_weights[issue.severity] for issue in issues)
        max_possible_weight = len(issues) * 20  # All critical issues
        
        if max_possible_weight == 0:
            return 100.0
        
        score = max(0, 100 - (total_weight / max_possible_weight) * 100)
        return round(score, 2)
    
    def _generate_security_summary(self, issues: List[Issue], metrics: Dict[str, Any]) -> str:
        """Generate security analysis summary"""
        if not issues:
            return "No security issues found. Code appears secure!"
        
        severity_counts = {}
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        summary_parts = []
        for severity, count in severity_counts.items():
            summary_parts.append(f"{count} {severity.value} security issues")
        
        summary = f"Found {len(issues)} security issues: {', '.join(summary_parts)}"
        
        if 'security_score' in metrics:
            summary += f". Security score: {metrics['security_score']}/100"
        
        return summary
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return ['.py', '.js', '.ts', '.java', '.go', '.php', '.rb']
