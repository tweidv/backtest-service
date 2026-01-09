from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="emulo-backtest",
    version="0.1.0",
    description="Minimal backtesting for Polymarket/Kalshi prediction markets via Dome API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="tweidv",
    author_email="tweidevrieze@gmail.com",
    url="https://github.com/tweidv/emulo-backtest",
    project_urls={
        "Bug Tracker": "https://github.com/tweidv/emulo-backtest/issues",
        "Documentation": "https://github.com/tweidv/emulo-backtest#readme",
        "Source Code": "https://github.com/tweidv/emulo-backtest",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.9",
    install_requires=[
        "dome-api-sdk>=0.1.7",
        "python-dotenv>=1.0.0",
    ],
    license="MIT",
    license_files=["LICENSE"],
    keywords=["polymarket", "kalshi", "prediction-markets", "backtesting", "trading"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
        "Operating System :: OS Independent",
    ],
)

