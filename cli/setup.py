import json
import os
import sys
import questionary
from pathlib import Path
from cli.utils import check_setup, MANIFEST_PATH, WORKSPACE_DIR
from core.provider import provider
from core.discovery import discovery

SETUP_PROMPT_PATH = Path("librarian/setup_prompt.md")

def run_setup():
    check_setup()
    print("\n" + "="*60)
    print("--> AI-RMF SETUP WIZARD (Intent-Based Manifest Generation)")
    print("="*60)
    
    if MANIFEST_PATH.exists():
        if not questionary.confirm("\n[!] Existing Project Manifest found. Overwrite it?").ask():
            print("Setup cancelled.")
            return

    if not SETUP_PROMPT_PATH.exists():
        print(f"[ERROR]: Setup prompt not found at {SETUP_PROMPT_PATH}")
        return

    # Proactive Discovery
    print("\n[!] PROACTIVE DISCOVERY (Scanning Environment)...")
    discovery_report = discovery.get_discovery_report()
    discovery_fragment = discovery.suggest_manifest_fragment()

    with open(SETUP_PROMPT_PATH, 'r') as f:
        system_prompt = f.read()

    print("\nWelcome to the AI-RMF Setup. I am the Librarian.")
    print("Tell me briefly about the AI application you are building or assessing.")
    print("(e.g., 'I am building a customer support chatbot using GPT-4o for a retail company')")

    user_input = questionary.text("Your Project Description:").ask()
    if not user_input:
        print("No description provided. Setup cancelled.")
        return

    # Enrich user input with discovery data
    enriched_input = f"""
User Project Description: {user_input}

PROACTIVE DISCOVERY DATA:
{json.dumps(discovery_report, indent=2)}

SUGGESTED MANIFEST FRAGMENT:
{json.dumps(discovery_fragment, indent=2)}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": enriched_input}
    ]

    while True:
        print("\n--> The Librarian is thinking...")
        try:
            response = provider.chat(messages)
        except Exception as e:
            print(f"[ERROR]: Failed to get response from Librarian: {e}")
            break

        if not response:
            print("[ERROR]: Empty response from Librarian.")
            break

        print(f"\nLibrarian: {response}")

        # Check if the response contains a JSON block (final manifest)
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
            try:
                manifest_data = json.loads(json_str)
                if questionary.confirm("\nLibrarian has generated a manifest draft. Save it?").ask():
                    with open(MANIFEST_PATH, 'w') as f:
                        json.dump(manifest_data, f, indent=4)
                    print(f"\n[SUCCESS]: Project Manifest saved to {MANIFEST_PATH}")
                    print("You can now run 'ai-rmf govern' to refine it or 'ai-rmf map' to start discovery.")
                    break
            except json.JSONDecodeError:
                print("\n[WARNING]: Librarian provided invalid JSON. Continuing conversation...")

        next_input = questionary.text(
            "\nYour response (or type 'exit' to cancel):",
        ).ask()

        if not next_input or next_input.lower() in ['exit', 'quit']:
            print("Setup session ended.")
            break

        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": next_input})

if __name__ == "__main__":
    run_setup()
