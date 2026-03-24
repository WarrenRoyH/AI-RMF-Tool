import json
import os
import questionary
from datetime import datetime
from pathlib import Path
from questionary import Choice
from cli.utils import check_setup, MANIFEST_PATH, ADVERSARY_PROMPT_PATH
from core.discovery import discovery
from core.provider import provider
from core.auditor import auditor

def run_map(is_autopilot=False, is_dry_run=False):
    check_setup()
    print("\n" + "="*60)
    print(f"--> Phase 2: MAP (The Adversary){' [DRY RUN MODE]' if is_dry_run else ''}")
    print("="*60)
    
    if is_dry_run:
        print("\n[STEP 1]: Dry Run - Scanning environment for AI systems...")
        print("--> [SIMULATED]: Found Ollama on :11434")
        print("\n[STEP 2]: Dry Run - Analyzing attack surface...")
        print("--> [SIMULATED]: Risk of prompt injection identified in chat interfaces.")
        print("\n[!] Dry Run complete for Phase 2.")
        return
    print("\nWelcome to the NIST AI RMF Map Phase.")
    print("I am the Adversary. My role is to automatically probe your model's attack surface.")

    if not MANIFEST_PATH.exists():
        print("\n[!] Error: Project Manifest not found. Please run 'govern' first.")
        return

    with open(MANIFEST_PATH, 'r') as f:
        manifest_data = json.load(f)

    # --- Automated Discovery Step ---
    print("\n[STEP 1]: Scanning environment for AI systems...")
    discovery_report = discovery.get_discovery_report()
    
    with open(ADVERSARY_PROMPT_PATH, 'r') as f:
        system_prompt = f.read()

    # Append automation instructions
    system_prompt += "\n\nCRITICAL: Provide your analysis in a structured format. Start with a brief summary, followed by a 'THREAT_MAP' section in JSON block if possible. Focus on providing actionable garak probe recommendations."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is our Project Manifest for mapping:\n{json.dumps(manifest_data, indent=2)}\n\n"
                                   f"Here is our local discovery report:\n{json.dumps(discovery_report, indent=2)}"}
    ]

    print(f"\n[STEP 2]: Analyzing attack surface for {manifest_data.get('project_name')}...")

    response = provider.chat(messages)
    if response:
        print("\n" + "-"*40)
        print("ADVERSARY THREAT ANALYSIS:")
        print("-"*40)
        print(response)
        print("-"*40)

        # --- NIST Artifact Export (Phase 11) ---
        artifact = {
            "phase": "MAP",
            "timestamp": datetime.now().isoformat(),
            "nist_mappings": {
                "MP-1.1": "AI system context and domain analyzed.",
                "MP-2.1": "Potential risks and impacts identified.",
                "MP-3.1": "System attack surface and threats mapped."
            },
            "analysis_summary": response
        }
        artifact_path = Path("workspace/reports/threat_artifact.json")
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        with open(artifact_path, 'w') as f:
            json.dump(artifact, f, indent=4)
        print(f"--> [ARTIFACT]: NIST Threat Artifact exported to {artifact_path}")

    if is_autopilot:
        # Automated Sequential Run
        print("\n[!] Autopilot: Triggering Garak Probes...")
        cmd = auditor.generate_garak_command()
        if cmd:
            print(f"Executing: {cmd}")
            os.system(cmd)
        return

    # --- Manual Mode ---
    action = questionary.select(
        "Mapping complete. What would you like to do next?",
        choices=[
            Choice("Run Automated Vulnerability Scanning (Garak)", "garak"),
            Choice("Proceed to Phase 3: MANAGE (The Sentry)", "manage"),
            Choice("Return to Main Menu", "exit")
        ]
    ).ask()

    if action == "garak":
        print("\n[!] Initializing Garak Scan...")
        cmd = auditor.generate_garak_command()
        if cmd:
            print(f"Executing: {cmd}")
            os.system(cmd)
            print("\n" + "-"*40)
            print("[MAP COMPLETE]: Vulnerabilities mapped. Transitioning to Phase 3: MANAGE (The Sentry)...")
            from cli.manage import run_manage
            run_manage()
    elif action == "manage":
        from cli.manage import run_manage
        run_manage()
