import os
import json
import sys
from pathlib import Path
from core.provider import provider

WORKSPACE_DIR = Path("workspace")
MANIFEST_PATH = WORKSPACE_DIR / "project-manifest.json"
LIBRARIAN_PROMPT_PATH = Path("librarian/prompt.md")
ADVERSARY_PROMPT_PATH = Path("librarian/adversary_prompt.md")

def check_setup():
    """Ensure workspace exists and environment is configured."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    (WORKSPACE_DIR / "data").mkdir(parents=True, exist_ok=True)
    (WORKSPACE_DIR / "logs").mkdir(parents=True, exist_ok=True)
    (WORKSPACE_DIR / "reports").mkdir(parents=True, exist_ok=True)
    (WORKSPACE_DIR / "policies").mkdir(parents=True, exist_ok=True)
    
    # Check for .env and API keys via the provider layer
    try:
        provider.validate_setup()
    except ValueError as e:
        print(f"\n" + "!"*40)
        print(f"ERROR: {e}")
        print("!"*40)
        print("\nPlease ensure your .env file exists and contains the required keys.")
        print("Example .env file content:")
        print("GOOGLE_API_KEY=your_google_key_here")
        print("ANTHROPIC_API_KEY=your_anthropic_key_here")
        print("OPENAI_API_KEY=your_openai_key_here")
        print("\nSee README.md for more configuration details.")
        sys.exit(1)
    
    print("--> API Configuration: [VERIFIED]")
