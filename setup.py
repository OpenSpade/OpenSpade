#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="openspade",
    version="1.0.0",
    description="Binance Futures Trading System",
    author="OpenSpade Team",
    packages=find_packages(),
    py_modules=[
        "binance_connector",
        "capital_pool",
        "risk_manager",
        "binance_futures_scraper",
        "database_extension",
        "notification",
        "cli"
    ],
    install_requires=[
        "six>=1.16.0",
        "twilio>=8.0.0",
        "requests>=2.28.0",
        "click>=8.0.0"
    ],
    entry_points={
        "console_scripts": [
            "openspade = cli:cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
