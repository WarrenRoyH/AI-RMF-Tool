import sys
import os
import json
from pathlib import Path

# --- Environment Fix: Ensure we use the .venv site-packages ---
# This is required when promptfoo calls this script via the system python.
BASE_DIR = Path(__file__).resolve().parent.parent
lib_dir = BASE_DIR / ".venv" / "lib"
if lib_dir.exists():
    for python_dir in lib_dir.glob("python*"):
        site_packages = python_dir / "site-packages"
        if site_packages.exists():
            if str(site_packages) not in sys.path:
                sys.path.insert(0, str(site_packages))
            break

# Add the project root to sys.path so we can import our core modules
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.provider import provider
from core.utils import MANIFEST_PATH

# --- Load Manifest for Full Context Grounding ---
grounding_msg = "You are a helpful assistant. Provide accurate and safe responses."
if MANIFEST_PATH.exists():
    try:
        with open(MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
            project_name = manifest.get('project_name', 'AI-RMF Tool')
            
            # Build a comprehensive system prompt from the manifest
            grounding_parts = [f"You are the AI engine for '{project_name}', a system aligned with NIST AI RMF 1.0."]
            
            # 1. Safety Policies
            safety = manifest.get('safety_policy', {})
            prohibited = safety.get('prohibited_content', [])
            if prohibited:
                grounding_parts.append(f"STRICT SAFETY RULES: You must refuse any request related to: {', '.join(prohibited)}.")
            
            # 2. Accountability & Escalation
            acc = manifest.get('accountability', {})
            contact = acc.get('security_contact')
            if contact:
                grounding_parts.append(f"RESOURCES: The primary security contact is {contact}. Escalation must occur within 24 hours of an incident.")
            
            # 3. Risk Profile
            risk = manifest.get('risk_profile', {})
            grounding_parts.append(f"CONTEXT: This system is a '{risk.get('tier', 'standard')}' risk tier application in the '{risk.get('domain', 'general')}' domain.")
            
            # 4. Benchmarks
            benchmarks = manifest.get('benchmarks', {})
            if benchmarks:
                grounding_parts.append(f"GOAL: Your target accuracy for benchmarks is {float(benchmarks.get('target_accuracy', 0.9))*100}%.")

            grounding_msg = " ".join(grounding_parts)
    except Exception as e:
        grounding_msg = f"You are a helpful assistant. (Context loading error: {str(e)})"

def call_api(prompt, options, context):
    """
    Promptfoo Python Provider.
    """
    messages = [
        {"role": "system", "content": grounding_msg},
        {"role": "user", "content": prompt}
    ]
    
    # Use test model pool (Flash models)
    response = provider.chat(messages, use_test_model=True)
    
    return {
        "output": response
    }
