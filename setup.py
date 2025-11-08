"""
Setup script for ClickUp Framework
Token-Efficient Modular Skill Framework for ClickUp API
"""

from setuptools import setup, find_packages
import os


# Read long description from README
def read_long_description():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Token-Efficient Modular Skill Framework for ClickUp API"


# Read version from __init__.py
def get_version():
    init_path = os.path.join(os.path.dirname(__file__), "__init__.py")
    with open(init_path, "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0-alpha"


setup(
    name="clickup-framework",
    version=get_version(),
    author="ClickUp Skills Development Team",
    author_email="",
    description="Token-Efficient Modular Skill Framework for ClickUp API",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/SOELexicon/skills",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
            "flake8>=6.0.0",
        ]
    },
    keywords="clickup api token-efficient formatters skills claude",
    project_urls={
        "Documentation": "https://github.com/SOELexicon/skills/tree/main/docs",
        "Source": "https://github.com/SOELexicon/skills",
        "Issues": "https://github.com/SOELexicon/skills/issues",
    },
)
