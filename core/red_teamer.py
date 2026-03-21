import os
import json
from pathlib import Path
from core.provider import provider
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
        if "garak" in plan.lower() or "promptfoo" in plan.lower():
            print("\n[!] [EXECUTION]: Red Teamer plan contains actionable commands.")
            # We don't automatically run arbitrary commands from the LLM for safety, 
            # but we can trigger our internal standardized probes.
            return "Red Team Plan generated and dataset ready."
        
        return "Red Team session complete."

red_teamer = RedTeamer()
