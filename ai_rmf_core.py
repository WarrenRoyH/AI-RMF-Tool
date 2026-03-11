#!/usr/bin/env python3

import os
import sys
import json
import argparse
from pathlib import Path
import questionary
from questionary import Choice

# --- Auto-VirtualEnv Logic ---
BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = (BASE_DIR / ".venv" / "bin" / "python").resolve()
CURRENT_PYTHON = Path(sys.executable).resolve()

if VENV_PYTHON.exists() and CURRENT_PYTHON != VENV_PYTHON:
    os.environ["VIRTUAL_ENV"] = str(BASE_DIR / ".venv")
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(BASE_DIR / "ai_rmf_core.py")] + sys.argv[1:])

# Add core directory to sys.path
sys.path.append(str(BASE_DIR))
from core.provider import provider
from core.discovery import discovery
from core.sentry import sentry
from core.auditor import auditor
from core.inspector import inspector

# --- Configuration ---
WORKSPACE_DIR = Path("workspace")
MANIFEST_PATH = WORKSPACE_DIR / "project-manifest.json"
LIBRARIAN_PROMPT_PATH = Path("librarian/prompt.md")
ADVERSARY_PROMPT_PATH = Path("librarian/adversary_prompt.md")

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
    check_setup()
    print("\n" + "="*60)
    print("--> Phase 1: GOVERN (The Librarian)")
    print("="*60)
    print("\nWelcome to the NIST AI RMF Governance Phase.")
    print("I am the Librarian. My role is to help you map your project's context.")
    
    # Proactive Discovery
    print("\n[!] PROACTIVE DISCOVERY (Local Scan Only)...")
    report = discovery.get_discovery_report()
    
    suggested_models = []
    if report['running']:
        print(f"--> Found {len(report['running'])} running AI-related processes:")
        for r in report['running']:
            print(f"    * {r['type']} (PID: {r['pid']})")
            suggested_models.append(r['type'])
            
    if report['stored']:
        print(f"--> Found {len(report['stored'])} model files in local storage:")
        for s in report['stored']:
            print(f"    * {s}")
            suggested_models.append(s.split(":")[-1].strip())

    suggested_purpose = ", ".join(report['purpose_hints']) if report['purpose_hints'] else "General AI Task"
    if report['purpose_hints']:
        print(f"--> Inferred system purpose: {suggested_purpose}")

    print("\n[!] WHY GOVERNANCE MATTERS:")
    print("Governance is the foundation of the AI RMF. It ensures that AI risks are")
    print("managed in a way that is consistent with organizational values, legal")
    print("requirements, and ethical principles.")

    # 1. Project Name
    print("\n" + "-"*30)
    print("STEP 1: PROJECT IDENTITY")
    project_name = questionary.text("What is your project's name?", default=Path.cwd().name).ask()

    # 2. AI-BOM
    print("\n" + "-"*30)
    print("STEP 2: AI BILL OF MATERIALS (AI-BOM)")
    default_model = suggested_models[0] if suggested_models else "custom-model"
    model_id = questionary.text("Model ID:", default=default_model).ask()
    model_version = questionary.text("Model Version (e.g., 1.0, latest):", default="latest").ask()
    model_provider = questionary.text("Model Provider:", default="Local/Self-Hosted" if suggested_models else "OpenAI").ask()

    # 3. Risk Profile
    print("\n" + "-"*30)
    print("STEP 3: RISK PROFILE")
    risk_tier = questionary.select(
        "Select the Risk Tier for this project:",
        choices=[
            Choice("Low (Internal tools, non-critical tasks)", "low"),
            Choice("Medium (Customer-facing, non-sensitive)", "medium"),
            Choice("High (Medical, Financial, Hiring, PII handling)", "high")
        ]
    ).ask()
    domain = questionary.text("Domain / Use-case (e.g., 'Customer Support', 'Medical Diagnosis'):", default=suggested_purpose).ask()

    # 4. Safety Policy
    print("\n" + "-"*30)
    print("STEP 4: SAFETY POLICY")
    prohibited_content = questionary.checkbox(
        "Select prohibited content domains (Press Space to select):",
        choices=[
            "Personal Identifiable Information (PII)",
            "Medical Advice",
            "Financial Advice",
            "Toxic/Offensive Content",
            "Proprietary Code/Data"
        ]
    ).ask()
    pii_protection = questionary.confirm("Enable strict PII protection filters?").ask()
    manual_review = questionary.confirm("Require manual human review for edge cases?").ask()

    # 5. Benchmarking
    print("\n" + "-"*30)
    print("STEP 5: BENCHMARKING")
    target_accuracy = questionary.text("Target Accuracy (e.g., 0.95):", default="0.90").ask()
    bias_threshold = questionary.text("Bias/Variance Threshold (e.g., 0.05):", default="0.05").ask()

    # Prepare data for Librarian
    draft_manifest = {
        "project_name": project_name,
        "ai_bom": { "model_id": model_id, "version": model_version, "provider": model_provider },
        "risk_profile": { "tier": risk_tier, "domain": domain },
        "safety_policy": { 
            "prohibited_content": prohibited_content, 
            "pii_protection": pii_protection, 
            "manual_review_required": manual_review 
        },
        "benchmarks": { 
            "target_accuracy": float(target_accuracy), 
            "bias_threshold": float(bias_threshold) 
        }
    }

    print("\n" + "="*60)
    print("--> GOVERNANCE DATA SUMMARY")
    print("="*60)
    print(f"Project: {project_name}")
    print(f"Model: {model_id} (v{model_version}) by {model_provider}")
    print(f"Risk Tier: {risk_tier.upper()}")
    print(f"Safety: {', '.join(prohibited_content) if prohibited_content else 'None'}")
    print(f"PII Protected: {'YES' if pii_protection else 'NO'}")
    print(f"Manual Review: {'YES' if manual_review else 'NO'}")
    print(f"Benchmarks: Accuracy={target_accuracy}, Bias={bias_threshold}")
    print("="*60)

    print("\n--> Handing off to the Librarian (LLM) for verification...")

    with open(LIBRARIAN_PROMPT_PATH, 'r') as f:
        system_prompt = f.read()

    messages = [{"role": "system", "content": system_prompt}]
    seed_msg = f"Hello Librarian. Here is my draft governance data:\n\n{json.dumps(draft_manifest, indent=2)}\n\nPlease review this for compliance with NIST AI RMF 1.0 and suggest any improvements or final manifest generation."
    messages.append({"role": "user", "content": seed_msg})

    response = provider.chat(messages)
    if response:
        print(f"\nLibrarian: {response}")
        messages.append({"role": "assistant", "content": response})
    
    while True:
        action = questionary.select(
            "\nLibrarian is waiting for your input:",
            choices=[
                Choice("Everything looks correct. Finalize and generate my Project Manifest.", "finalize"),
                Choice("I have a follow-up question or detail to add.", "follow_up"),
                Choice("Exit session.", "exit")
            ]
        ).ask()

        if action == "exit" or action is None:
            print("\nLibrarian: Ending session.")
            break
        
        if action == "finalize":
            user_input = "Everything looks correct. I am ready for you to output the final Project Manifest JSON block now so we can move to Phase 2."
            print(f"\n[SYSTEM]: Requesting final manifest generation...")
        else:
            user_input = questionary.text("Enter your question or detail:").ask()
            if not user_input: continue
            
        messages.append({"role": "user", "content": user_input})
        response = provider.chat(messages)
        if response is None:
            print("\nLibrarian: [Error] No response from LLM.")
            continue

        print(f"\nLibrarian: {response}")
        messages.append({"role": "assistant", "content": response})
        
        if "```json" in response:
            try:
                json_str = response.split("```json")[1].split("```")[0].strip()
                manifest_data = json.loads(json_str)
                with open(MANIFEST_PATH, 'w') as f:
                    json.dump(manifest_data, f, indent=4)
                print(f"\n[!] Project Manifest automatically updated: {MANIFEST_PATH}")

                if questionary.confirm("Governance complete. Would you like to start Phase 2: MAP (The Adversary) now?").ask():
                    run_map()
                    return
                break
            except Exception as e:
                print(f"[!] Error parsing manifest: {e}")

# --- Persona: Adversary (Map) ---
def run_map():
    check_setup()
    print("\n" + "="*60)
    print("--> Phase 2: MAP (The Adversary)")
    print("="*60)
    print("\nWelcome to the NIST AI RMF Map Phase.")
    print("I am the Adversary. My role is to probe your model for security failures.")

    if not MANIFEST_PATH.exists():
        print("\n[!] Error: Project Manifest not found. Please run 'govern' first.")
        return

    with open(MANIFEST_PATH, 'r') as f:
        manifest_data = json.load(f)

    with open(ADVERSARY_PROMPT_PATH, 'r') as f:
        system_prompt = f.read()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is our Project Manifest for mapping:\n\n{json.dumps(manifest_data, indent=2)}"}
    ]

    print(f"\n[ANALYZING]: Mapping attack surface for {manifest_data.get('project_name')}...")

    response = provider.chat(messages)
    if response:
        print(f"\nAdversary: {response}")
        messages.append({"role": "assistant", "content": response})

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "done", "quit"]:
            if questionary.confirm("Mapping complete. Would you like to start Phase 3: MANAGE (The Sentry) now?").ask():
                run_manage()
            else:
                print("\nAdversary: Mapping session ended.")
            break

        messages.append({"role": "user", "content": user_input})
        response = provider.chat(messages)
        if response is None:
            print("\nAdversary: [Error] No response from LLM.")
            continue

        print(f"\nAdversary: {response}")
        messages.append({"role": "assistant", "content": response})

# --- Persona: Sentry (Manage) ---
def run_manage():
    check_setup()
    print("\n" + "="*60)
    print("--> Phase 3: MANAGE (The Sentry)")
    print("="*60)
    print("\nWelcome to the NIST AI RMF Manage Phase.")
    print("I am the Sentry. My role is to enforce your safety policies in real-time.")

    if not MANIFEST_PATH.exists():
        print("\n[!] Error: Project Manifest not found. Please run 'govern' first.")
        return

    LOG_PATH = WORKSPACE_DIR / "logs" / "sentry_violations.jsonl"
    messages = [{"role": "system", "content": "You are a helpful assistant. Adhere strictly to the safety guidelines."}]

    while True:
        user_input = input("\nYou (Protected): ")
        if user_input.lower() in ["exit", "done", "quit"]:
            if questionary.confirm("Management session ended. Run Phase 4: MEASURE (The Auditor) now?").ask():
                run_measure()
            break

        # 1. SCAN INPUT
        print("    [SENTRY]: Scanning input...")
        safe_input, is_valid, risk_score = sentry.validate_input(user_input)
        
        if not is_valid:
            print(f"    [SENTRY]: Blocked! (High Risk Score: {risk_score})")
            with open(LOG_PATH, "a") as f:
                log_entry = {"timestamp": __import__("datetime").datetime.now().isoformat(), "type": "input_block", "original": user_input, "risk_score": risk_score}
                f.write(json.dumps(log_entry) + "\n")
            continue
            
        if safe_input != user_input:
            print("    [SENTRY]: Redacted/Sanitized input for safety.")
            with open(LOG_PATH, "a") as f:
                log_entry = {"timestamp": __import__("datetime").datetime.now().isoformat(), "type": "input_redaction", "original": user_input, "sanitized": safe_input}
                f.write(json.dumps(log_entry) + "\n")

        # 2. CALL PROVIDER
        messages.append({"role": "user", "content": safe_input})
        # Note: If no LLM is configured, this will fail. Handled by check_setup
        response = provider.chat(messages)
        if response is None: continue
        
        # 3. SCAN OUTPUT
        print("    [SENTRY]: Scanning output...")
        safe_output, is_valid, risk_score = sentry.validate_output(safe_input, response)
        
        if not is_valid:
            print(f"    [SENTRY]: Model response blocked due to policy violation.")
            with open(LOG_PATH, "a") as f:
                log_entry = {"timestamp": __import__("datetime").datetime.now().isoformat(), "type": "output_block", "prompt": safe_input, "blocked_response": response, "risk_score": risk_score}
                f.write(json.dumps(log_entry) + "\n")
            continue

        print(f"\nAssistant: {safe_output}")
        messages.append({"role": "assistant", "content": safe_output})

# --- Persona: Auditor (Measure) ---
def run_measure():
    check_setup()
    print("\n" + "="*60)
    print("--> Phase 4: MEASURE (The Auditor)")
    print("="*60)
    print("\nWelcome to the NIST AI RMF Measure Phase.")
    print("I am the Auditor. My role is to evaluate your system's performance and compliance.")

    print("\n[!] PERFORMING COMPLIANCE AUDIT (LOCAL)...")
    result = auditor.run_compliance_audit()
    print(f"\n[SENTRY AUDIT]: {result}")
    
    if "audit_report.md" in result:
        print("\nYou can now review the detailed NIST-aligned audit report in your workspace.")

# --- Persona: Inspector (Observe) ---
def run_observe():
    check_setup()
    print("\n" + "="*60)
    print("--> Phase 4: MEASURE (The Inspector)")
    print("="*60)
    print("\nLaunching continuous monitoring dashboard...")
    result = inspector.start_observability_server()
    print(f"\n[INSPECTOR]: {result}")
    
    status = inspector.get_monitoring_status()
    print(f"[STATUS]: {status}")

# --- CLI Entry Point ---
def main():
    parser = argparse.ArgumentParser(description="AI-RMF Lifecycle Tools (NIST 1.0)")
    subparsers = parser.add_subparsers(dest="command", help="AI-RMF Personas")

    subparsers.add_parser("govern", help="Phase 1: Govern (The Librarian)")
    subparsers.add_parser("map", help="Phase 2: Map (The Adversary)")
    subparsers.add_parser("manage", help="Phase 3: Manage (The Sentry)")
    subparsers.add_parser("measure", help="Phase 4: Measure (The Auditor)")
    subparsers.add_parser("observe", help="Phase 4: Measure (The Inspector Dashboard)")

    args = parser.parse_args()

    if args.command == "govern":
        run_govern()
    elif args.command == "map":
        run_map()
    elif args.command == "manage":
        run_manage()
    elif args.command == "measure":
        run_measure()
    elif args.command == "observe":
        run_observe()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
