"""
Command-line interface for PR Agent
"""

import asyncio
import click
import json
from pathlib import Path
from typing import Optional

from .core.config import Config
from .core.agent import PRAgent


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """PR Agent - Automated pull request analysis and review"""
    ctx.ensure_object(dict)
    
    # Load configuration
    if config:
        ctx.obj['config'] = Config.from_file(Path(config))
    else:
        # Try to load default config
        default_config = Path('pragent.json')
        if default_config.exists():
            ctx.obj['config'] = Config.from_file(default_config)
        else:
            # Create default config
            ctx.obj['config'] = Config()
    
    # Override verbose setting
    if verbose:
        ctx.obj['config'].verbose = True


@cli.command()
@click.option('--server', '-s', required=True, help='Git server name (github, gitlab, bitbucket)')
@click.option('--repo', '-r', required=True, help='Repository name (owner/repo)')
@click.option('--pr', '-p', type=int, required=True, help='Pull request number')
@click.option('--post-comments', is_flag=True, help='Post comments to the PR')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def analyze(ctx, server, repo, pr, post_comments, output):
    """Analyze a single pull request"""
    config = ctx.obj['config']
    
    async def run_analysis():
        agent = PRAgent(config)
        
        try:
            # Analyze PR
            result = await agent.analyze_pr(server, repo, pr)
            
            # Print summary
            print(f"\nPR Analysis Complete")
            print(f"Overall Score: {result['overall_score']}/100")
            print(f"Total Issues: {result['total_issues']}")
            print(f"Files Analyzed: {len(result['file_analyses'])}")
            
            # Print issues by severity
            if result['issues_by_severity']:
                print(f"\nIssues by Severity:")
                for severity, count in result['issues_by_severity'].items():
                    print(f"  - {severity.capitalize()}: {count}")
            
            # Print feedback
            if result['feedback']['recommendations']:
                print(f"\nRecommendations:")
                for i, rec in enumerate(result['feedback']['recommendations'], 1):
                    print(f"  {i}. {rec}")
            
            # Post comments if requested
            if post_comments:
                print(f"\nPosting comments to PR...")
                comment_url = await agent.post_review(server, repo, pr, result)
                print(f"Comments posted: {comment_url}")
            
            # Save output if requested
            if output:
                output_path = Path(output)
                if config.output_format == 'json':
                    with open(output_path, 'w') as f:
                        json.dump(result, f, indent=2, default=str)
                elif config.output_format == 'markdown':
                    # Generate markdown report
                    from .utils.report import ReportGenerator
                    report_gen = ReportGenerator(config)
                    report = await report_gen.generate_report(
                        result['pr_info'], result['file_analyses'], 
                        [], result['overall_score']
                    )
                    await report_gen.save_report(report, output_path)
                
                print(f"Report saved to: {output_path}")
            
            if config.verbose:
                print(f"\nDetailed Analysis:")
                for file_path, analysis in result['file_analyses'].items():
                    print(f"\n{file_path} (Score: {analysis['score']}/100)")
                    for issue in analysis['issues']:
                        print(f"  - {issue.severity.value.upper()}: {issue.message}")
                        if issue.suggestion:
                            print(f"    Suggestion: {issue.suggestion}")
        
        finally:
            await agent.close()
    
    asyncio.run(run_analysis())


@cli.command()
@click.option('--server', '-s', required=True, help='Git server name')
@click.option('--repo', '-r', required=True, help='Repository name')
@click.option('--state', default='open', help='PR state (open, closed, all)')
@click.option('--limit', '-l', type=int, default=10, help='Maximum number of PRs to analyze')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def analyze_multiple(ctx, server, repo, state, limit, output):
    """Analyze multiple pull requests"""
    config = ctx.obj['config']
    
    async def run_analysis():
        agent = PRAgent(config)
        
        try:
            # Analyze multiple PRs
            results = await agent.analyze_multiple_prs(server, repo, state, limit)
            
            print(f"\nAnalyzed {len(results)} pull requests")
            
            # Print summary for each PR
            for result in results:
                pr_info = result['pr_info']
                print(f"\nPR #{pr_info.id}: {pr_info.title}")
                print(f"   Author: {pr_info.author}")
                print(f"   Score: {result['overall_score']}/100")
                print(f"   Issues: {result['total_issues']}")
                print(f"   URL: {pr_info.url}")
            
            # Calculate overall statistics
            if results:
                avg_score = sum(r['overall_score'] for r in results) / len(results)
                total_issues = sum(r['total_issues'] for r in results)
                
                print(f"\nOverall Statistics:")
                print(f"   Average Score: {avg_score:.1f}/100")
                print(f"   Total Issues: {total_issues}")
                print(f"   PRs Analyzed: {len(results)}")
            
            # Save output if requested
            if output:
                output_path = Path(output)
                with open(output_path, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                print(f"\nResults saved to: {output_path}")
        
        finally:
            await agent.close()
    
    asyncio.run(run_analysis())


@cli.command()
@click.option('--output', '-o', type=click.Path(), default='pragent.json', help='Output config file path')
@click.pass_context
def init_config(ctx, output):
    """Initialize configuration file"""
    config = Config()
    
    # Add some example configurations
    config.git_servers = {
        'github': {
            'name': 'GitHub',
            'base_url': 'https://api.github.com',
            'token': 'your_github_token_here'
        },
        'gitlab': {
            'name': 'GitLab',
            'base_url': 'https://gitlab.com',
            'token': 'your_gitlab_token_here'
        }
    }
    
    config.ai = {
        'enabled': False,
        'provider': 'openai',
        'model': 'gpt-3.5-turbo',
        'api_key': 'your_openai_api_key_here'
    }
    
    # Save configuration
    config.save_to_file(Path(output))
    print(f"Configuration file created: {output}")
    print(f"Please edit the file to add your API tokens and customize settings")


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information"""
    from . import __version__
    print(f"PR Agent version {__version__}")


if __name__ == '__main__':
    cli()

