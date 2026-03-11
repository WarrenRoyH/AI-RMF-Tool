import os
import psutil
from pathlib import Path

class ModelDiscovery:
    """
    Local-only discovery tool for identifying AI systems and models.
    Operates without external LLM calls to ensure privacy.
    """
    def __init__(self):
        self.common_paths = [
            Path.home() / ".ollama" / "models",
            Path.home() / ".cache" / "huggingface" / "hub",
            Path.home() / ".cache" / "lm-studio" / "models",
            Path("/usr/share/ollama/.ollama/models")
        ]
        
    def find_running_models(self):
        """Checks for common AI-serving processes."""
        running = []
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                name = proc.info['name'].lower()
                cmdline = " ".join(proc.info['cmdline'] or []).lower()
                
                if 'ollama' in name:
                    running.append({"type": "Ollama", "pid": proc.pid})
                elif 'vllm' in cmdline:
                    running.append({"type": "vLLM", "pid": proc.pid})
                elif 'python' in name and ('llama' in cmdline or 'transformers' in cmdline):
                    running.append({"type": "Python/Transformer", "pid": proc.pid})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return running

    def scan_local_storage(self):
        """Scans common directories for model files."""
        found_models = []
        for path in self.common_paths:
            if path.exists():
                # Check for .gguf files or common manifest files
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith(".gguf") or file == "config.json":
                            found_models.append(f"{path.name}: {file}")
                            if len(found_models) > 5: break # Limit results
        return found_models

    def detect_purpose(self):
        """Infers system purpose from environment and folder names."""
        purpose_hints = []
        # Check current folder name
        cwd_name = Path.cwd().name.lower()
        if any(x in cwd_name for x in ['chat', 'support', 'bot']):
            purpose_hints.append("Customer Interaction / Support")
        if any(x in cwd_name for x in ['code', 'dev', 'agent']):
            purpose_hints.append("Software Development / Coding Assistant")
            
        # Check env vars
        if os.getenv("DATABASE_URL"):
            purpose_hints.append("Database-integrated Application")
            
        return purpose_hints

    def get_discovery_report(self):
        """Returns a structured summary of findings."""
        return {
            "running": self.find_running_models(),
            "stored": self.scan_local_storage(),
            "purpose_hints": self.detect_purpose()
        }

discovery = ModelDiscovery()
