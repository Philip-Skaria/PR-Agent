"""
Configuration management for PR Agent
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from pathlib import Path


class GitServerConfig(BaseModel):
    """Configuration for a specific git server"""
    name: str
    base_url: str
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = True


class AnalysisConfig(BaseModel):
    """Configuration for code analysis rules"""
    enable_pylint: bool = True
    enable_bandit: bool = True
    enable_black: bool = True
    enable_isort: bool = True
    enable_mypy: bool = True
    
    # Quality thresholds
    min_complexity_score: int = 5
    max_line_length: int = 88
    min_test_coverage: float = 0.8
    
    # Custom rules
    custom_rules: List[str] = Field(default_factory=list)
    
    # File patterns to analyze
    include_patterns: List[str] = Field(default_factory=lambda: ["*.py", "*.js", "*.ts", "*.java", "*.go"])
    exclude_patterns: List[str] = Field(default_factory=lambda: ["*.min.js", "*.bundle.js", "node_modules/**", "venv/**"])


class AIConfig(BaseModel):
    """Configuration for AI-powered analysis"""
    enabled: bool = False
    provider: str = "openai"  # openai, anthropic, local
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.1
    
    # AI analysis features
    enable_performance_suggestions: bool = True
    enable_security_analysis: bool = True
    enable_readability_improvements: bool = True


class Config(BaseModel):
    """Main configuration class"""
    # Git servers
    git_servers: Dict[str, GitServerConfig] = Field(default_factory=dict)
    
    # Analysis settings
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    
    # AI settings
    ai: AIConfig = Field(default_factory=AIConfig)
    
    # Output settings
    output_format: str = "json"  # json, markdown, html
    output_file: Optional[Path] = None
    verbose: bool = False
    
    # CI/CD settings
    ci_enabled: bool = False
    webhook_port: int = 8080
    webhook_secret: Optional[str] = None
    
    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Load configuration from file"""
        import json
        with open(config_path, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to file"""
        import json
        with open(config_path, 'w') as f:
            json.dump(self.dict(), f, indent=2, default=str)

