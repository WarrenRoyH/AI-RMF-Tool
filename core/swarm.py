import os
import json
from pathlib import Path
from core.provider import provider

BASE_DIR = Path(__file__).resolve().parent.parent

class Swarm:
    """
    Phase 17: Multi-Agent Orchestration
    Orchestrates a swarm of personas to reach a consensus on AI risk and compliance.
    """
    def __init__(self, workspace_dir="workspace"):
        self.workspace_dir = Path(workspace_dir).resolve()
        self.personas = {
            "Policy Expert": BASE_DIR / "librarian" / "policy_expert_prompt.md",
            "Compliance Officer": BASE_DIR / "librarian" / "compliance_officer_prompt.md",
            "Red Teamer": BASE_DIR / "librarian" / "red_teamer_prompt.md"
        }

    def _load_prompt(self, persona_name):
        prompt_path = self.personas.get(persona_name)
        if prompt_path and prompt_path.exists():
            return prompt_path.read_text()
        return "You are an AI Auditor for NIST RMF."

    def run_consensus(self, manifest_data, scan_results, sentry_logs):
        """
        Runs the swarm and returns a synthesized consensus report.
        """
        context = {
            "manifest": manifest_data,
            "scan_results": scan_results,
            "sentry_logs": sentry_logs[:50] # Limit logs for context window
        }
        
        individual_reports = {}
        
        # 1. Run Individual Personas (Flash Pool)
        for name, prompt_path in self.personas.items():
            print(f"[SWARM]: Querying {name}...")
            system_prompt = self._load_prompt(name)
            user_msg = f"CONTEXT:\n{json.dumps(context, indent=2)}\n\nPerform your assessment based on your persona."
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
            
            # Use test model (Flash) for individual reasoning
            report = provider.chat(messages, use_test_model=True)
            individual_reports[name] = report

        # 2. Synthesize Consensus (Pro Model)
        print("[SWARM]: Synthesizing Consensus from individual reports...")
        synth_system = "You are the Lead Auditor for a Multi-Agent NIST AI RMF assessment. Your task is to synthesize three individual reports (Policy Expert, Compliance Officer, Red Teamer) into a final, authoritative consensus. Highlight conflicts, reach a majority or weighted decision, and provide the final compliance score."
        
        synth_user = "INDIVIDUAL REPORTS:\n"
        for name, report in individual_reports.items():
            synth_user += f"--- {name} REPORT ---\n{report}\n\n"
        
        synth_user += "Synthesize the final Consensus Report in Markdown. Include a 'Swarm Consensus Score' (0-100) and a final 'Approved' or 'Rejected' status."

        messages = [
            {"role": "system", "content": synth_system},
            {"role": "user", "content": synth_user}
        ]
        
        # Use primary (Pro) model for the final synthesis
        consensus_report = provider.chat(messages, use_test_model=False)
        
        # 3. Save Swarm Artifacts
        swarm_dir = self.workspace_dir / "reports" / "swarm"
        swarm_dir.mkdir(parents=True, exist_ok=True)
        
        with open(swarm_dir / "individual_reports.json", "w") as f:
            json.dump(individual_reports, f, indent=4)
            
        with open(swarm_dir / "consensus_report.md", "w") as f:
            f.write(consensus_report)
            
        return consensus_report, individual_reports

swarm = Swarm()
