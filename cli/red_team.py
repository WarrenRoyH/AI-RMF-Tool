import os
import json
import questionary
from cli.utils import check_setup, MANIFEST_PATH
from core.red_teamer import red_teamer

def run_red_team(target_url=None, assessment_type=None, num_probes=5):
    check_setup()
    print("\n" + "="*60)
    print("--> Persona: RED TEAMER (Adversarial Stress Test)")
    print("="*60)
    
    # If no target provided, try to find one in manifest or env
    if not target_url:
        if MANIFEST_PATH.exists():
            with open(MANIFEST_PATH, 'r') as f:
                manifest = json.load(f)
                target_url = manifest.get('ai_bom', {}).get('target_url')
        
        if not target_url:
            target_url = os.getenv("AI_RMF_TARGET_URL")

    # Interactive choice for scan type if not provided
    if not assessment_type:
        # Interactive prompt for target URL if still missing
        if not target_url:
            target_url = questionary.text("Enter target endpoint URL (or press Enter for Local):").ask()

        action = questionary.select(
            "\nRED TEAM TOOLBOX: Select an assessment type:",
            choices=[
                questionary.Choice("Run Automated Attack Matrix (Static Probes)", "static"),
                questionary.Choice("Run Dynamic Jailbreak Scan (March 2026 Research)", "dynamic"),
                questionary.Choice("Exit Red Team phase", "exit")
            ]
        ).ask()
        if action == "exit" or action is None: return
        assessment_type = action

    if assessment_type == "static":
        res = red_teamer.run_stress_test(target_url=target_url)
        print(f"\n--> [RESULT]: {res}")
    elif assessment_type == "dynamic":
        if not num_probes:
            num_probes = questionary.text("Number of dynamic probes to run:", default="5").ask()
            try: num_probes = int(num_probes)
            except: num_probes = 5
        summary, path = red_teamer.run_dynamic_scan(num_probes=num_probes)
        print(f"\n--> [RESULT]: {summary}")
        print(f"--> [REPORT]: {path}")
