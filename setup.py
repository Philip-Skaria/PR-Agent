"""
Setup script for PR Agent
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding="utf-8").strip().split("\n")
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="pragent",
    version="0.1.0",
    description="A comprehensive Python-based pull request review agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="PR Agent Team",
    author_email="team@pragent.dev",
    url="https://github.com/pragent/pragent",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "pragent=pragent.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
    keywords="pull-request code-review git github gitlab bitbucket analysis",
    project_urls={
        "Bug Reports": "https://github.com/pragent/pragent/issues",
        "Source": "https://github.com/pragent/pragent",
        "Documentation": "https://pragent.readthedocs.io/",
    },
)

