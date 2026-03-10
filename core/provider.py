import os
import sys
from dotenv import load_dotenv
from litellm import completion

# Load environment variables from .env
load_dotenv()

class LLMProvider:
    def __init__(self):
        # Normalization mapping for March 2026
        self.model_map = {
            "gemini-1.5-pro": "gemini/gemini-3.1-pro-preview",
            "gemini-3-pro": "gemini/gemini-3.1-pro-preview",
            "gemini-1.5-flash": "gemini/gemini-3.1-flash-lite-preview",
            "gpt-4o": "gpt-5.4-pro",
            "claude-3-5-sonnet": "claude-4-sonnet-20260217"
        }
        
        raw_model = os.getenv("AI_RMF_MODEL", "gpt-5.4-pro")
        self.model = self.model_map.get(raw_model.replace("gemini/", ""), raw_model)
        
        if "gemini" in self.model and not self.model.startswith("gemini/"):
            self.model = f"gemini/{self.model}"
            
        self.api_key = self._get_api_key()

    def _get_api_key(self):
        if "gpt" in self.model: return os.getenv("OPENAI_API_KEY")
        elif "claude" in self.model: return os.getenv("ANTHROPIC_API_KEY")
        elif "gemini" in self.model: return os.getenv("GOOGLE_API_KEY")
        return None

    def validate_setup(self):
        if not self.api_key and "ollama" not in self.model:
            print(f"Error: API Key missing for model '{self.model}'.")
            sys.exit(1)
        return True

    def chat(self, messages):
        """
        Takes a full list of messages (history) and returns the LLM's response.
        """
        try:
            response = completion(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM Error: {str(e)}")
            sys.exit(1)

provider = LLMProvider()
