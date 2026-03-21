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
                try:
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if file.endswith(".gguf") or file == "config.json":
                                found_models.append(f"{path.name}: {file}")
                                if len(found_models) > 5: break
                except: continue
        return found_models

    def scan_project_code(self):
        """Scans the current directory for AI imports and dependencies."""
        findings = {"libraries": [], "files_with_ai": []}
        ai_keywords = ['openai', 'anthropic', 'langchain', 'llama', 'transformers', 'torch', 'tensorflow', 'vertexai', 'google.generativeai']
        
        # 1. Check dependency files
        dep_files = ['requirements.txt', 'package.json', 'pyproject.toml']
        for df in dep_files:
            p = Path.cwd() / df
            if p.exists():
                try:
                    content = p.read_text().lower()
                    for kw in ai_keywords:
                        if kw in content:
                            findings["libraries"].append(f"{df}: {kw}")
                except: continue

        # 2. Scan source files for imports
        extensions = ['.py', '.js', '.ts']
        try:
            for root, dirs, files in os.walk(Path.cwd()):
                if '.venv' in root or '.git' in root: continue
                for file in files:
                    if any(file.endswith(ext) for ext in extensions):
                        p = Path(root) / file
                        try:
                            content = p.read_text().lower()
                            if any(f"import {kw}" in content or f"from {kw}" in content for kw in ai_keywords):
                                findings["files_with_ai"].append(file)
                                if len(findings["files_with_ai"]) > 5: break
                        except: continue
                if len(findings["files_with_ai"]) > 5: break
        except: pass
        
        return findings

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

    def scan_network_interfaces(self):
        """Scans common ports for AI services and web applications."""
        import socket
        targets = [
            ("Ollama", 11434),
            ("vLLM / OpenAI-Compat", 8000),
            ("LM Studio", 1234),
            ("TGW / WebUI", 7860),
            ("Local Analytics App", 3000),
            ("Local Dev App", 5000),
            ("Sentry Proxy", 8080)
        ]
        
        found_interfaces = []
        for name, port in targets:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    found_interfaces.append({"name": name, "port": port, "url": f"http://localhost:{port}"})
        return found_interfaces

    def get_discovery_report(self):
        """Returns a structured summary of findings."""
        return {
            "running": self.find_running_models(),
            "interfaces": self.scan_network_interfaces(),
            "stored": self.scan_local_storage(),
            "code": self.scan_project_code(),
            "purpose_hints": self.detect_purpose()
        }

discovery = ModelDiscovery()
