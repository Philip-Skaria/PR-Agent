#!/usr/bin/env python3
"""
Web application entry point for PR Agent
"""

from pragent.cli import cli
import sys

if __name__ == '__main__':
    # Run CLI with web arguments
    sys.argv = ['pragent', '--help']
    cli()
