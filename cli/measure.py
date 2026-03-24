import os
import questionary
from questionary import Choice
from cli.utils import check_setup
from core.auditor import auditor

def run_measure(is_autopilot=False, assessment_type=None, is_dry_run=False):
    check_setup()
    print("\n" + "="*60)
    print(f"--> Phase 4: MEASURE (The Auditor){' [DRY RUN MODE]' if is_dry_run else ''}")
    print("="*60)
    
    if is_dry_run:
        print("\n[STEP 3]: Dry Run - Executing Performance Benchmarks...")
        print("--> [SIMULATED]: Running Multi-Agent Adversarial Red-Teaming...")
        print("--> [SIMULATED]: Executing Accuracy Benchmarks (Promptfoo)...")
        print("\n[STEP 4]: Dry Run - Synthesizing NIST Compliance Artifacts...")
        print("--> [SIMULATED]: NIST Compliance Report Generated.")
        print("--> [SIMULATED]: Nutrition Label Generated.")
        print("\n[!] Dry Run complete for Phase 4.")
        return

    if is_autopilot:
        # Step 3: MEASURE
        print("\n[STEP 3/4: MEASURE] - Executing Performance Benchmarks...")
        print("--> [SIMULATION]: Running Multi-Agent Adversarial Red-Teaming...")
        auditor.run_adversarial_sim()
        print("--> [PROMPTFOO]: Executing Accuracy Benchmarks...")
        cmd_pf = auditor.generate_promptfoo_config()
        if cmd_pf: os.system(cmd_pf)
        
        # Step 4: REPORT
        print("\n[STEP 4/4: REPORT] - Synthesizing NIST Compliance Artifacts...")
        auditor.run_compliance_audit()
        auditor.generate_nutrition_label()
        res_pdf = auditor.export_report(format="pdf")
        res_html = auditor.export_report(format="html")
        print("\n" + "="*60)
        print("[AUTOPILOT PIPELINE COMPLETE]")
        print("="*60)
        print(f"--> {res_pdf}")
        print(f"--> {res_html}")
        return

    # --- CLI-Direct Execution ---
    if assessment_type:
        print(f"\n[!] CLI Trigger: Running '{assessment_type}' assessment...")
        if assessment_type == "audit":
            auditor.run_compliance_audit()
        elif assessment_type == "swarm":
            auditor.run_swarm_audit()
        elif assessment_type == "promptfoo":
            cmd = auditor.generate_promptfoo_config()
            if cmd: os.system(cmd)
        elif assessment_type == "garak":
            cmd = auditor.generate_garak_command()
            if cmd: os.system(cmd)
        return

    # --- Manual Mode ---
    while True:
        action = questionary.select(
            "\nMEASURE TOOLBOX: Select an assessment type:",
            choices=[
                Choice("Generate NIST Compliance Audit Report", "audit"),
                Choice("Multi-Agent Consensus (Swarm Audit)", "swarm"),
                Choice("Run Automated Accuracy Benchmarking (Promptfoo)", "promptfoo"),
                Choice("Run Automated Vulnerability Scanning (Garak)", "garak"),
                Choice("Exit Measure phase", "exit")
            ]
        ).ask()
        if action == "exit" or action is None: break
        if action == "audit": auditor.run_compliance_audit()
        elif action == "swarm": auditor.run_swarm_audit()
        elif action == "promptfoo":
            cmd = auditor.generate_promptfoo_config()
            if cmd: os.system(cmd)
        elif action == "garak":
            cmd = auditor.generate_garak_command()
            if cmd: os.system(cmd)
