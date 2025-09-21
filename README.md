# PR Agent

A comprehensive Python-based pull request review agent capable of fetching pull requests from multiple git servers and generating detailed feedback on code quality, security, and best practices.

## Features

### Core Features
- **Multi-Server Support**: Works with GitHub, GitLab, and Bitbucket
- **Comprehensive Analysis**: Code quality, security, style, and maintainability checks
- **AI-Powered Insights**: Optional AI-driven suggestions for improvements
- **Automated Feedback**: Generate and post review comments
- **Flexible Configuration**: Customizable rules and thresholds
- **Multiple Output Formats**: JSON, Markdown reports

### Analysis Capabilities
- **Code Quality**: Pylint integration, complexity analysis, duplicate code detection
- **Security**: Bandit integration, custom security checks for vulnerabilities
- **Style**: Black, isort integration, custom style rules
- **AI Analysis**: Performance suggestions, readability improvements, security analysis

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd pragent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize configuration:
```bash
python main.py init-config
```

4. Edit the configuration file (`pragent.json`) with your API tokens and preferences.

## Quick Start

### Analyze a Single PR
```bash
python main.py analyze --server github --repo owner/repo --pr 123
```

### Analyze Multiple PRs
```bash
python main.py analyze-multiple --server github --repo owner/repo --limit 10
```

### Post Comments to PR
```bash
python main.py analyze --server github --repo owner/repo --pr 123 --post-comments
```

### Generate Report
```bash
python main.py analyze --server github --repo owner/repo --pr 123 --output report.json
```

## Configuration

The configuration file (`pragent.json`) allows you to customize:

### Git Server Settings
```json
{
  "git_servers": {
    "github": {
      "name": "GitHub",
      "base_url": "https://api.github.com",
      "token": "your_github_token"
    }
  }
}
```

### Analysis Settings
```json
{
  "analysis": {
    "enable_pylint": true,
    "enable_bandit": true,
    "enable_black": true,
    "min_complexity_score": 5,
    "max_line_length": 88
  }
}
```

### AI Settings
```json
{
  "ai": {
    "enabled": true,
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "api_key": "your_openai_api_key"
  }
}
```

## Supported Git Servers

### GitHub
- Uses PyGithub library
- Requires personal access token
- Supports inline comments and reviews

### GitLab
- Uses GitLab API v4
- Requires personal access token
- Supports merge request analysis

### Bitbucket
- Uses Bitbucket API v2
- Requires username and password/app password
- Supports pull request analysis

## Analysis Tools

### Code Quality
- **Pylint**: Static code analysis
- **AST Analysis**: Custom complexity and maintainability checks
- **Duplicate Code Detection**: Identifies repeated patterns

### Security
- **Bandit**: Security vulnerability scanner
- **Custom Checks**: Hardcoded secrets, SQL injection, unsafe operations
- **Input Validation**: Missing validation checks

### Style
- **Black**: Code formatting
- **isort**: Import sorting
- **Custom Rules**: Trailing whitespace, indentation, line length

### AI Analysis
- **OpenAI GPT**: Advanced code analysis and suggestions
- **Anthropic Claude**: Alternative AI provider
- **Performance Optimization**: AI-driven performance suggestions
- **Security Analysis**: AI-powered security vulnerability detection

## Output Formats

### JSON
Structured data format for programmatic processing:
```json
{
  "pr_info": {...},
  "file_analyses": {...},
  "overall_score": 85.5,
  "total_issues": 12,
  "feedback": {...}
}
```

### Markdown
Human-readable report format with sections for:
- PR information
- Summary statistics
- File-by-file analysis
- Detailed recommendations

## CI/CD Integration

PR Agent can be integrated into CI/CD pipelines:

1. **GitHub Actions**: Use as a workflow step
2. **GitLab CI**: Add to pipeline configuration
3. **Jenkins**: Integrate as a build step
4. **Webhook Support**: Automated analysis on PR events

## API Reference

### Core Classes

#### PRAgent
Main agent class for PR analysis:
```python
from pragent import PRAgent, Config

config = Config.from_file('pragent.json')
agent = PRAgent(config)

# Analyze a PR
result = await agent.analyze_pr('github', 'owner/repo', 123)

# Post review
await agent.post_review('github', 'owner/repo', 123, result)
```

#### Analyzers
Custom analyzers can be created by extending the base `Analyzer` class:
```python
from pragent.analyzers import Analyzer, AnalysisResult

class CustomAnalyzer(Analyzer):
    async def analyze(self, file_path: str, content: str) -> AnalysisResult:
        # Custom analysis logic
        pass
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the configuration examples

## Roadmap

- [ ] Additional git server support (Azure DevOps, etc.)
- [ ] More AI providers (local models, etc.)
- [ ] Advanced reporting features
- [ ] Plugin system for custom analyzers
- [ ] Web dashboard for analysis results
- [ ] Integration with more CI/CD platforms

