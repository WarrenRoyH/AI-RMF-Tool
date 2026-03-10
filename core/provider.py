import os
import sys
from dotenv import load_dotenv
from litellm import completion

# Load environment variables from .env
load_dotenv()

class LLMProvider:
    def __init__(self):
        self.model = os.getenv("AI_RMF_MODEL", "gpt-4o") # Default to gpt-4o, can be changed
        self.api_key = self._get_api_key()

    def _get_api_key(self):
        """
        Detects the correct API key based on the model provider.
        """
        if "gpt" in self.model:
            return os.getenv("OPENAI_API_KEY")
        elif "claude" in self.model:
            return os.getenv("ANTHROPIC_API_KEY")
        elif "gemini" in self.model:
            return os.getenv("GOOGLE_API_KEY")
        return None

    def validate_setup(self):
        """
        Ensures the necessary API keys are present before proceeding.
        """
        if not self.api_key and "ollama" not in self.model:
            print(f"Error: API Key missing for model '{self.model}'.")
            print("Please set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY in your .env file.")
            sys.exit(1)
        return True

    def chat(self, system_prompt, user_input):
        """
        A simple completion wrapper for persona-based interactions.
        """
        try:
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM Error: {str(e)}")
            sys.exit(1)

provider = LLMProvider()
