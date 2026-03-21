import os
import json
import questionary
from cli.utils import check_setup, MANIFEST_PATH
from core.red_teamer import red_teamer

def run_red_team(target_url=None):
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

    # Interactive prompt for target URL if still missing
    if not target_url:
        target_url = questionary.text("Enter target endpoint URL (or press Enter for Local):").ask()

    res = red_teamer.run_stress_test(target_url=target_url)
    print(f"\n--> [RESULT]: {res}")
