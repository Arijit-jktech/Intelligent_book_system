"""
Application configuration module.
This module automatically loads environment variables from .env file on import.
Must be imported at the top of app/main.py to ensure environment is configured
before any other modules read environment variables.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("WARNING: python-dotenv not installed. Environment variables must be set manually.")
    load_dotenv = None


def load_environment():
    """Load environment variables from .env file in project root."""
    if load_dotenv is None:
        return

    # Find project root (parent of 'app' directory)
    app_dir = Path(__file__).parent
    project_root = app_dir.parent

    # Try .env file first, then .env.local, then .env.development
    env_files = [
        project_root / ".env",
        project_root / ".env.local",
        project_root / ".env.development",
    ]

    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file, verbose=True)
            print(f"✓ Loaded environment from: {env_file}")
            return

    # If no .env file found, check for .env.example
    env_example = project_root / ".env.example"
    if env_example.exists():
        print(
            f"⚠ No .env file found. Using .env.example as reference.\n"
            f"  Create .env file: cp .env.example .env"
        )
    else:
        print("⚠ No .env or .env.example file found. Using system environment variables.")


# Load environment on import
load_environment()
