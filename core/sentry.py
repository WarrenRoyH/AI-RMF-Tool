import json
import logging
import os
from pathlib import Path

# Force CPU for llm-guard to save VRAM for the main LLM processes
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Configure logging to suppress debug noise from llm_guard and its dependencies
logging.getLogger("llm_guard").setLevel(logging.ERROR)

try:
    from llm_guard import scan_prompt, scan_output
    from llm_guard.vault import Vault
    from llm_guard.input_scanners import (
        Anonymize, PromptInjection, TokenLimit, Toxicity, 
        BanSubstrings, Gibberish, Secrets
    )
    from llm_guard.output_scanners import (
        Deanonymize, NoRefusal, Relevance, Sensitive,
        Toxicity as OutputToxicity, Bias, BanSubstrings as OutputBanSubstrings
    )
except ImportError as e:
    logging.error(f"Failed to import llm-guard: {e}")
    # Fallback placeholders for environments where llm-guard is missing
    scan_prompt = lambda scanners, p: (p, True, 0.0)
    scan_output = lambda scanners, p, r: (r, True, 0.0)
    Vault = lambda: None

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
        self.input_scanners = []
        self.output_scanners = []

        try:
            # Default mandatory scanners (Core NIST AI RMF protections)
            self.input_scanners.append(PromptInjection())
            self.input_scanners.append(Toxicity())
            self.input_scanners.append(Secrets())
            self.input_scanners.append(Gibberish())
            
            # Default output protections
            self.output_scanners.append(NoRefusal())
            self.output_scanners.append(OutputToxicity())
        except Exception as e:
            logging.error(f"Error initializing default scanners: {e}")

        if not self.manifest_path.exists():
            return

        try:
            with open(self.manifest_path, 'r') as f:
                policy_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        safety = policy_data.get("safety_policy", {})
        self.shadow_mode = safety.get("shadow_mode", False)

        # 1. Input Scanners (Protecting the Model)
        try:
            # Enable PII protection if requested in manifest
            if safety.get("pii_protection") and self.vault:
                self.input_scanners.append(Anonymize(self.vault))

            # Handle prohibited content substrings
            prohibited = safety.get("prohibited_content", [])
            if prohibited:
                self.input_scanners.append(BanSubstrings(substrings=prohibited))
        except Exception as e:
            logging.error(f"Error initializing manifest-based input scanners: {e}")

        # 2. Output Scanners (Protecting the User)
        try:
            # Deanonymize if PII protection was active
            if safety.get("pii_protection") and self.vault:
                self.output_scanners.append(Deanonymize(self.vault))

            # Check for sensitive data (PII, secrets) in output
            self.output_scanners.append(Sensitive(redact=True))
            
            if prohibited:
                # We use both Sensitive and BanSubstrings for maximum coverage
                self.output_scanners.append(OutputBanSubstrings(substrings=prohibited))
            
            # Add Bias detection for high-risk domains
            if policy_data.get("risk_profile", {}).get("tier") == "high":
                self.output_scanners.append(Bias())

            # Add Relevance to ensure output isn't hallucinating unrelated content
            self.output_scanners.append(Relevance())
        except Exception as e:
            logging.error(f"Error initializing manifest-based output scanners: {e}")

    def send_notification(self, log_entry):
        """Sends an alert via Resend for Phase 10: Refined Feedback Loop."""
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            return

        try:
            import resend
            resend.api_key = api_key
            
            # Load contact from manifest
            contact = "security@example.com"
            project_name = "AI-RMF Tool"
            if self.manifest_path.exists():
                with open(self.manifest_path, 'r') as f:
                    data = json.load(f)
                    contact = data.get("accountability", {}).get("security_contact", contact)
                    project_name = data.get("project_name", project_name)

            params = {
                "from": "AI-RMF Sentry <onboarding@resend.dev>",
                "to": [contact],
                "subject": f"[ALERT] Policy Violation Detected: {project_name}",
                "html": f"""
                <h2>NIST AI RMF Policy Violation</h2>
                <p><strong>Project:</strong> {project_name}</p>
                <p><strong>Type:</strong> {log_entry['type']}</p>
                <p><strong>Risk Score:</strong> {log_entry['risk_score']}</p>
                <p><strong>Timestamp:</strong> {log_entry['timestamp']}</p>
                <hr>
                <p><strong>Original Input:</strong><br><pre>{log_entry['original']}</pre></p>
                <p><strong>Action Required:</strong> Please review this violation in the AI-RMF Dashboard.</p>
                """
            }
            resend.Emails.send(params)
        except Exception as e:
            logging.error(f"Failed to send Resend notification: {e}")

    def log_violation(self, violation_type, original, risk_score, sanitized=None):
        """Logs a policy violation for Phase 10: Advisory Kill-Switch."""
        LOG_PATH = Path("workspace/logs/sentry_violations.jsonl")
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "type": violation_type,
            "original": original,
            "sanitized": sanitized,
            "risk_score": risk_score,
            "status": "pending" if not self.shadow_mode else "shadow_blocked"
        }
        
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Trigger notification for high-risk violations
        self.send_notification(log_entry)
        
        return log_entry

    def validate_input(self, prompt):
        """Scans and potentially redacts user input."""
        if not self.input_scanners:
            return prompt, True, 0.0
        try:
            sanitized_prompt, is_valid, risk_score = scan_prompt(self.input_scanners, prompt)
            
            # llm-guard can return a bool or a dict of {scanner: bool}
            if is_valid is False or (isinstance(is_valid, dict) and any(v is False for v in is_valid.values())):
                self.log_violation("input_violation", prompt, risk_score, sanitized_prompt)
            return sanitized_prompt, is_valid, risk_score
        except Exception as e:
            logging.error(f"Sentry input validation error: {e}")
            return prompt, True, 0.0

    def validate_output(self, prompt, response):
        """Scans and potentially redacts model output."""
        if not self.output_scanners:
            return response, True, 0.0
        try:
            sanitized_response, is_valid, risk_score = scan_output(self.output_scanners, prompt, response)
            if is_valid is False or (isinstance(is_valid, dict) and any(v is False for v in is_valid.values())):
                self.log_violation("output_violation", response, risk_score, sanitized_response)
            return sanitized_response, is_valid, risk_score
        except Exception as e:
            logging.error(f"Sentry output validation error: {e}")
            return response, True, 0.0

    def get_about_info(self):
        """Provides technical and NIST context for the Sentry component."""
        return {
            "NIST Function": "MANAGE (ID: MA-1, MA-2)",
            "Role": "Active Risk Mitigation and Guardrail Enforcement",
            "Logic": "Utilizes LLM-Guard to scan inputs for injections/PII/secrets and outputs for policy violations/bias/hallucinations.",
            "Workflow": "Map (Identify) -> Measure (Quantify) -> Manage (Act/Enforce)"
        }

    def get_status(self):
        """Returns a summary of the active scanners."""
        return {
            "input_scanners": [s.__class__.__name__ for s in self.input_scanners],
            "output_scanners": [s.__class__.__name__ for s in self.output_scanners],
            "vault_active": self.vault is not None,
            "shadow_mode": self.shadow_mode,
            "policy_source": str(self.manifest_path) if self.manifest_path.exists() else "default"
        }

sentry = Sentry()


