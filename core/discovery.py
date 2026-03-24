import os
import psutil
import json
import urllib.request
import socket
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
        self.ollama_api_url = "http://localhost:11434"
        self.common_ports = {
            11434: "Ollama",
            8000: "vLLM / OpenAI Compatible",
            18888: "Arize Phoenix",
            5001: "Local AI API",
            11435: "Ollama (Alternative)",
            8080: "Local LLM Server"
        }
        
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

    def verify_ollama_models(self):
        """Attempts to reach the local Ollama API to list installed models."""
        models = []
        try:
            # Try fetching available tags (models)
            req = urllib.request.Request(f"{self.ollama_api_url}/api/tags")
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    for m in data.get('models', []):
                        models.append({
                            "name": m.get('name'),
                            "size": f"{m.get('size', 0) / (1024**3):.2f} GB",
                            "status": "Installed"
                        })
            
            # Try fetching currently loaded (running) models
            req_ps = urllib.request.Request(f"{self.ollama_api_url}/api/ps")
            with urllib.request.urlopen(req_ps, timeout=1) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    for m in data.get('models', []):
                        for installed in models:
                            if installed['name'] == m.get('name'):
                                installed['status'] = "Loaded"
        except Exception:
            # Ollama not running or API not reachable, or other error
            pass
            
        return models

    def scan_network_interfaces(self):
        """Scans localhost for open AI-related ports."""
        found_interfaces = []
        for port, name in self.common_ports.items():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.1)
                    if s.connect_ex(('127.0.0.1', port)) == 0:
                        found_interfaces.append({
                            "name": name,
                            "port": port,
                            "host": "localhost",
                            "status": "Listening"
                        })
            except: continue
        return found_interfaces

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
        ai_keywords = ['openai', 'anthropic', 'langchain', 'llama', 'transformers', 'torch', 'tensorflow', 'vertexai', 'google.generativeai', 'haystack', 'autogen', 'crewai', 'mistralai', 'cohere', 'replicate']
        
        # 1. Check dependency files
        dep_files = ['requirements.txt', 'package.json', 'pyproject.toml', 'uv.lock', 'Cargo.toml']
        for df in dep_files:
            p = Path.cwd() / df
            if p.exists():
                try:
                    content = p.read_text().lower()
                    for kw in ai_keywords:
                        if kw in content:
                            findings["libraries"].append({"file": df, "keyword": kw})
                except: continue

        # 2. Scan source files for imports
        extensions = ['.py', '.js', '.ts', '.rs', '.go']
        try:
            for root, dirs, files in os.walk(Path.cwd()):
                if any(x in root for x in ['.venv', '.git', 'node_modules', '__pycache__']): continue
                for file in files:
                    if any(file.endswith(ext) for ext in extensions):
                        p = Path(root) / file
                        try:
                            # Read first 500 lines for speed
                            with open(p, 'r', errors='ignore') as f:
                                lines = [f.readline().lower() for _ in range(500)]
                            content = "".join(lines)
                            if any(f"import {kw}" in content or f"from {kw}" in content or f"require('{kw}')" in content for kw in ai_keywords):
                                findings["files_with_ai"].append(str(p.relative_to(Path.cwd())))
                                if len(findings["files_with_ai"]) > 10: break
                        except: continue
                if len(findings["files_with_ai"]) > 10: break
        except: pass
        
        return findings

    def detect_env_vars(self):
        """Scans .env files for AI-related API keys (without logging the values)."""
        env_findings = []
        ai_env_patterns = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'COHERE_API_KEY', 'MISTRAL_API_KEY', 'AWS_ACCESS_KEY', 'AZURE_OPENAI_KEY']
        
        env_files = ['.env', '.env.local', '.env.development', '.env.production']
        for ef in env_files:
            p = Path.cwd() / ef
            if p.exists():
                try:
                    content = p.read_text()
                    for pattern in ai_env_patterns:
                        if pattern in content:
                            env_findings.append({"file": ef, "key": pattern})
                except: continue
        return env_findings

    def detect_purpose(self):
        """Infers system purpose from environment and folder names."""
        purpose_hints = []
        # Check current folder name
        cwd_name = Path.cwd().name.lower()
        if any(x in cwd_name for x in ['chat', 'support', 'bot']):
            purpose_hints.append("Customer Interaction / Support")
        if any(x in cwd_name for x in ['code', 'dev', 'agent']):
            purpose_hints.append("Software Development / Coding Assistant")
        if any(x in cwd_name for x in ['medical', 'health', 'clinic']):
            purpose_hints.append("Healthcare / Medical Information")
        if any(x in cwd_name for x in ['finance', 'bank', 'trading']):
            purpose_hints.append("Financial Services")
            
        # Check env vars
        if os.getenv("DATABASE_URL"):
            purpose_hints.append("Database-integrated Application")
            
        return purpose_hints

    def suggest_manifest_fragment(self):
        """Generates a suggested project-manifest.json fragment based on discovery."""
        report = self.get_discovery_report()
        suggestion = {
            "project_name": Path.cwd().name,
            "ai_bom": [],
            "risk_profile": {"tier": "medium", "domain": "General AI Application"}
        }

        # Suggest AI-BOM from env vars
        for env in report.get("env_vars", []):
            provider_map = {
                "OPENAI": ("OpenAI", "model"),
                "ANTHROPIC": ("Anthropic", "model"),
                "GEMINI": ("Google", "model"),
                "GOOGLE": ("Google", "model"),
                "MISTRAL": ("Mistral", "api"),
                "COHERE": ("Cohere", "api")
            }
            for key_prefix, (provider, type) in provider_map.items():
                if env["key"].startswith(key_prefix):
                    suggestion["ai_bom"].append({
                        "component_id": f"{provider} Service",
                        "type": type,
                        "version": "latest",
                        "provider": provider
                    })

        # Suggest risk tier from purpose hints
        if any("Medical" in h or "Financial" in h for h in report.get("purpose_hints", [])):
            suggestion["risk_profile"]["tier"] = "high"
            suggestion["risk_profile"]["domain"] = report["purpose_hints"][0]
        elif any("Support" in h for h in report.get("purpose_hints", [])):
            suggestion["risk_profile"]["tier"] = "medium"
            suggestion["risk_profile"]["domain"] = "Customer Support"

        # Deduplicate AI-BOM
        seen = set()
        new_bom = []
        for item in suggestion["ai_bom"]:
            if item["component_id"] not in seen:
                seen.add(item["component_id"])
                new_bom.append(item)
        suggestion["ai_bom"] = new_bom

        return suggestion

    def get_discovery_report(self):
        """Returns a structured summary of findings."""
        return {
            "running": self.find_running_models(),
            "ollama_models": self.verify_ollama_models(),
            "interfaces": self.scan_network_interfaces(),
            "stored": self.scan_local_storage(),
            "code": self.scan_project_code(),
            "env_vars": self.detect_env_vars(),
            "purpose_hints": self.detect_purpose()
        }

discovery = ModelDiscovery()
