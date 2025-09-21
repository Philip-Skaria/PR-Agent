"""
Main PR Agent class
"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

from .config import Config
from ..adapters import GitAdapter, PRInfo, GitHubAdapter, GitLabAdapter, BitbucketAdapter
from ..analyzers import QualityAnalyzer, SecurityAnalyzer, StyleAnalyzer, AIAnalyzer, AnalysisResult
from ..utils.feedback import FeedbackGenerator
from ..utils.report import ReportGenerator


class PRAgent:
    """Main PR Agent class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.adapters: Dict[str, GitAdapter] = {}
        self.analyzers: List[Any] = []
        self.feedback_generator = FeedbackGenerator(config)
        self.report_generator = ReportGenerator(config)
        
        # Initialize analyzers
        self._initialize_analyzers()
    
    def _initialize_analyzers(self):
        """Initialize code analyzers"""
        # Quality analyzer
        quality_config = {
            'enable_pylint': self.config.analysis.enable_pylint,
            'min_complexity_score': self.config.analysis.min_complexity_score,
            'max_line_length': self.config.analysis.max_line_length
        }
        self.analyzers.append(QualityAnalyzer(quality_config))
        
        # Security analyzer
        security_config = {
            'enable_bandit': self.config.analysis.enable_bandit,
            'severity_threshold': 'medium'
        }
        self.analyzers.append(SecurityAnalyzer(security_config))
        
        # Style analyzer
        style_config = {
            'enable_black': self.config.analysis.enable_black,
            'enable_isort': self.config.analysis.enable_isort,
            'max_line_length': self.config.analysis.max_line_length,
            'require_docstrings': False
        }
        self.analyzers.append(StyleAnalyzer(style_config))
        
        # AI analyzer (if enabled)
        if self.config.ai.enabled:
            ai_config = {
                'enabled': self.config.ai.enabled,
                'provider': self.config.ai.provider,
                'model': self.config.ai.model,
                'api_key': self.config.ai.api_key,
                'max_tokens': self.config.ai.max_tokens,
                'temperature': self.config.ai.temperature,
                'enable_performance_suggestions': self.config.ai.enable_performance_suggestions,
                'enable_security_analysis': self.config.ai.enable_security_analysis,
                'enable_readability_improvements': self.config.ai.enable_readability_improvements
            }
            self.analyzers.append(AIAnalyzer(ai_config))
    
    async def get_adapter(self, server_name: str) -> GitAdapter:
        """Get or create git server adapter"""
        if server_name not in self.adapters:
            if server_name not in self.config.git_servers:
                raise ValueError(f"Git server '{server_name}' not configured")
            
            server_config = self.config.git_servers[server_name]
            
            if server_name.lower() == 'github':
                adapter = GitHubAdapter(server_config.dict())
            elif server_name.lower() == 'gitlab':
                adapter = GitLabAdapter(server_config.dict())
            elif server_name.lower() == 'bitbucket':
                adapter = BitbucketAdapter(server_config.dict())
            else:
                raise ValueError(f"Unsupported git server: {server_name}")
            
            await adapter.connect()
            self.adapters[server_name] = adapter
        
        return self.adapters[server_name]
    
    async def analyze_pr(self, server_name: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Analyze a single pull request"""
        adapter = await self.get_adapter(server_name)
        
        # Fetch PR data
        pr_info = await adapter.fetch_pr(repo, pr_number)
        
        # Analyze each changed file
        file_analyses = {}
        total_issues = []
        total_metrics = {}
        
        for file_change in pr_info.file_changes:
            if file_change.change_type == 'deleted':
                continue
            
            # Get file content
            try:
                content = await adapter.get_file_content(repo, file_change.file_path, pr_info.source_branch)
                
                # Run all analyzers on the file
                file_issues = []
                file_metrics = {}
                
                for analyzer in self.analyzers:
                    if self._should_analyze_file(file_change.file_path, analyzer):
                        try:
                            result = await analyzer.analyze(file_change.file_path, content)
                            file_issues.extend(result.issues)
                            file_metrics.update(result.metrics)
                        except Exception as e:
                            if self.config.verbose:
                                print(f"Warning: Analyzer {analyzer.__class__.__name__} failed for {file_change.file_path}: {e}")
                
                file_analyses[file_change.file_path] = {
                    'issues': file_issues,
                    'metrics': file_metrics,
                    'score': self._calculate_file_score(file_issues)
                }
                
                total_issues.extend(file_issues)
                total_metrics.update(file_metrics)
                
            except Exception as e:
                if self.config.verbose:
                    print(f"Warning: Could not analyze {file_change.file_path}: {e}")
        
        # Generate overall analysis
        overall_score = self._calculate_overall_score(total_issues)
        
        # Generate feedback
        feedback = await self.feedback_generator.generate_feedback(
            pr_info, file_analyses, total_issues, overall_score
        )
        
        # Generate report
        report = await self.report_generator.generate_report(
            pr_info, file_analyses, total_issues, total_metrics, overall_score
        )
        
        return {
            'pr_info': pr_info,
            'file_analyses': file_analyses,
            'overall_score': overall_score,
            'total_issues': len(total_issues),
            'issues_by_severity': self._group_issues_by_severity(total_issues),
            'feedback': feedback,
            'report': report
        }
    
    async def analyze_multiple_prs(self, server_name: str, repo: str, 
                                 state: str = "open", limit: int = 10) -> List[Dict[str, Any]]:
        """Analyze multiple pull requests"""
        adapter = await self.get_adapter(server_name)
        
        # Fetch PRs
        pr_infos = await adapter.fetch_prs(repo, state, limit)
        
        # Analyze each PR
        results = []
        for pr_info in pr_infos:
            try:
                result = await self.analyze_pr(server_name, repo, int(pr_info.id))
                results.append(result)
            except Exception as e:
                if self.config.verbose:
                    print(f"Warning: Failed to analyze PR {pr_info.id}: {e}")
        
        return results
    
    async def post_review(self, server_name: str, repo: str, pr_number: int, 
                         analysis_result: Dict[str, Any]) -> str:
        """Post review comments to PR"""
        adapter = await self.get_adapter(server_name)
        
        # Generate inline comments
        comments = []
        for file_path, file_analysis in analysis_result['file_analyses'].items():
            for issue in file_analysis['issues']:
                if issue.severity.value in ['high', 'critical']:
                    comments.append({
                        'file_path': file_path,
                        'line_number': issue.line_number,
                        'body': f"**{issue.severity.value.upper()}**: {issue.message}\n\n{issue.suggestion or ''}"
                    })
        
        # Post comments
        if comments:
            review_url = await adapter.create_review(repo, pr_number, comments)
            return review_url
        else:
            # Post general comment
            general_comment = f"PR Analysis Complete\n\nOverall Score: {analysis_result['overall_score']}/100\nTotal Issues: {analysis_result['total_issues']}"
            comment_url = await adapter.post_comment(repo, pr_number, general_comment)
            return comment_url
    
    def _should_analyze_file(self, file_path: str, analyzer: Any) -> bool:
        """Check if file should be analyzed by the given analyzer"""
        file_ext = Path(file_path).suffix
        return file_ext in analyzer.get_supported_extensions()
    
    def _calculate_file_score(self, issues: List[Any]) -> float:
        """Calculate score for a single file"""
        if not issues:
            return 100.0
        
        # Weight issues by severity
        severity_weights = {
            'low': 1,
            'medium': 3,
            'high': 7,
            'critical': 15
        }
        
        total_weight = sum(severity_weights.get(issue.severity.value, 1) for issue in issues)
        max_possible_weight = len(issues) * 15  # All critical issues
        
        if max_possible_weight == 0:
            return 100.0
        
        score = max(0, 100 - (total_weight / max_possible_weight) * 100)
        return round(score, 2)
    
    def _calculate_overall_score(self, issues: List[Any]) -> float:
        """Calculate overall PR score"""
        if not issues:
            return 100.0
        
        # Calculate weighted average of file scores
        # This is a simplified implementation
        return self._calculate_file_score(issues)
    
    def _group_issues_by_severity(self, issues: List[Any]) -> Dict[str, int]:
        """Group issues by severity"""
        groups = {}
        for issue in issues:
            severity = issue.severity.value
            groups[severity] = groups.get(severity, 0) + 1
        return groups
    
    async def close(self):
        """Close all adapters"""
        for adapter in self.adapters.values():
            if hasattr(adapter, 'close'):
                await adapter.close()
