#!/usr/bin/env python3
"""
Setup script for PGDN Publisher library.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pgdn-publish",
    version="1.6.0",
    author="PGDN Network",
    author_email="contact@pgdn.network",
    description="A pure Python library for publishing DePIN scan results to blockchain ledgers and reports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pgdn-network/pgdn-publisher",
    packages=find_packages(),
    package_data={
        'pgdn_publish': ['contracts/ledger/*.json'],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "web3>=6.0.0",
        "eth-account>=0.8.0",
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "pgdn-publish=pgdn_publish.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)