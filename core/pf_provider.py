import sys
from pathlib import Path

# Add the project root to sys.path so we can import our core modules
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.provider import provider

def call_api(prompt, options, context):
    """
    Promptfoo Python Provider.
    This bridge ensures promptfoo uses the exact same LiteLLM config and .env
    settings as the rest of the AI-RMF toolkit.
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Provide accurate and safe responses."},
        {"role": "user", "content": prompt}
    ]
    
    # This uses our central provider (with its mappings and .env keys)
    response = provider.chat(messages)
    
    return {
        "output": response
    }
