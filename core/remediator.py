import json
from pathlib import Path
from core.provider import provider

class Remediator:
    """
    Phase 4: MEASURE -> Phase 3: MANAGE (Auto-Remediation)
    Uses an LLM to suggest prompt patches based on security failures.
    """
    def __init__(self, workspace_dir="workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.manifest_path = self.workspace_dir / "project-manifest.json"

    def suggest_patch(self, failure_report_path):
        """
        Analyzes a failure report (e.g., Garak or Sentry logs) 
        and suggests a system prompt patch.
        """
        report_path = Path(failure_report_path)
        if not report_path.exists():
            return "Error: Failure report not found."

        # Load the report content (truncated if too large)
        with open(report_path, 'r') as f:
            report_content = f.read()[-2000:] # Last 2000 chars

        # Load the manifest for context
        if self.manifest_path.exists():
            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)
        else:
            manifest = {}

        prompt = f"""
[CONTEXT]: I am an AI safety engineer remediating a system prompt based on security failures.
[SYSTEM MANIFEST]: {json.dumps(manifest.get('safety_policy', {}))}
[FAILURE EVIDENCE]: {report_content}

[TASK]: Based on the failures above, suggest a "Hardened System Prompt" snippet that specifically mitigates these risks. 
Ensure the patch is concise and direct. Output ONLY the suggested prompt snippet in a Markdown code block.
"""
        messages = [{"role": "user", "content": prompt}]
        response = provider.chat(messages)

        if response:
            patch_path = self.workspace_dir / "reports" / "suggested_patch.md"
            with open(patch_path, 'w') as f:
                f.write(f"# Suggested Remediation Patch\n\n{response}")
            return f"Patch suggested based on failures: {patch_path}"
        
        return "Error: Could not generate remediation patch."

remediator = Remediator()
