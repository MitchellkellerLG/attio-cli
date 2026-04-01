# Kept for editable install compatibility with older pip versions.
# pyproject.toml is the authoritative source for all project metadata and dependencies.
from setuptools import setup, find_packages

setup(
    name="cli-anything-attio",
    version="0.1.0",
    description="Attio CRM CLI — full API coverage for AI agents and power users",
    packages=find_packages(where="agent-harness"),
    package_dir={"": "agent-harness"},
    python_requires=">=3.10",
    install_requires=[
        "click>=8.3.1",
        "httpx>=0.28.1",
        "tenacity>=9.1.4",
        "rich>=14.3.3",
        "python-dotenv>=1.2.2",
        "prompt-toolkit>=3.0.52",
        "rich-click>=1.9",
        "click-repl>=0.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-httpx>=0.35",
            "pytest-cov",
            "ruff",
            "mypy",
        ]
    },
    entry_points={
        "console_scripts": [
            "cli-anything-attio=cli_anything.attio.attio_cli:cli",
            "attio=cli_anything.attio.attio_cli:cli",
        ],
    },
)
