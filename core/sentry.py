import json
import logging
from pathlib import Path

# Configure logging to suppress debug noise from llm_guard and its dependencies
logging.getLogger("llm_guard").setLevel(logging.ERROR)

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
        self.shadow_mode = False
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

        # Load shadow mode setting
        self.shadow_mode = policy.get("safety_policy", {}).get("shadow_mode", False)

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

    def get_about_info(self):
        """Provides technical and NIST context for the Sentry component."""
        return {
            "NIST Function": "MANAGE (ID: MA-1, MA-2)",
            "Role": "Active Risk Mitigation and Guardrail Enforcement",
            "Logic": "Utilizes LLM-Guard to scan inputs for injections/PII and outputs for policy violations/hallucinations.",
            "Workflow": "Map (Identify) -> Measure (Quantify) -> Manage (Act/Enforce)"
        }

    def get_deployment_guide(self):
        """Provides architectural guidance on NIST-aligned deployment methods."""
        return {
            "1. Library (Native Integration)": "Embed the Sentry directly into your application code. This provides the lowest latency and highest control. Used when you have full access to the application lifecycle.",
            "2. Middleware / Proxy": "Deploy the Sentry as a standalone service (like a WAF for AI) that sits between the user and the LLM. Ideal for legacy systems or multi-model routing where you cannot change the app code.",
            "3. Prompt / System Guard": "Inject safety instructions directly into the System Prompt. This is the easiest to implement but the most vulnerable to jailbreaking (as seen in Phase 2). Best used as a secondary layer."
        }

    def get_status(self):
        """Returns a summary of the active scanners."""
        return {
            "input_scanners": [s.__class__.__name__ for s in self.input_scanners],
            "output_scanners": [s.__class__.__name__ for s in self.output_scanners],
            "vault_active": self.vault is not None
        }

sentry = Sentry()
