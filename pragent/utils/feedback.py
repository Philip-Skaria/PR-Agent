"""
Feedback generation utilities
"""

from typing import List, Dict, Any
from ..adapters import PRInfo
from ..analyzers import Issue


class FeedbackGenerator:
    """Generates human-readable feedback from analysis results"""
    
    def __init__(self, config):
        self.config = config
    
    async def generate_feedback(self, pr_info: PRInfo, file_analyses: Dict[str, Any], 
                              total_issues: List[Issue], overall_score: float) -> Dict[str, Any]:
        """Generate comprehensive feedback"""
        
        feedback = {
            'summary': self._generate_summary(pr_info, total_issues, overall_score),
            'file_feedback': self._generate_file_feedback(file_analyses),
            'recommendations': self._generate_recommendations(total_issues, overall_score),
            'scores': self._generate_score_breakdown(file_analyses, overall_score)
        }
        
        return feedback
    
    def _generate_summary(self, pr_info: PRInfo, total_issues: List[Issue], overall_score: float) -> str:
        """Generate overall summary"""
        if overall_score >= 90:
            status = "excellent"
            emoji = "🎉"
        elif overall_score >= 75:
            status = "good"
            emoji = "✅"
        elif overall_score >= 60:
            status = "fair"
            emoji = "⚠️"
        else:
            status = "needs improvement"
            emoji = "❌"
        
        summary = f"{emoji} **PR Analysis Summary**\n\n"
        summary += f"**Overall Score**: {overall_score}/100 ({status})\n"
        summary += f"**Total Issues**: {len(total_issues)}\n"
        summary += f"**Files Changed**: {len(pr_info.file_changes)}\n"
        summary += f"**Author**: {pr_info.author}\n\n"
        
        if total_issues:
            severity_counts = {}
            for issue in total_issues:
                severity_counts[issue.severity.value] = severity_counts.get(issue.severity.value, 0) + 1
            
            summary += "**Issues by Severity**:\n"
            for severity, count in sorted(severity_counts.items(), key=lambda x: ['critical', 'high', 'medium', 'low'].index(x[0])):
                summary += f"- {severity.capitalize()}: {count}\n"
        else:
            summary += "**No issues found! Great work!** 🎉\n"
        
        return summary
    
    def _generate_file_feedback(self, file_analyses: Dict[str, Any]) -> Dict[str, str]:
        """Generate feedback for each file"""
        file_feedback = {}
        
        for file_path, analysis in file_analyses.items():
            issues = analysis['issues']
            score = analysis['score']
            
            if not issues:
                file_feedback[file_path] = f"✅ **{file_path}**: No issues found (Score: {score}/100)"
            else:
                severity_counts = {}
                for issue in issues:
                    severity_counts[issue.severity.value] = severity_counts.get(issue.severity.value, 0) + 1
                
                feedback = f"⚠️ **{file_path}**: {len(issues)} issues (Score: {score}/100)\n"
                
                for severity, count in sorted(severity_counts.items(), key=lambda x: ['critical', 'high', 'medium', 'low'].index(x[0])):
                    feedback += f"  - {severity.capitalize()}: {count}\n"
                
                file_feedback[file_path] = feedback
        
        return file_feedback
    
    def _generate_recommendations(self, total_issues: List[Issue], overall_score: float) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if overall_score < 60:
            recommendations.append("🔧 **Priority**: Address critical and high severity issues immediately")
        
        # Group issues by type
        issue_types = {}
        for issue in total_issues:
            issue_type = issue.issue_type.value
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)
        
        # Generate type-specific recommendations
        if 'security' in issue_types:
            recommendations.append("🔒 **Security**: Review and fix security vulnerabilities")
        
        if 'performance' in issue_types:
            recommendations.append("⚡ **Performance**: Optimize code for better performance")
        
        if 'maintainability' in issue_types:
            recommendations.append("🔧 **Maintainability**: Improve code structure and documentation")
        
        if 'style' in issue_types:
            recommendations.append("🎨 **Style**: Run code formatters (black, isort) to fix style issues")
        
        if 'bug' in issue_types:
            recommendations.append("🐛 **Bugs**: Fix identified bugs before merging")
        
        # General recommendations
        if overall_score >= 90:
            recommendations.append("🎉 **Great job!** This PR is ready to merge")
        elif overall_score >= 75:
            recommendations.append("✅ **Good work!** Address minor issues and you're good to go")
        else:
            recommendations.append("⚠️ **Needs work**: Please address the identified issues before merging")
        
        return recommendations
    
    def _generate_score_breakdown(self, file_analyses: Dict[str, Any], overall_score: float) -> Dict[str, Any]:
        """Generate detailed score breakdown"""
        scores = {
            'overall': overall_score,
            'files': {},
            'average_file_score': 0,
            'lowest_score': 100,
            'highest_score': 0
        }
        
        if file_analyses:
            file_scores = [analysis['score'] for analysis in file_analyses.values()]
            scores['average_file_score'] = round(sum(file_scores) / len(file_scores), 2)
            scores['lowest_score'] = min(file_scores)
            scores['highest_score'] = max(file_scores)
            
            for file_path, analysis in file_analyses.items():
                scores['files'][file_path] = analysis['score']
        
        return scores

