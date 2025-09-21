"""
Code style analyzer using black, isort, and custom style checks
"""

import subprocess
import tempfile
import os
import re
from typing import List, Dict, Any

from .base import Analyzer, AnalysisResult, Issue, IssueSeverity, IssueType


class StyleAnalyzer(Analyzer):
    """Code style analyzer using black, isort, and custom checks"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.enable_black = config.get('enable_black', True)
        self.enable_isort = config.get('enable_isort', True)
        self.max_line_length = config.get('max_line_length', 88)
        self.require_docstrings = config.get('require_docstrings', False)
    
    async def analyze(self, file_path: str, content: str) -> AnalysisResult:
        """Analyze code style"""
        issues = []
        metrics = {}
        
        # Run black if enabled and file is Python
        if self.enable_black and file_path.endswith('.py'):
            black_issues = await self._run_black(file_path, content)
            issues.extend(black_issues)
        
        # Run isort if enabled and file is Python
        if self.enable_isort and file_path.endswith('.py'):
            isort_issues = await self._run_isort(file_path, content)
            issues.extend(isort_issues)
        
        # Custom style checks
        custom_issues = self._custom_style_checks(file_path, content)
        issues.extend(custom_issues)
        
        # Calculate style score
        score = self._calculate_style_score(issues)
        metrics['style_score'] = score
        
        # Generate summary
        summary = self._generate_style_summary(issues, metrics)
        
        return AnalysisResult(
            file_path=file_path,
            issues=issues,
            metrics=metrics,
            score=score,
            summary=summary
        )
    
    async def _run_black(self, file_path: str, content: str) -> List[Issue]:
        """Run black formatting check"""
        issues = []
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            # Run black in check mode
            result = subprocess.run([
                'black', '--check', '--diff', temp_file
            ], capture_output=True, text=True, timeout=30)
            
            # If black suggests changes, create issues
            if result.returncode != 0 and result.stdout:
                # Parse diff output to find specific lines
                diff_lines = result.stdout.split('\n')
                current_line = 0
                
                for line in diff_lines:
                    if line.startswith('@@'):
                        # Parse line numbers from diff
                        match = re.search(r'\+(\d+)', line)
                        if match:
                            current_line = int(match.group(1))
                    elif line.startswith('+') and not line.startswith('+++'):
                        issues.append(self._create_issue(
                            file_path=file_path,
                            line_number=current_line,
                            severity=IssueSeverity.LOW,
                            issue_type=IssueType.STYLE,
                            message="Code formatting issue detected by black",
                            rule_id="black-formatting",
                            suggestion="Run 'black' to format this code",
                            code_snippet=line[1:].strip()
                        ))
                        current_line += 1
                    elif line.startswith('-') and not line.startswith('---'):
                        current_line += 1
            
            # Clean up
            os.unlink(temp_file)
            
        except Exception as e:
            # If black fails, continue without it
            pass
        
        return issues
    
    async def _run_isort(self, file_path: str, content: str) -> List[Issue]:
        """Run isort import sorting check"""
        issues = []
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            # Run isort in check mode
            result = subprocess.run([
                'isort', '--check-only', '--diff', temp_file
            ], capture_output=True, text=True, timeout=30)
            
            # If isort suggests changes, create issues
            if result.returncode != 0 and result.stdout:
                # Parse diff output
                diff_lines = result.stdout.split('\n')
                current_line = 0
                
                for line in diff_lines:
                    if line.startswith('@@'):
                        # Parse line numbers from diff
                        match = re.search(r'\+(\d+)', line)
                        if match:
                            current_line = int(match.group(1))
                    elif line.startswith('+') and not line.startswith('+++'):
                        issues.append(self._create_issue(
                            file_path=file_path,
                            line_number=current_line,
                            severity=IssueSeverity.LOW,
                            issue_type=IssueType.STYLE,
                            message="Import sorting issue detected by isort",
                            rule_id="isort-imports",
                            suggestion="Run 'isort' to sort imports",
                            code_snippet=line[1:].strip()
                        ))
                        current_line += 1
                    elif line.startswith('-') and not line.startswith('---'):
                        current_line += 1
            
            # Clean up
            os.unlink(temp_file)
            
        except Exception as e:
            # If isort fails, continue without it
            pass
        
        return issues
    
    def _custom_style_checks(self, file_path: str, content: str) -> List[Issue]:
        """Custom style checks"""
        issues = []
        lines = content.split('\n')
        
        # Check for trailing whitespace
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line:
                issues.append(self._create_issue(
                    file_path=file_path,
                    line_number=i,
                    severity=IssueSeverity.LOW,
                    issue_type=IssueType.STYLE,
                    message="Trailing whitespace",
                    rule_id="trailing-whitespace",
                    suggestion="Remove trailing whitespace",
                    code_snippet=line
                ))
        
        # Check for inconsistent indentation
        indentations = []
        for i, line in enumerate(lines, 1):
            if line.strip():  # Non-empty line
                indent = len(line) - len(line.lstrip())
                indentations.append((i, indent, line))
        
        if indentations:
            # Check for mixed tabs and spaces
            has_tabs = any('\t' in line for _, _, line in indentations)
            has_spaces = any(' ' in line and not line.startswith('\t') for _, _, line in indentations)
            
            if has_tabs and has_spaces:
                issues.append(self._create_issue(
                    file_path=file_path,
                    line_number=1,
                    severity=IssueSeverity.MEDIUM,
                    issue_type=IssueType.STYLE,
                    message="Mixed tabs and spaces for indentation",
                    rule_id="mixed-indentation",
                    suggestion="Use consistent indentation (preferably spaces)"
                ))
        
        # Check for missing docstrings (if required)
        if self.require_docstrings and file_path.endswith('.py'):
            docstring_issues = self._check_docstrings(file_path, content)
            issues.extend(docstring_issues)
        
        # Check for long lines
        for i, line in enumerate(lines, 1):
            if len(line) > self.max_line_length:
                issues.append(self._create_issue(
                    file_path=file_path,
                    line_number=i,
                    severity=IssueSeverity.LOW,
                    issue_type=IssueType.STYLE,
                    message=f"Line too long: {len(line)} characters",
                    rule_id="line-too-long",
                    suggestion=f"Break this line into multiple lines (max {self.max_line_length} characters)",
                    code_snippet=line.strip()
                ))
        
        # Check for unused imports (basic check)
        if file_path.endswith('.py'):
            unused_import_issues = self._check_unused_imports(file_path, content)
            issues.extend(unused_import_issues)
        
        return issues
    
    def _check_docstrings(self, file_path: str, content: str) -> List[Issue]:
        """Check for missing docstrings"""
        issues = []
        lines = content.split('\n')
        
        # Simple check for function/class definitions without docstrings
        in_function = False
        in_class = False
        function_start_line = 0
        class_start_line = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for function definition
            if re.match(r'def\s+\w+', stripped):
                in_function = True
                function_start_line = i
                in_class = False
            
            # Check for class definition
            elif re.match(r'class\s+\w+', stripped):
                in_class = True
                class_start_line = i
                in_function = False
            
            # Check for docstring after function/class
            elif in_function and stripped.startswith('"""') or stripped.startswith("'''"):
                in_function = False
            
            elif in_class and stripped.startswith('"""') or stripped.startswith("'''"):
                in_class = False
            
            # Check for end of function/class (next function/class or end of file)
            elif (in_function or in_class) and (stripped.startswith('def ') or stripped.startswith('class ') or i == len(lines)):
                if in_function:
                    issues.append(self._create_issue(
                        file_path=file_path,
                        line_number=function_start_line,
                        severity=IssueSeverity.LOW,
                        issue_type=IssueType.DOCUMENTATION,
                        message="Function missing docstring",
                        rule_id="missing-docstring",
                        suggestion="Add a docstring to describe what this function does"
                    ))
                    in_function = False
                
                if in_class:
                    issues.append(self._create_issue(
                        file_path=file_path,
                        line_number=class_start_line,
                        severity=IssueSeverity.LOW,
                        issue_type=IssueType.DOCUMENTATION,
                        message="Class missing docstring",
                        rule_id="missing-docstring",
                        suggestion="Add a docstring to describe what this class does"
                    ))
                    in_class = False
        
        return issues
    
    def _check_unused_imports(self, file_path: str, content: str) -> List[Issue]:
        """Basic check for unused imports"""
        issues = []
        lines = content.split('\n')
        
        # Find import statements
        imports = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith(('import ', 'from ')):
                # Extract imported names
                if line.strip().startswith('import '):
                    # Handle: import module, import module as alias
                    parts = line.strip().split('import ')[1].split(',')
                    for part in parts:
                        name = part.strip().split(' as ')[0].strip()
                        imports.append((i, name))
                
                elif line.strip().startswith('from '):
                    # Handle: from module import name1, name2
                    if ' import ' in line:
                        module_part, names_part = line.strip().split(' import ')
                        names = names_part.split(',')
                        for name in names:
                            name = name.strip().split(' as ')[0].strip()
                            imports.append((i, name))
        
        # Check if imports are used
        content_lower = content.lower()
        for line_num, import_name in imports:
            # Simple check - look for the import name in the code
            if import_name not in content_lower or f'import {import_name}' in content_lower:
                # This is a very basic check and might have false positives
                continue
            
            # More sophisticated check would be needed here
            # For now, we'll skip this to avoid false positives
        
        return issues
    
    def _calculate_style_score(self, issues: List[Issue]) -> float:
        """Calculate style score (higher is better)"""
        if not issues:
            return 100.0
        
        # Style issues are generally less critical
        style_weights = {
            IssueSeverity.LOW: 0.5,
            IssueSeverity.MEDIUM: 1,
            IssueSeverity.HIGH: 2,
            IssueSeverity.CRITICAL: 5
        }
        
        total_weight = sum(style_weights[issue.severity] for issue in issues)
        max_possible_weight = len(issues) * 5  # All critical issues
        
        if max_possible_weight == 0:
            return 100.0
        
        score = max(0, 100 - (total_weight / max_possible_weight) * 100)
        return round(score, 2)
    
    def _generate_style_summary(self, issues: List[Issue], metrics: Dict[str, Any]) -> str:
        """Generate style analysis summary"""
        if not issues:
            return "No style issues found. Code follows good style practices!"
        
        severity_counts = {}
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        summary_parts = []
        for severity, count in severity_counts.items():
            summary_parts.append(f"{count} {severity.value} style issues")
        
        summary = f"Found {len(issues)} style issues: {', '.join(summary_parts)}"
        
        if 'style_score' in metrics:
            summary += f". Style score: {metrics['style_score']}/100"
        
        return summary
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return ['.py', '.js', '.ts', '.java', '.go', '.php', '.rb', '.cpp', '.c', '.h']

