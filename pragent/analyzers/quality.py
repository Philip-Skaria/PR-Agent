"""
Code quality analyzer using pylint and other tools
"""

import ast
import subprocess
import tempfile
import os
from typing import List, Dict, Any
from pathlib import Path

from .base import Analyzer, AnalysisResult, Issue, IssueSeverity, IssueType


class QualityAnalyzer(Analyzer):
    """Code quality analyzer using pylint and AST analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.enable_pylint = config.get('enable_pylint', True)
        self.min_complexity = config.get('min_complexity_score', 5)
        self.max_line_length = config.get('max_line_length', 88)
    
    async def analyze(self, file_path: str, content: str) -> AnalysisResult:
        """Analyze code quality"""
        issues = []
        metrics = {}
        
        # Run pylint if enabled
        if self.enable_pylint and file_path.endswith('.py'):
            pylint_issues = await self._run_pylint(file_path, content)
            issues.extend(pylint_issues)
        
        # AST-based analysis
        if file_path.endswith('.py'):
            ast_issues, ast_metrics = await self._analyze_ast(file_path, content)
            issues.extend(ast_issues)
            metrics.update(ast_metrics)
        
        # Line length analysis
        length_issues = self._check_line_lengths(file_path, content)
        issues.extend(length_issues)
        
        # Calculate score
        score = self._calculate_score(issues)
        
        # Generate summary
        summary = self._generate_summary(issues, metrics)
        
        return AnalysisResult(
            file_path=file_path,
            issues=issues,
            metrics=metrics,
            score=score,
            summary=summary
        )
    
    async def _run_pylint(self, file_path: str, content: str) -> List[Issue]:
        """Run pylint analysis"""
        issues = []
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            # Run pylint
            result = subprocess.run([
                'pylint', temp_file, '--output-format=json'
            ], capture_output=True, text=True, timeout=30)
            
            # Parse pylint output
            if result.stdout:
                import json
                try:
                    pylint_results = json.loads(result.stdout)
                    for item in pylint_results:
                        severity_map = {
                            'error': IssueSeverity.HIGH,
                            'warning': IssueSeverity.MEDIUM,
                            'info': IssueSeverity.LOW,
                            'refactor': IssueSeverity.LOW
                        }
                        
                        issues.append(self._create_issue(
                            file_path=file_path,
                            line_number=item['line'],
                            severity=severity_map.get(item['type'], IssueSeverity.MEDIUM),
                            issue_type=IssueType.MAINTAINABILITY,
                            message=item['message'],
                            rule_id=item['message-id'],
                            suggestion=item.get('suggestion', ''),
                            column_number=item.get('column', None)
                        ))
                except json.JSONDecodeError:
                    pass
            
            # Clean up
            os.unlink(temp_file)
            
        except Exception as e:
            # If pylint fails, continue without it
            pass
        
        return issues
    
    async def _analyze_ast(self, file_path: str, content: str) -> tuple[List[Issue], Dict[str, Any]]:
        """Analyze code using AST"""
        issues = []
        metrics = {}
        
        try:
            tree = ast.parse(content)
            
            # Calculate cyclomatic complexity
            complexity = self._calculate_complexity(tree)
            metrics['cyclomatic_complexity'] = complexity
            
            if complexity > self.min_complexity:
                issues.append(self._create_issue(
                    file_path=file_path,
                    line_number=1,
                    severity=IssueSeverity.MEDIUM,
                    issue_type=IssueType.MAINTAINABILITY,
                    message=f"High cyclomatic complexity: {complexity}",
                    rule_id="high-complexity",
                    suggestion=f"Consider breaking down this function. Current complexity: {complexity}"
                ))
            
            # Check for long functions
            long_functions = self._find_long_functions(tree)
            for func_name, line_count in long_functions:
                if line_count > 50:  # Arbitrary threshold
                    issues.append(self._create_issue(
                        file_path=file_path,
                        line_number=1,  # Would need to track actual line
                        severity=IssueSeverity.LOW,
                        issue_type=IssueType.MAINTAINABILITY,
                        message=f"Long function '{func_name}': {line_count} lines",
                        rule_id="long-function",
                        suggestion="Consider breaking this function into smaller functions"
                    ))
            
            # Check for duplicate code patterns
            duplicate_patterns = self._find_duplicate_patterns(tree)
            for pattern, count in duplicate_patterns.items():
                if count > 3:  # Arbitrary threshold
                    issues.append(self._create_issue(
                        file_path=file_path,
                        line_number=1,
                        severity=IssueSeverity.LOW,
                        issue_type=IssueType.MAINTAINABILITY,
                        message=f"Potential code duplication: {pattern} appears {count} times",
                        rule_id="duplicate-code",
                        suggestion="Consider extracting common code into a function"
                    ))
            
        except SyntaxError as e:
            issues.append(self._create_issue(
                file_path=file_path,
                line_number=e.lineno or 1,
                severity=IssueSeverity.CRITICAL,
                issue_type=IssueType.BUG,
                message=f"Syntax error: {e.msg}",
                rule_id="syntax-error"
            ))
        
        return issues, metrics
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _find_long_functions(self, tree: ast.AST) -> List[tuple[str, int]]:
        """Find functions that are too long"""
        long_functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count lines in function (simplified)
                line_count = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 1
                long_functions.append((node.name, line_count))
        
        return long_functions
    
    def _find_duplicate_patterns(self, tree: ast.AST) -> Dict[str, int]:
        """Find potential duplicate code patterns"""
        patterns = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Look for repeated function calls
                if hasattr(node.func, 'id'):
                    key = f"call:{node.func.id}"
                    patterns[key] = patterns.get(key, 0) + 1
        
        return patterns
    
    def _check_line_lengths(self, file_path: str, content: str) -> List[Issue]:
        """Check for lines that are too long"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if len(line) > self.max_line_length:
                issues.append(self._create_issue(
                    file_path=file_path,
                    line_number=i,
                    severity=IssueSeverity.LOW,
                    issue_type=IssueType.STYLE,
                    message=f"Line too long: {len(line)} characters",
                    rule_id="line-too-long",
                    suggestion=f"Break this line into multiple lines (max {self.max_line_length} characters)"
                ))
        
        return issues
    
    def _generate_summary(self, issues: List[Issue], metrics: Dict[str, Any]) -> str:
        """Generate analysis summary"""
        if not issues:
            return "No quality issues found. Code looks good!"
        
        severity_counts = {}
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        summary_parts = []
        for severity, count in severity_counts.items():
            summary_parts.append(f"{count} {severity.value} issues")
        
        summary = f"Found {len(issues)} issues: {', '.join(summary_parts)}"
        
        if 'cyclomatic_complexity' in metrics:
            summary += f". Complexity: {metrics['cyclomatic_complexity']}"
        
        return summary
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return ['.py']

