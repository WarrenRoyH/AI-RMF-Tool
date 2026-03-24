import os
import json
from pathlib import Path
from core.provider import provider
from core.jailbreak_engine import jailbreak_engine
from librarian.data_factory import DataFactory

BASE_DIR = Path(__file__).resolve().parent.parent

class RedTeamer:
    """
    Phase 2: MAP -> Phase 4: MEASURE (The Red Teamer)
    Expert persona for automated security stress-testing.
    """
    def __init__(self, workspace_dir="workspace"):
        self.workspace_dir = Path(workspace_dir).resolve()
        self.manifest_path = self.workspace_dir / "project-manifest.json"
        self.prompt_path = BASE_DIR / "librarian" / "red_teamer_prompt.md"
        self.data_factory = DataFactory(output_dir=str(self.workspace_dir / "data"))

    def run_stress_test(self, target_url=None):
        """
        Coordinates a red-teaming session: 
        1. Generates adversarial data.
        2. Proposes a test plan via LLM.
        3. Executes the probe.
        """
        if not self.manifest_path.exists():
            return "Error: Project Manifest missing. Run 'govern' first."

        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)

        print(f"\n[RED TEAM]: Initializing stress-test for {manifest.get('project_name')}...")
        
        # 1. Generate adversarial data
        print("--> [DATA]: Generating synthetic adversarial dataset (Honey Pots, Injections)...")
        data_path = self.data_factory.generate_adversarial_csv(num_rows=20)
        print(f"    Dataset created: {data_path}")

        # 2. Get Red Teamer guidance
        with open(self.prompt_path, 'r') as f:
            system_prompt = f.read()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the manifest: {json.dumps(manifest)}\n\n"
                                       f"Target URL: {target_url or 'Not provided'}\n\n"
                                       f"Please provide an 'Attack Matrix' and a specific command-line for 'garak' or 'promptfoo' to test this system."}
        ]
        
        print("--> [PLAN]: Requesting Attack Matrix from the Red Teamer persona...")
        # Use primary model for reasoning
        plan = provider.chat(messages)
        print("\n" + "="*40)
        print("RED TEAMER PLAN:")
        print("="*40)
        print(plan)
        print("="*40)

        # 3. Execution (Simulated or triggered if command found)
        execution_results = []
        if "garak" in plan.lower():
            from core.auditor import auditor
            print("\n[!] [EXECUTION]: Triggering automated Garak probe based on plan...")
            cmd = auditor.generate_garak_command(slim_mode=True)
            if cmd:
                print(f"Running: {cmd}")
                os.system(cmd)
                execution_results.append("Garak probe executed.")
        
        if "promptfoo" in plan.lower():
            from core.auditor import auditor
            print("\n[!] [EXECUTION]: Triggering automated Promptfoo evaluation based on plan...")
            cmd = auditor.generate_promptfoo_config(slim_mode=True)
            if cmd:
                print(f"Running: {cmd}")
                os.system(cmd)
                execution_results.append("Promptfoo evaluation executed.")

        if execution_results:
            return f"Red Team session complete. Actions: {', '.join(execution_results)}"
        
        return "Red Team Plan generated and dataset ready."

    def run_dynamic_scan(self, num_probes=5):
        """Phase 17: Dynamic Jailbreak Scan."""
        print(f"\n[RED TEAM]: Starting Dynamic Jailbreak Scan ({num_probes} probes)...")
        summary, path = jailbreak_engine.run_full_scan(num_probes)
        print(f"--> [SCAN COMPLETE]: {summary}")
        return summary, path

red_teamer = RedTeamer()
