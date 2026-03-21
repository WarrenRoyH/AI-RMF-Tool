import json
import questionary
from questionary import Choice
from cli.utils import check_setup, MANIFEST_PATH, LIBRARIAN_PROMPT_PATH
from core.discovery import discovery
from core.provider import provider
from core.auditor import auditor

def run_govern(is_autopilot=False, is_dry_run=False):
    check_setup()
    print("\n" + "="*60)
    print(f"--> Phase 1: GOVERN (The Librarian){' [DRY RUN MODE]' if is_dry_run else ''}")
    print("="*60)
    
    if is_dry_run:
        print("\n[!] Dry Run: Skipping Librarian interview and policy drafting.")
        return

    # --- Step 0: Session Management ---
    if MANIFEST_PATH.exists() and not is_autopilot:
        if questionary.confirm("\n[!] [RESUME]: Existing Project Manifest found. Load it and skip interview?").ask():
            print(f"--> [SUCCESS]: Loaded {MANIFEST_PATH}. Proceeding to Librarian verification...")
            with open(MANIFEST_PATH, 'r') as f:
                draft_manifest = json.load(f)
            # Jump to verification phase (Librarian LLM)
            librarian_verify(draft_manifest, is_autopilot)
            return

    print("\nWelcome to the NIST AI RMF Governance Phase.")
    print("I am the Librarian. My role is to help you map your project's context,")
    print("establish risk tolerance, and define safety policies (GOVERN-1, GOVERN-2).")

    # Proactive Discovery
    print("\n[!] PROACTIVE DISCOVERY (Local Environment Scan)...")
    report = discovery.get_discovery_report()
    
    # --- Step 0: Profile Selection ---
    print("\n" + "-"*30)
    print("STEP 0: NIST PROFILE TEMPLATES")
    print("EXPLANATION: Templates pre-configure the risk tier and safety policies")
    print("based on industry standards (e.g., HIPAA for Health, PCI for Finance).")
    
    with open("config/templates.json", "r") as f:
        templates = json.load(f)
    
    template_choices = [Choice(name, name) for name in templates.keys()]
    selected_template_name = questionary.select(
        "Select a pre-configured Industry Profile:",
        choices=template_choices
    ).ask()
    
    template = templates[selected_template_name]
    print(f"--> [INFO]: Pre-loading NIST baseline for {selected_template_name}...")

    # --- Step 1: Project Identity ---
    print("\n" + "-"*30)
    print("STEP 1: PROJECT IDENTITY")
    project_name = questionary.text("Project Name (for reporting):", default="ai-rmf-tools").ask()

    # --- Step 2: AI-BOM ---
    print("\n" + "-"*30)
    print("STEP 2: AI BILL OF MATERIALS (AI-BOM)")
    print("EXPLANATION: Tracking the model identity and provenance is critical")
    print("for transparency and accountability (GOVERN-4).")
    target_type = questionary.select(
        "AI System Access Method (Target Type):",
        choices=[
            Choice("Cloud API (OpenAI, Claude, Gemini)", "api"),
            Choice("Local Model (Ollama/Llama.cpp)", "local"),
            Choice("Local Binary/Program (stdin/stdout)", "program"),
            Choice("Web Application (URL Scan)", "web")
        ]
    ).ask()
    
    model_id = questionary.text("Model Identifier (e.g., gemini-3.1-pro, llama-3):", default="Gemini").ask()
    model_version = questionary.text("Model Version (e.g., 1.0, preview):", default="3.1 Flash Lite").ask()
    model_provider = questionary.text("Model Provenance (Provider):", default="Google (Gemini)").ask()

    # --- Step 3: Risk Profile ---
    print("\n" + "-"*30)
    print("STEP 3: RISK PROFILE & CONTEXT")
    print("EXPLANATION: Categorizing risk helps prioritize mitigation resources.")
    print("Tiering is based on potential impact to individuals and organizations.")
    risk_tier = questionary.select(
        "NIST Risk Tier:",
        choices=[
            Choice("Low (Internal, low-impact tasks)", "low"),
            Choice("Medium (Customer-facing, non-critical)", "medium"),
            Choice("High (Regulated domains: Legal, Finance, HR, PII)", "high")
        ],
        default=template["risk_profile"]["tier"]
    ).ask()
    
    domain = questionary.text("Primary Business/Safety Domain:", default=template["risk_profile"]["domain"]).ask()

    # --- Step 4: Safety Policy ---
    print("\n" + "-"*30)
    print("STEP 4: SAFETY POLICY & GUARDRAILS")
    print("EXPLANATION: These policies define the boundaries for the Sentry.")
    print("The Sentry will actively block or redact content matching these categories.")
    prohibited = questionary.checkbox(
        "Active Blocklist (Select with Space):",
        choices=[Choice(c, c, checked=True) for c in template["safety_policy"]["prohibited_content"]]
    ).ask()
    
    custom_prohibited = questionary.text("Additional custom prohibited categories (Comma-separated):").ask()
    if custom_prohibited:
        prohibited.extend([x.strip() for x in custom_prohibited.split(",")])

    pii_protection = questionary.confirm("Enable Automatic PII Anonymization (Input/Output)?", default=True).ask()
    manual_review = questionary.confirm("Flag high-risk outputs for human audit?", default=True).ask()

    # --- Step 5: Benchmarks ---
    print("\n" + "-"*30)
    print("STEP 5: EVALUATION BENCHMARKS")
    print("EXPLANATION: Quantifying system performance ensures consistent safety (MEASURE-1).")
    perf_standard = questionary.select(
        "Performance Standard:",
        choices=[
            Choice("High Precision (99% Accuracy, 1% Bias)", "high"),
            Choice("Standard (90% Accuracy, 5% Bias)", "standard"),
            Choice("Experimental (Development only)", "low")
        ]
    ).ask()
    
    target_accuracy = 0.99 if perf_standard == "high" else 0.90 if perf_standard == "standard" else 0.70
    bias_threshold = 0.01 if perf_standard == "high" else 0.05 if perf_standard == "standard" else 0.15

    # --- Step 6: Compliance & Legal ---
    print("\n" + "-"*30)
    print("STEP 6: COMPLIANCE & LEGAL CONTEXT")
    print("EXPLANATION: This information is used to generate official policies")
    print("and incident response plans.")
    org_name = questionary.text("Organization Name:", default="AI-RMF Demo Org").ask()
    security_contact = questionary.text("Security Escalation Contact (Email/Channel):", default="security@example.com").ask()
    reporting_window = questionary.text("Mandatory reporting window for incidents (hours):", default="24").ask()

    # --- Step 7: Accountability & Data Governance ---
    print("\n" + "-"*30)
    print("STEP 7: ACCOUNTABILITY & DATA GOVERNANCE")
    print("EXPLANATION: These details address NIST functions for human oversight,")
    print("staff readiness, and data transparency (GV-3, GV-4, GV-5, MP-4, MP-5).")
    
    hitl_process = questionary.text(
        "Describe the Human-in-the-loop (HITL) oversight process:",
        default="Manual review of high-risk outputs by compliance staff."
    ).ask()
    
    staff_training = questionary.text(
        "Staff Training Status (e.g., 'Completed March 2026' or 'Pending'):",
        default="Completed March 2026"
    ).ask()
    
    data_provenance = questionary.text(
        "Primary Data Sources (e.g., 'Internal audited logs', 'Synthetic datasets'):",
        default="Internal audited logs and NIST compliance templates."
    ).ask()
    
    license_cleared = questionary.confirm("Have all data licenses been audited and cleared?", default=True).ask()
    
    risk_tradeoffs = questionary.text(
        "Describe any performance vs. safety tradeoffs made:",
        default="Prioritized filtering depth over response latency for PII categories."
    ).ask()
    
    pii_risk = questionary.select(
        "PII Risk Level of the underlying data:",
        choices=[Choice("Low", "low"), Choice("Medium", "medium"), Choice("High", "high")],
        default="low"
    ).ask()

    draft_manifest = {
        "project_name": project_name,
        "ai_bom": { "model_id": model_id, "version": model_version, "provider": model_provider },
        "risk_profile": { "tier": risk_tier, "domain": domain },
        "accountability": {
            "security_contact": security_contact,
            "hitl_process": hitl_process,
            "staff_training": staff_training,
            "escalation_path": f"Contact {security_contact} within {reporting_window}h of incident."
        },
        "data_governance": {
            "provenance": data_provenance,
            "license_cleared": license_cleared,
            "risk_tradeoffs": risk_tradeoffs,
            "pii_risk_level": pii_risk
        },
        "safety_policy": { 
            "prohibited_content": prohibited, 
            "pii_protection": pii_protection, 
            "manual_review_required": manual_review 
        },
        "benchmarks": { "target_accuracy": target_accuracy, "bias_threshold": bias_threshold },
        "compliance_context": {
            "organization": org_name,
            "security_contact": security_contact,
            "reporting_window": reporting_window
        }
    }

    print("\n" + "="*60)
    print("--> GOVERNANCE DATA SUMMARY")
    print("="*60)
    print(f"Project: {project_name}")
    print(f"Model: {model_id} (v{model_version}) by {model_provider}")
    print(f"Risk Tier: {risk_tier.upper()}")
    print(f"Safety: {', '.join(prohibited)}")
    print(f"PII Protected: {'YES' if pii_protection else 'NO'}")
    print(f"Manual Review: {'YES' if manual_review else 'NO'}")
    print(f"Benchmarks: Accuracy={target_accuracy}, Bias={bias_threshold}")
    print("="*60)

    librarian_verify(draft_manifest, is_autopilot)

def librarian_verify(draft_manifest, is_autopilot=False):
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

                # --- Automated Policy Drafting ---
                print("\n[!] [GENERATING]: Drafting NIST compliance policies (AUP, SSP, IRP)...")
                policy_res = auditor.generate_compliance_policies()
                print(f"--> {policy_res}")

                # --- Automated Dataset Generation ---
                if questionary.confirm("\nLibrarian: Would you like me to generate a domain-specific evaluation dataset for benchmarking?").ask():
                    print(f"\n[!] [GENERATING]: Creating {manifest_data.get('risk_profile', {}).get('domain')} test cases...")
                    dataset_prompt = (
                        f"Based on this AI project manifest: {json.dumps(manifest_data)}\n"
                        "Generate 5 complex, domain-specific evaluation test cases for the model to perform.\n"
                        "Each test case must have:\n"
                        "1. 'query': The input prompt.\n"
                        "2. 'expected': A brief description of the ideal response or a specific string.\n"
                        "3. 'grading_type': Either 'llm-rubric' (for open-ended or safety checks) or 'contains' (for specific technical terms).\n"
                        "4. 'rubric': If grading_type is 'llm-rubric', provide the specific criteria (e.g., 'The model should refuse to generate a resemblance shell and explain why').\n"
                        "Output ONLY a JSON list of objects."
                    )
                    dataset_raw = provider.chat([{"role": "user", "content": dataset_prompt}])
                    try:
                        if "```json" in dataset_raw:
                            dataset_raw = dataset_raw.split("```json")[1].split("```")[0].strip()
                        manifest_data["evaluation_dataset"] = json.loads(dataset_raw)
                        with open(MANIFEST_PATH, 'w') as f:
                            json.dump(manifest_data, f, indent=4)
                        print(f"--> [SUCCESS]: {len(manifest_data['evaluation_dataset'])} domain-specific test cases added to manifest.")
                    except Exception as e:
                        print(f"[!] Error generating dataset: {e}")

                if not is_autopilot:
                    from cli.map import run_map
                    if questionary.confirm("Governance complete. Would you like to start Phase 2: MAP (The Adversary) now?").ask():
                        run_map()
                break
            except Exception as e:
                print(f"[!] Error parsing manifest: {e}")
