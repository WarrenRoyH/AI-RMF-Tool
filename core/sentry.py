import json
from pathlib import Path
from llm_guard import scan_prompt, scan_output
from llm_guard.vault import Vault
from llm_guard.input_scanners import Anonymize, PromptInjection, TokenLimit, Toxicity
from llm_guard.output_scanners import Deanonymize, NoRefusal, Relevance, Sensitive

class Sentry:
    """
    Phase 3: MANAGE (The Sentry)
    A local-first safety layer that enforces NIST AI RMF policies.
    """
    def __init__(self, manifest_path="workspace/project-manifest.json"):
        self.manifest_path = Path(manifest_path)
        self.vault = Vault()
        self.input_scanners = []
        self.output_scanners = []
        self._load_policy()

    def _load_policy(self):
        """Configures scanners based on the project manifest."""
        if not self.manifest_path.exists():
            # Default fallback policy
            self.input_scanners = [PromptInjection(), Toxicity()]
            self.output_scanners = [NoRefusal()]
            return

        with open(self.manifest_path, 'r') as f:
            policy = json.load(f)

        # 1. Input Scanners (Protecting the Model)
        self.input_scanners.append(PromptInjection())
        
        # Enable PII protection if requested in manifest
        if policy.get("safety_policy", {}).get("pii_protection"):
            self.input_scanners.append(Anonymize(self.vault))

        # 2. Output Scanners (Protecting the User)
        # Check for prohibited content domains (Mental Health, Finance, etc.)
        prohibited = policy.get("safety_policy", {}).get("prohibited_content", [])
        if prohibited:
            # We use a sensitive data scanner to look for keywords/patterns
            self.output_scanners.append(Sensitive(redact=True))
        
        # Ensure the model doesn't just "Refuse" valid help
        self.output_scanners.append(NoRefusal())

    def validate_input(self, prompt):
        """Scans and potentially redacts user input."""
        sanitized_prompt, is_valid, risk_score = scan_prompt(self.input_scanners, prompt)
        return sanitized_prompt, is_valid, risk_score

    def validate_output(self, prompt, response):
        """Scans and potentially redacts model output."""
        sanitized_response, is_valid, risk_score = scan_output(self.output_scanners, prompt, response)
        return sanitized_response, is_valid, risk_score

sentry = Sentry()
