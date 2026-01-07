from setuptools import setup, find_packages

setup(
    name="backtest_service",
    version="0.3.0",
    description="Minimal backtesting for Polymarket/Kalshi prediction markets via Dome API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tweidv/backtest-service",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "dome-api-sdk>=0.1.7",
    ],
    license="MIT",
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
    ],
)

