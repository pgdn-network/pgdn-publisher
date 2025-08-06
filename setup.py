"""
Setup script for PGDN Publisher
"""

from setuptools import setup, find_packages

# Read requirements from requirements.txt
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="pgdn-publisher",
    version="1.5.3",
    description="PGDN Publisher - DePIN scan result publishing library",
    long_description="A clean library for publishing DePIN scan results to blockchain ledgers and report storage.",
    author="PGDN Team",
    author_email="",
    url="",
    packages=['pgdn_publisher'],
    package_data={
        '': ['contracts/ledger/abi.json'],
    },
    include_package_data=True,
    py_modules=['cli', '__main__'],
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'pgdn-publisher=cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
)