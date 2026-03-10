#!/usr/bin/env python3

import os
import sys
import json
import argparse
from pathlib import Path

# --- Auto-VirtualEnv Logic ---
BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = (BASE_DIR / ".venv" / "bin" / "python").resolve()
CURRENT_PYTHON = Path(sys.executable).resolve()

if VENV_PYTHON.exists() and CURRENT_PYTHON != VENV_PYTHON:
    # Optional: print(f"--> Switching to virtualenv: {VENV_PYTHON}")
    os.environ["VIRTUAL_ENV"] = str(BASE_DIR / ".venv")
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(BASE_DIR / "ai-rmf")] + sys.argv[1:])

# Add core directory to sys.path
sys.path.append(str(BASE_DIR))
from core.provider import provider

# --- Configuration ---
WORKSPACE_DIR = Path("workspace")
MANIFEST_PATH = WORKSPACE_DIR / "project-manifest.json"
LIBRARIAN_PROMPT_PATH = Path("librarian/prompt.md")

def check_setup():
    """
    Ensures the workspace exists and API keys are configured.
    """
    if not WORKSPACE_DIR.exists():
        print("Error: Workspace not found. Run 'bootstrap.sh' first.")
        sys.exit(1)
    
    # Check for .env and API keys via the provider layer
    provider.validate_setup()
    print("--> API Configuration: [VERIFIED]")

# --- Persona: Librarian (Govern) ---
def run_govern():
    """
    Launches an interactive interview with the Librarian using the provider layer.
    """
    check_setup()
    print("\n" + "="*60)
    print("--> Phase 1: GOVERN (The Librarian)")
    print("="*60)
    print("\nWelcome to the NIST AI RMF Governance Phase.")
    print("I am the Librarian. My role is to help you map your project's context,")
    print("inventory your AI-BOM, and define the safety policies that will")
    print("configure the rest of our automated security agents.")
    print("\nType 'exit' or 'done' to end the session at any time.")
    print("-" * 60)
    
    with open(LIBRARIAN_PROMPT_PATH, 'r') as f:
        system_prompt = f.read()

    # Proactively start the conversation
    intro_query = "Hello. I am ready to begin the NIST AI RMF interview. Please introduce yourself and briefly describe the AI project we are governing today."
    print(f"\nLibrarian: {intro_query}")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "done", "quit"]:
            print("\nLibrarian: Ending session. Don't forget to save your manifest.")
            break
            
        # Get response from the LLM
        response = provider.chat(system_prompt, user_input)
        print(f"\nLibrarian: {response}")
        
        # If the Librarian outputs a JSON block, offer to save it
        if "```json" in response:
            try:
                json_str = response.split("```json")[1].split("```")[0].strip()
                manifest_data = json.loads(json_str)
                with open(MANIFEST_PATH, 'w') as f:
                    json.dump(manifest_data, f, indent=4)
                print(f"\n[!] Project Manifest saved to {MANIFEST_PATH}")
            except Exception as e:
                print(f"\n[Error] Failed to auto-save manifest: {e}")

# --- CLI Entry Point ---
def main():
    parser = argparse.ArgumentParser(description="AI-RMF Lifecycle Tools (NIST 1.0)")
    subparsers = parser.add_subparsers(dest="command", help="AI-RMF Personas")

    subparsers.add_parser("govern", help="Phase 1: Govern (The Librarian)")
    subparsers.add_parser("map", help="Phase 2: Map (The Adversary)")
    subparsers.add_parser("manage", help="Phase 3: Manage (The Sentry)")
    subparsers.add_parser("measure", help="Phase 4: Measure (The Auditor / Red Teamer)")

    args = parser.parse_args()

    if args.command == "govern":
        run_govern()
    elif args.command == "map":
        # Adversary logic here
        pass
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
