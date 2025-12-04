"""
Setup script for Ascend AI SDK (backward compatibility)

Modern packaging uses pyproject.toml, but this file is provided
for compatibility with older pip versions.
"""

from setuptools import setup, find_packages

# Read version from pyproject.toml
version = "1.0.0"

setup(
    name="ascend-ai-sdk",
    version=version,
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "types-requests>=2.28.0",
        ],
    },
)
