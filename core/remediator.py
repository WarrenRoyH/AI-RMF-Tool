import json
import re
from pathlib import Path
from core.provider import provider

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_RULES_PATH = BASE_DIR / "config" / "remediation_rules.json"

class RuleRegistry:
    def __init__(self, rules_path=DEFAULT_RULES_PATH):
        self.rules_path = Path(rules_path)
        self.rules = []
        self.load_rules()

    def load_rules(self):
        if not self.rules_path.exists():
            return
        with open(self.rules_path, 'r') as f:
            data = json.load(f)
            self.rules = data.get("rules", [])
        
        # Pre-compile regexes
        for rule in self.rules:
            trigger = rule.get("trigger", {})
            if trigger.get("regex"):
                trigger["_compiled_regex"] = re.compile(trigger["regex"])

    def apply_rules(self, text, target, category=None, risk_score=0):
        """
        Applies rules to the text based on target (input/output), category, and risk_score.
        Returns a dict: {"action": "allow"|"block"|"mask"|"route", "modified_text": text, "route_to": None, "reason": None}
        """
        for rule in self.rules:
            if rule.get("target") != target:
                continue
                
            trigger = rule.get("trigger", {})
            match = False
            
            # Check conditions based on trigger schema
            cat_match = False
            if trigger.get("category") and trigger.get("category") == category:
                if risk_score >= trigger.get("min_score", 0):
                    cat_match = True
            
            regex_match = False
            if trigger.get("_compiled_regex"):
                if trigger["_compiled_regex"].search(text):
                    regex_match = True
                    
            # If any condition matches, apply the rule
            # Assuming OR condition between category matching and regex matching
            if cat_match or regex_match:
                action = rule.get("action")
                result = {
                    "action": action,
                    "modified_text": text,
                    "route_to": rule.get("route_to"),
                    "reason": rule.get("reason")
                }
                
                if action == "mask":
                    if trigger.get("_compiled_regex"):
                        result["modified_text"] = trigger["_compiled_regex"].sub("[MASKED]", text)
                    else:
                        result["modified_text"] = "[MASKED_PII]"
                        
                return result
                
        return {"action": "allow", "modified_text": text, "route_to": None, "reason": None}

class Remediator:
    def __init__(self, rules_path=DEFAULT_RULES_PATH, workspace_dir=None):
        self.registry = RuleRegistry(rules_path=rules_path)
        from core.utils import WORKSPACE_DIR
        self.workspace_dir = Path(workspace_dir).resolve() if workspace_dir else WORKSPACE_DIR
        self.manifest_path = self.workspace_dir / "project-manifest.json"
        
    def process_input(self, text, category=None, risk_score=0):
        return self.registry.apply_rules(text, "input", category, risk_score)
        
    def process_output(self, text, category=None, risk_score=0):
        return self.registry.apply_rules(text, "output", category, risk_score)

    def suggest_patch(self, failure_report_path):
        import json
        import re
        report_path = Path(failure_report_path)
        if not report_path.exists():
            return "Error: Failure report not found."

        with open(report_path, 'r') as f:
            report_content = f.read()[-2000:]

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
            
            match = re.search(r"```(?:markdown|text|)\n(.*?)\n```", response, re.DOTALL)
            if match:
                snippet = match.group(1).strip()
                (self.workspace_dir / "reports" / "suggested_patch_raw.txt").write_text(snippet)

            return f"Patch suggested based on failures: {patch_path}"
        
        return "Error: Could not generate remediation patch."

    def apply_patch(self):
        import json
        raw_patch_path = self.workspace_dir / "reports" / "suggested_patch_raw.txt"
        if not raw_patch_path.exists():
            return "Error: No raw patch found to apply."

        snippet = raw_patch_path.read_text()

        if not self.manifest_path.exists():
            return "Error: Manifest missing."

        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)

        if 'safety_policy' not in manifest:
            manifest['safety_policy'] = {}
        
        manifest['safety_policy']['hardened_prompt'] = snippet

        with open(self.manifest_path, 'w') as f:
            json.dump(manifest, f, indent=4)

        return "Patch applied to project-manifest.json successfully."

remediator = Remediator()
