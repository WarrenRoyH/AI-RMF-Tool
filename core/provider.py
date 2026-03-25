import os
import sys
import json
import subprocess
import logging
from dotenv import load_dotenv
from litellm import completion

# Load environment variables from .env
load_dotenv()

from core.vault_security import VaultSecurity as Vault

# --- Arize Phoenix / OpenInference Instrumentation ---
# Instrumentation will automatically pick up PHOENIX_PORT if set by Inspector
try:
    # Set context to HOST for initialization
    Vault.set_context("HOST")
    phoenix_port = Vault.get("PHOENIX_PORT", "HOST")
    if phoenix_port:
        from phoenix.otel import register
        from openinference.instrumentation.litellm import LiteLLMInstrumentor
        
        endpoint = f"http://localhost:{phoenix_port}/v1/traces"
        register(
            project_name=Vault.get("PHOENIX_PROJECT_NAME", "HOST") or "ai-rmf-tools",
            endpoint=endpoint
        )
        LiteLLMInstrumentor().instrument()
except ImportError:
    pass
except Exception as e:
    logging.error(f"Failed to initialize observability instrumentation: {e}")

class QuotaExceededError(Exception):
    """Exception raised when API quota is reached (429)."""
    pass

class BaseAdapter:
    def chat(self, messages):
        raise NotImplementedError("Adapters must implement chat()")

class APIAdapter(BaseAdapter):
    def __init__(self, model, namespace="HOST"):
        self.model = model
        self.namespace = namespace
        self.api_key = self._get_api_key()

    def _get_api_key(self):
        # Context is already set by the caller (LLMProvider.chat)
        if "gpt" in self.model: return Vault.get("OPENAI_API_KEY", self.namespace)
        elif "claude" in self.model: return Vault.get("ANTHROPIC_API_KEY", self.namespace)
        elif "gemini" in self.model: return Vault.get("GOOGLE_API_KEY", self.namespace)
        return None

    def chat(self, messages):
        try:
            # Ensure the API key is current for the namespace context
            # (In case it was empty during init due to a test env)
            if not self.api_key:
                self.api_key = self._get_api_key()
            
            response = completion(model=self.model, messages=messages, api_key=self.api_key)
            return response.choices[0].message.content
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "rate_limit" in err_msg.lower() or "quota" in err_msg.lower():
                raise QuotaExceededError(f"Quota reached for {self.model}: {err_msg}")
            return f"API Error: {err_msg}"

class LocalAdapter(BaseAdapter):
    def __init__(self, endpoint, model):
        self.endpoint = endpoint or "http://localhost:11434/api/chat"
        self.model = model

    def chat(self, messages):
        try:
            import requests
            response = requests.post(
                self.endpoint,
                json={"model": self.model, "messages": messages, "stream": False}
            )
            return response.json().get("message", {}).get("content", "Error: No content")
        except Exception as e:
            return f"Local LLM Error: {str(e)}"

class WebAdapter(BaseAdapter):
    """
    Simulates interaction with a web-accessible LLM or App (e.g., spreadsheet upload).
    """
    def __init__(self, url):
        self.url = url

    def chat(self, messages):
        # Implementation would use playwright/selenium
        # For this toolkit, we provide a placeholder that identifies the intent
        prompt = messages[-1]["content"]
        return f"[WEB_TARGET_MOCK]: Successfully uploaded/processed prompt at {self.url}. Response captured from DOM."

class ProgramAdapter(BaseAdapter):
    """
    Interacts with a local program via stdin/stdout.
    """
    def __init__(self, binary_path):
        self.binary_path = binary_path

    def chat(self, messages):
        try:
            prompt = messages[-1]["content"]
            process = subprocess.Popen(
                [self.binary_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=prompt, timeout=30)
            return stdout if stdout else f"Program Error: {stderr}"
        except Exception as e:
            return f"Subprocess Error: {str(e)}"

class LLMProvider:
    def __init__(self):
        # Normalization mapping for March 2026
        self.model_map = {
            "gemini-3.1-pro": "gemini/gemini-3.1-pro-preview",
            "gemini-3.1-flash-lite": "gemini/gemini-3.1-flash-lite-preview",
            "gemini-3-flash": "gemini/gemini-3-flash-preview",
            "gemini-2.5-flash": "gemini/gemini-2.5-flash",
            "gemini-2.5-flash-lite": "gemini/gemini-2.5-flash-lite",
            "gpt-5.4-pro": "openai/gpt-5.4-pro",
            "gpt-5-nano": "openai/gpt-5-nano",
            "claude-4.6-sonnet": "anthropic/claude-4.6-sonnet-20260217",
            "claude-4-sonnet": "anthropic/claude-4.0-sonnet-20260217",
            "deepseek-r1": "deepseek/deepseek-r1",
            "deepseek-r2-lite": "deepseek/deepseek-r2-lite-202603",
            "gpt-4o": "openai/gpt-5.4-pro",
            "claude-3-5-sonnet": "anthropic/claude-4.0-sonnet-20260217"
        }
        
        # Core model for primary reasoning (The Auditor / Optimizer Agent)
        # Using Vault for Model IDs
        raw_auditor_model = Vault.get("AI_RMF_AUDITOR_MODEL", "HOST") or Vault.get("AI_RMF_MODEL", "HOST") or "gemini/gemini-3.1-pro-preview"
        self.model = self.model_map.get(raw_auditor_model.replace("gemini/", ""), raw_auditor_model)
        
        # Target model (The application infrastructure being assessed)
        self.target_model = Vault.get("AI_RMF_TARGET_MODEL", "TARGET") or self.model
        
        # Pool of test models to conserve Pro quota
        self.test_model_pool = [
            "gemini/gemini-3.1-flash-lite-preview",
            "gemini/gemini-3-flash-preview",
            "gemini/gemini-2.5-flash",
            "gemini/gemini-2.5-flash-lite"
        ]
        self._test_model_index = 0

        if "gemini" in self.model and not self.model.startswith("gemini/"):
            self.model = f"gemini/{self.model}"

        self.target_type = (Vault.get("AI_RMF_TARGET_TYPE", "TARGET") or "api").lower()
        self.target_url = Vault.get("AI_RMF_TARGET_URL", "TARGET")
        
        # Initialize adapters
        self.adapter = self._initialize_adapter(self.model, namespace="HOST") # The Auditor
        self.target_adapter = self._initialize_adapter(self.target_model, namespace="TARGET") # The SUT
        self.test_adapters = {m: self._initialize_adapter(m, namespace="HOST") for m in self.test_model_pool}


    def _initialize_adapter(self, model_id, namespace="HOST"):
        if self.target_type == "web":
            return WebAdapter(self.target_url)
        elif self.target_type == "local":
            return LocalAdapter(self.target_url, model_id)
        elif self.target_type == "program":
            return ProgramAdapter(self.target_url)
        else:
            return APIAdapter(model_id, namespace=namespace)

    def validate_setup(self):
        if self.target_type == "api":
            if not self.adapter.api_key and "ollama" not in self.model:
                raise ValueError(f"API Key missing for Auditor model '{self.model}'. Please set the appropriate environment variable (e.g., HOST_GOOGLE_API_KEY) in your .env file.")
            
            if not self.target_adapter.api_key and "ollama" not in self.target_model:
                logging.warning(f"API Key missing for Target model '{self.target_model}'. Please set the appropriate environment variable (e.g., TARGET_GOOGLE_API_KEY) in your .env file.")
        return True

    def chat(self, messages, use_test_model=False, use_target=False):
        """
        Standard chat method. 
        If use_test_model is True, cycles through available Flash models to conserve Pro quota.
        If use_target is True, uses the Target model (System Under Test).
        """
        # T2: Dynamically set the Vault context based on the operation type.
        # This prevents accidental credential leak even if internal adapters share state.
        if use_target:
            Vault.set_context("TARGET")
        else:
            Vault.set_context("HOST")
            
        try:
            if use_test_model:
                model_id = self.test_model_pool[self._test_model_index]
                self._test_model_index = (self._test_model_index + 1) % len(self.test_model_pool)
                return self.test_adapters[model_id].chat(messages)
            
            if use_target:
                return self.target_adapter.chat(messages)
                
            return self.adapter.chat(messages)
        finally:
            # Safety: Reset to HOST context after the operation.
            Vault.set_context("HOST")

provider = LLMProvider()
