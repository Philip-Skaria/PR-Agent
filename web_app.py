#!/usr/bin/env python3
"""
Simple web interface for PR Agent
"""

from flask import Flask, render_template_string, request, jsonify
import asyncio
from pragent import PRAgent, Config

app = Flask(__name__)

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PR Agent - Pull Request Analysis</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 10px; }
        input, select { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .result { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
        .error { border-left-color: #dc3545; }
        .success { border-left-color: #28a745; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 PR Agent</h1>
        <p>Analyze pull requests from GitHub, GitLab, and Bitbucket</p>
        
        <form method="POST">
            <label>Git Server:</label>
            <select name="server">
                <option value="github">GitHub</option>
                <option value="gitlab">GitLab</option>
                <option value="bitbucket">Bitbucket</option>
            </select>
            
            <label>Repository (owner/repo):</label>
            <input type="text" name="repo" placeholder="microsoft/vscode" required>
            
            <label>Pull Request Number:</label>
            <input type="number" name="pr" placeholder="123" required>
            
            <button type="submit">Analyze PR</button>
        </form>
        
        {% if result %}
        <div class="result {{ result.type }}">
            <h3>{{ result.title }}</h3>
            <p>{{ result.message }}</p>
            {% if result.details %}
            <pre>{{ result.details }}</pre>
            {% endif %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/', methods=['POST'])
def analyze_pr():
    try:
        server = request.form.get('server')
        repo = request.form.get('repo')
        pr_number = int(request.form.get('pr'))
        
        # Create basic config
        config = Config()
        config.git_servers = {
            'github': {
                'name': 'GitHub',
                'base_url': 'https://api.github.com',
                'token': 'demo_token'  # This would need to be set properly
            }
        }
        
        # For demo purposes, return a mock result
        result = {
            'type': 'success',
            'title': f'PR Analysis Complete',
            'message': f'Analyzed PR #{pr_number} from {repo} on {server}',
            'details': f'This is a demo result. To get real analysis, configure API tokens in the backend.'
        }
        
        return render_template_string(HTML_TEMPLATE, result=result)
        
    except Exception as e:
        result = {
            'type': 'error',
            'title': 'Analysis Failed',
            'message': f'Error: {str(e)}',
            'details': 'Please check your inputs and try again.'
        }
        return render_template_string(HTML_TEMPLATE, result=result)

@app.route('/api/analyze')
def api_analyze():
    """API endpoint for programmatic access"""
    return jsonify({
        'status': 'success',
        'message': 'PR Agent API is running',
        'endpoints': {
            'analyze': '/api/analyze?server=github&repo=owner/repo&pr=123',
            'help': '/api/help'
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
