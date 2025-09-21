"""
PR Agent - A comprehensive pull request review system
"""

__version__ = "0.1.0"
__author__ = "PR Agent Team"

from .core.agent import PRAgent
from .core.config import Config

__all__ = ["PRAgent", "Config"]

