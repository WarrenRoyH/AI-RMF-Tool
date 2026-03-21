import os
import sys
import json
import subprocess
from dotenv import load_dotenv
from litellm import completion

# Load environment variables from .env
load_dotenv()

class QuotaExceededError(Exception):
    """Exception raised when API quota is reached (429)."""
    pass

class BaseAdapter:
    def chat(self, messages):
        raise NotImplementedError("Adapters must implement chat()")

class APIAdapter(BaseAdapter):
    def __init__(self, model):
        self.model = model
        self.api_key = self._get_api_key()

    def _get_api_key(self):
        if "gpt" in self.model: return os.getenv("OPENAI_API_KEY")
        elif "claude" in self.model: return os.getenv("ANTHROPIC_API_KEY")
        elif "gemini" in self.model: return os.getenv("GOOGLE_API_KEY")
        return None

    def chat(self, messages):
        try:
            response = completion(model=self.model, messages=messages)
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
            "gpt-4o": "gpt-5.4-pro",
            "claude-3-5-sonnet": "claude-4-sonnet-20260217"
        }
        
        # Core model for primary reasoning (The Optimizer Agent)
        raw_model = os.getenv("AI_RMF_MODEL", "gemini/gemini-3.1-pro-preview")
        self.model = self.model_map.get(raw_model.replace("gemini/", ""), raw_model)
        
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

        self.target_type = os.getenv("AI_RMF_TARGET_TYPE", "api").lower()
        self.target_url = os.getenv("AI_RMF_TARGET_URL")
        
        # Initialize adapters
        self.adapter = self._initialize_adapter(self.model)
        self.test_adapters = {m: self._initialize_adapter(m) for m in self.test_model_pool}

    def _initialize_adapter(self, model_id):
        if self.target_type == "web":
            return WebAdapter(self.target_url)
        elif self.target_type == "local":
            return LocalAdapter(self.target_url, model_id)
        elif self.target_type == "program":
            return ProgramAdapter(self.target_url)
        else:
            return APIAdapter(model_id)

    def validate_setup(self):
        if self.target_type == "api":
            if not self.adapter.api_key and "ollama" not in self.model:
                raise ValueError(f"API Key missing for model '{self.model}'. Please set the appropriate environment variable (e.g., GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY) in your .env file.")
        return True

    def chat(self, messages, use_test_model=False):
        """
        Standard chat method. 
        If use_test_model is True, cycles through available Flash models to conserve Pro quota.
        """
        if use_test_model:
            model_id = self.test_model_pool[self._test_model_index]
            self._test_model_index = (self._test_model_index + 1) % len(self.test_model_pool)
            return self.test_adapters[model_id].chat(messages)
            
        return self.adapter.chat(messages)

provider = LLMProvider()
