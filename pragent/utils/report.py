"""
Report generation utilities
"""

import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from ..adapters import PRInfo
from ..analyzers import Issue


class ReportGenerator:
    """Generates various report formats"""
    
    def __init__(self, config):
        self.config = config
    
    async def generate_report(self, pr_info: PRInfo, file_analyses: Dict[str, Any], 
                            total_issues: List[Issue], total_metrics: Dict[str, Any], 
                            overall_score: float) -> Dict[str, Any]:
        """Generate comprehensive report"""
        
        report = {
            'metadata': self._generate_metadata(pr_info),
            'summary': self._generate_summary_stats(total_issues, overall_score),
            'file_analyses': self._generate_file_analyses(file_analyses),
            'issues': self._generate_issues_report(total_issues),
            'metrics': total_metrics,
            'recommendations': self._generate_recommendations(total_issues, overall_score),
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_metadata(self, pr_info: PRInfo) -> Dict[str, Any]:
        """Generate report metadata"""
        return {
            'pr_id': pr_info.id,
            'title': pr_info.title,
            'author': pr_info.author,
            'status': pr_info.status.value,
            'source_branch': pr_info.source_branch,
            'target_branch': pr_info.target_branch,
            'created_at': pr_info.created_at,
            'updated_at': pr_info.updated_at,
            'url': pr_info.url,
            'files_changed': len(pr_info.file_changes)
        }
    
    def _generate_summary_stats(self, total_issues: List[Issue], overall_score: float) -> Dict[str, Any]:
        """Generate summary statistics"""
        severity_counts = {}
        type_counts = {}
        
        for issue in total_issues:
            # Count by severity
            severity = issue.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by type
            issue_type = issue.issue_type.value
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        return {
            'overall_score': overall_score,
            'total_issues': len(total_issues),
            'issues_by_severity': severity_counts,
            'issues_by_type': type_counts,
            'quality_rating': self._get_quality_rating(overall_score)
        }
    
    def _generate_file_analyses(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate file analysis details"""
        file_reports = {}
        
        for file_path, analysis in file_analyses.items():
            issues = analysis['issues']
            metrics = analysis['metrics']
            score = analysis['score']
            
            # Group issues by severity
            severity_counts = {}
            for issue in issues:
                severity = issue.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            file_reports[file_path] = {
                'score': score,
                'total_issues': len(issues),
                'issues_by_severity': severity_counts,
                'metrics': metrics,
                'quality_rating': self._get_quality_rating(score)
            }
        
        return file_reports
    
    def _generate_issues_report(self, total_issues: List[Issue]) -> List[Dict[str, Any]]:
        """Generate detailed issues report"""
        issues_report = []
        
        for issue in total_issues:
            issues_report.append({
                'file_path': issue.file_path,
                'line_number': issue.line_number,
                'column_number': issue.column_number,
                'severity': issue.severity.value,
                'issue_type': issue.issue_type.value,
                'message': issue.message,
                'rule_id': issue.rule_id,
                'suggestion': issue.suggestion,
                'code_snippet': issue.code_snippet
            })
        
        # Sort by severity and line number
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        issues_report.sort(key=lambda x: (severity_order.get(x['severity'], 4), x['line_number']))
        
        return issues_report
    
    def _generate_recommendations(self, total_issues: List[Issue], overall_score: float) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Overall recommendations
        if overall_score >= 90:
            recommendations.append({
                'priority': 'low',
                'category': 'general',
                'title': 'Ready to merge',
                'description': 'This PR has excellent quality and is ready to merge.',
                'action': 'Approve and merge'
            })
        elif overall_score >= 75:
            recommendations.append({
                'priority': 'medium',
                'category': 'general',
                'title': 'Minor improvements needed',
                'description': 'Address minor issues before merging.',
                'action': 'Review and fix minor issues'
            })
        else:
            recommendations.append({
                'priority': 'high',
                'category': 'general',
                'title': 'Significant improvements needed',
                'description': 'Address critical and high severity issues before merging.',
                'action': 'Fix major issues and re-review'
            })
        
        # Issue-specific recommendations
        issue_types = {}
        for issue in total_issues:
            issue_type = issue.issue_type.value
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)
        
        for issue_type, issues in issue_types.items():
            if issue_type == 'security':
                recommendations.append({
                    'priority': 'high',
                    'category': 'security',
                    'title': 'Security vulnerabilities detected',
                    'description': f'Found {len(issues)} security issues that need immediate attention.',
                    'action': 'Review and fix security vulnerabilities'
                })
            elif issue_type == 'performance':
                recommendations.append({
                    'priority': 'medium',
                    'category': 'performance',
                    'title': 'Performance optimizations available',
                    'description': f'Found {len(issues)} performance-related issues.',
                    'action': 'Consider performance optimizations'
                })
            elif issue_type == 'maintainability':
                recommendations.append({
                    'priority': 'medium',
                    'category': 'maintainability',
                    'title': 'Code maintainability improvements',
                    'description': f'Found {len(issues)} maintainability issues.',
                    'action': 'Improve code structure and documentation'
                })
        
        return recommendations
    
    def _get_quality_rating(self, score: float) -> str:
        """Get quality rating based on score"""
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        else:
            return 'poor'
    
    async def save_report(self, report: Dict[str, Any], output_path: Path) -> None:
        """Save report to file"""
        if self.config.output_format == 'json':
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        elif self.config.output_format == 'markdown':
            markdown_content = self._generate_markdown_report(report)
            with open(output_path, 'w') as f:
                f.write(markdown_content)
        else:
            raise ValueError(f"Unsupported output format: {self.config.output_format}")
    
    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate markdown report"""
        md = f"# PR Analysis Report\n\n"
        md += f"**Generated**: {report['generated_at']}\n\n"
        
        # Metadata
        metadata = report['metadata']
        md += f"## PR Information\n\n"
        md += f"- **PR ID**: {metadata['pr_id']}\n"
        md += f"- **Title**: {metadata['title']}\n"
        md += f"- **Author**: {metadata['author']}\n"
        md += f"- **Status**: {metadata['status']}\n"
        md += f"- **Branches**: {metadata['source_branch']} → {metadata['target_branch']}\n"
        md += f"- **Files Changed**: {metadata['files_changed']}\n\n"
        
        # Summary
        summary = report['summary']
        md += f"## Summary\n\n"
        md += f"- **Overall Score**: {summary['overall_score']}/100 ({summary['quality_rating']})\n"
        md += f"- **Total Issues**: {summary['total_issues']}\n\n"
        
        if summary['issues_by_severity']:
            md += f"### Issues by Severity\n\n"
            for severity, count in summary['issues_by_severity'].items():
                md += f"- **{severity.capitalize()}**: {count}\n"
            md += "\n"
        
        if summary['issues_by_type']:
            md += f"### Issues by Type\n\n"
            for issue_type, count in summary['issues_by_type'].items():
                md += f"- **{issue_type.capitalize()}**: {count}\n"
            md += "\n"
        
        # File analyses
        md += f"## File Analyses\n\n"
        for file_path, analysis in report['file_analyses'].items():
            md += f"### {file_path}\n\n"
            md += f"- **Score**: {analysis['score']}/100 ({analysis['quality_rating']})\n"
            md += f"- **Issues**: {analysis['total_issues']}\n\n"
            
            if analysis['issues_by_severity']:
                md += f"**Issues by Severity**:\n"
                for severity, count in analysis['issues_by_severity'].items():
                    md += f"- {severity.capitalize()}: {count}\n"
                md += "\n"
        
        # Recommendations
        md += f"## Recommendations\n\n"
        for i, rec in enumerate(report['recommendations'], 1):
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(rec['priority'], '⚪')
            md += f"{i}. {priority_emoji} **{rec['title']}** ({rec['category']})\n"
            md += f"   - {rec['description']}\n"
            md += f"   - *Action*: {rec['action']}\n\n"
        
        return md

