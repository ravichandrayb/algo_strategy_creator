from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="trading-signals",
    version="0.1.0",
    author="Ravichandra B",
    author_email="ravichandrayb@gmail.com",
    description="Real-time trading signal generation with Zerodha Kite API integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ravichandrayb/algo_strategy_creator",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'trading_signals': ['*.json', '*.md'],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.9",
        ],
    },
    entry_points={
        "console_scripts": [
            "trading-signals-test=trading_signals.test:main",
        ],
    },
)