"""
AI-powered analyzer for advanced code analysis
"""

import asyncio
import json
from typing import List, Dict, Any, Optional

from .base import Analyzer, AnalysisResult, Issue, IssueSeverity, IssueType


class AIAnalyzer(Analyzer):
    """AI-powered analyzer for advanced code analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.enabled = config.get('enabled', False)
        self.provider = config.get('provider', 'openai')
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.api_key = config.get('api_key')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.1)
        
        # AI analysis features
        self.enable_performance = config.get('enable_performance_suggestions', True)
        self.enable_security = config.get('enable_security_analysis', True)
        self.enable_readability = config.get('enable_readability_improvements', True)
    
    async def analyze(self, file_path: str, content: str) -> AnalysisResult:
        """Analyze code using AI"""
        if not self.enabled or not self.api_key:
            return AnalysisResult(
                file_path=file_path,
                issues=[],
                metrics={},
                score=100.0,
                summary="AI analysis disabled"
            )
        
        issues = []
        metrics = {}
        
        try:
            # Generate AI analysis
            ai_analysis = await self._analyze_with_ai(file_path, content)
            
            # Parse AI response into issues
            issues = self._parse_ai_response(ai_analysis, file_path)
            
            # Calculate metrics
            metrics = self._calculate_ai_metrics(issues)
            
            # Calculate score
            score = self._calculate_score(issues)
            
            # Generate summary
            summary = self._generate_ai_summary(issues, metrics)
            
        except Exception as e:
            # If AI analysis fails, return empty result
            issues = []
            metrics = {'ai_error': str(e)}
            score = 100.0
            summary = f"AI analysis failed: {e}"
        
        return AnalysisResult(
            file_path=file_path,
            issues=issues,
            metrics=metrics,
            score=score,
            summary=summary
        )
    
    async def _analyze_with_ai(self, file_path: str, content: str) -> str:
        """Analyze code using AI provider"""
        if self.provider == 'openai':
            return await self._analyze_with_openai(file_path, content)
        elif self.provider == 'anthropic':
            return await self._analyze_with_anthropic(file_path, content)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
    
    async def _analyze_with_openai(self, file_path: str, content: str) -> str:
        """Analyze code using OpenAI API"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            prompt = self._build_analysis_prompt(file_path, content)
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer. Analyze the provided code and identify issues, improvements, and suggestions. Return your analysis in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            raise RuntimeError("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")
    
    async def _analyze_with_anthropic(self, file_path: str, content: str) -> str:
        """Analyze code using Anthropic API"""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            prompt = self._build_analysis_prompt(file_path, content)
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": f"You are an expert code reviewer. Analyze the provided code and identify issues, improvements, and suggestions. Return your analysis in JSON format.\n\n{prompt}"}
                ]
            )
            
            return response.content[0].text
            
        except ImportError:
            raise RuntimeError("Anthropic library not installed. Install with: pip install anthropic")
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")
    
    def _build_analysis_prompt(self, file_path: str, content: str) -> str:
        """Build analysis prompt for AI"""
        features = []
        if self.enable_performance:
            features.append("performance optimization")
        if self.enable_security:
            features.append("security vulnerabilities")
        if self.enable_readability:
            features.append("code readability and maintainability")
        
        features_str = ", ".join(features)
        
        prompt = f"""
Analyze the following code file: {file_path}

Focus on: {features_str}

Code:
```python
{content}
```

Please provide your analysis in the following JSON format:
{{
    "issues": [
        {{
            "line_number": 1,
            "severity": "low|medium|high|critical",
            "issue_type": "bug|security|performance|maintainability|style",
            "message": "Description of the issue",
            "suggestion": "How to fix or improve",
            "rule_id": "unique-rule-id"
        }}
    ],
    "metrics": {{
        "complexity": "estimated complexity level",
        "maintainability": "estimated maintainability level",
        "performance": "estimated performance level"
    }},
    "summary": "Overall assessment of the code"
}}

Be thorough but concise. Focus on actionable improvements.
"""
        return prompt
    
    def _parse_ai_response(self, ai_response: str, file_path: str) -> List[Issue]:
        """Parse AI response into Issue objects"""
        issues = []
        
        try:
            # Try to extract JSON from response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = ai_response[json_start:json_end]
                data = json.loads(json_str)
                
                for issue_data in data.get('issues', []):
                    severity_map = {
                        'low': IssueSeverity.LOW,
                        'medium': IssueSeverity.MEDIUM,
                        'high': IssueSeverity.HIGH,
                        'critical': IssueSeverity.CRITICAL
                    }
                    
                    issue_type_map = {
                        'bug': IssueType.BUG,
                        'security': IssueType.SECURITY,
                        'performance': IssueType.PERFORMANCE,
                        'maintainability': IssueType.MAINTAINABILITY,
                        'style': IssueType.STYLE
                    }
                    
                    issues.append(self._create_issue(
                        file_path=file_path,
                        line_number=issue_data.get('line_number', 1),
                        severity=severity_map.get(issue_data.get('severity', 'medium'), IssueSeverity.MEDIUM),
                        issue_type=issue_type_map.get(issue_data.get('issue_type', 'maintainability'), IssueType.MAINTAINABILITY),
                        message=issue_data.get('message', 'AI detected issue'),
                        rule_id=issue_data.get('rule_id', 'ai-analysis'),
                        suggestion=issue_data.get('suggestion'),
                        column_number=None
                    ))
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # If parsing fails, create a generic issue
            issues.append(self._create_issue(
                file_path=file_path,
                line_number=1,
                severity=IssueSeverity.LOW,
                issue_type=IssueType.MAINTAINABILITY,
                message="AI analysis completed but response format was unexpected",
                rule_id="ai-parse-error",
                suggestion="Check AI response format"
            ))
        
        return issues
    
    def _calculate_ai_metrics(self, issues: List[Issue]) -> Dict[str, Any]:
        """Calculate AI-specific metrics"""
        metrics = {}
        
        if not issues:
            metrics['ai_confidence'] = 100.0
            metrics['ai_analysis_quality'] = 'excellent'
        else:
            # Calculate confidence based on issue severity distribution
            severity_counts = {}
            for issue in issues:
                severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
            
            # Higher confidence if issues are well-distributed across severities
            total_issues = len(issues)
            if total_issues > 0:
                diversity_score = len(severity_counts) / 4.0  # 4 severity levels
                metrics['ai_confidence'] = min(100.0, diversity_score * 100)
            else:
                metrics['ai_confidence'] = 100.0
            
            # Determine analysis quality
            if total_issues == 0:
                metrics['ai_analysis_quality'] = 'excellent'
            elif total_issues <= 3:
                metrics['ai_analysis_quality'] = 'good'
            elif total_issues <= 7:
                metrics['ai_analysis_quality'] = 'fair'
            else:
                metrics['ai_analysis_quality'] = 'needs_improvement'
        
        return metrics
    
    def _generate_ai_summary(self, issues: List[Issue], metrics: Dict[str, Any]) -> str:
        """Generate AI analysis summary"""
        if not issues:
            return "AI analysis found no issues. Code appears to be well-written!"
        
        severity_counts = {}
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        summary_parts = []
        for severity, count in severity_counts.items():
            summary_parts.append(f"{count} {severity.value} issues")
        
        summary = f"AI analysis found {len(issues)} issues: {', '.join(summary_parts)}"
        
        if 'ai_confidence' in metrics:
            summary += f". AI confidence: {metrics['ai_confidence']:.1f}%"
        
        if 'ai_analysis_quality' in metrics:
            summary += f". Analysis quality: {metrics['ai_analysis_quality']}"
        
        return summary
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return ['.py', '.js', '.ts', '.java', '.go', '.php', '.rb', '.cpp', '.c', '.h', '.cs', '.swift', '.kt']

