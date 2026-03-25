import sys
import json
import pytest
import os
import asyncio
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from fastapi.testclient import TestClient
from datetime import datetime

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Import targets
from core.pf_provider import call_api as pf_call_api
from core.provider import provider, LLMProvider
from core.proxy import app as proxy_app
from cli.dashboard import app as dashboard_app, run_sync as dash_run_sync
from core.auditor import auditor

# --- 1. core/pf_provider.py tests (Target 100%) ---
def test_pf_provider_full_manifest():
    mock_manifest = {
        "project_name": "Test Project",
        "safety_policy": {"prohibited_content": ["Hate Speech", "Violence"]},
        "accountability": {"security_contact": "security@example.com"},
        "risk_profile": {"tier": "high", "domain": "finance"},
        "benchmarks": {"target_accuracy": "0.95"} # String to test the fix
    }
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_manifest))), \
         patch('core.provider.provider.chat', return_value="Manifest-aware Response"):
        
        import importlib
        import core.pf_provider
        importlib.reload(core.pf_provider)
        
        result = core.pf_provider.call_api("Hello", {}, {})
        assert result["output"] == "Manifest-aware Response"
        assert "Test Project" in core.pf_provider.grounding_msg
        assert "95.0%" in core.pf_provider.grounding_msg

# --- 2. core/provider.py tests ---
def test_provider_chat_target():
    with patch.object(provider.target_adapter, 'chat', return_value="Target Resp"):
        res = provider.chat("hi", use_target=True)
        assert res == "Target Resp"

def test_provider_initialization_no_keys():
    with patch.dict(os.environ, {}, clear=True):
        p = LLMProvider()
        assert p.test_model_pool is not None

# --- 3. core/proxy.py tests ---
proxy_client = TestClient(proxy_app)

def test_proxy_input_block_no_shadow():
    with patch('core.sentry.sentry.validate_input', return_value=("", False, 0.9)), \
         patch('core.sentry.sentry.shadow_mode', False), \
         patch('core.proxy.log_violation'):
        response = proxy_client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "bad"}]})
        assert "violates safety policies" in response.json()["choices"][0]["message"]["content"]

# --- 4. cli/dashboard.py tests ---
dashboard_client = TestClient(dashboard_app)

def test_dashboard_read_index():
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data="<html></html>")):
        response = dashboard_client.get("/")
        assert response.status_code == 200
        assert "<html>" in response.text

def test_dashboard_get_manifest():
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data='{"name": "test"}')):
        response = dashboard_client.get("/manifest")
        assert response.json()["name"] == "test"

def test_dashboard_sync_post():
    with patch('builtins.open', mock_open()), \
         patch('cli.dashboard.run_sync'):
        response = dashboard_client.post("/sync", json={"name": "new"})
        assert response.status_code == 200

def test_dashboard_logs_stream():
    # Testing streaming is hard, but we can test if it returns a response
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data="log line\n")):
        response = dashboard_client.get("/logs/stream")
        assert response.status_code == 200

def test_dashboard_health_logic_variants():
    # Test secure vault
    with patch.dict(os.environ, {"HOST_OPENAI_API_KEY": "h", "TARGET_OPENAI_API_KEY": "t"}):
        with patch('socket.socket.connect_ex', return_value=1):
            response = dashboard_client.get("/health")
            assert response.json()["vault"] == "online"
            assert response.json()["proxy"] == "offline"

# --- 5. core/auditor.py tests ---
def test_auditor_sast():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Success")
        res = auditor.run_sast_scan()
        assert res is not None

def test_auditor_compliance_audit():
    with patch('core.auditor.auditor.run_infra_audit', return_value="Infra OK"), \
         patch('core.auditor.auditor.run_sast_scan', return_value="SAST OK"), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data='{}')):
        res = auditor.run_compliance_audit()
        assert "Infra OK" in res

def test_auditor_drift_check():
    res = auditor.check_drift(0.5) # accuracy 0.5 < 0.9
    assert "ALERT" in res or "Drift" in res

# --- 6. core/utils.py tests ---
from core.utils import obfuscator
def test_obfuscator_coverage():
    text = "Hello World"
    assert obfuscator.b64_encode(text) != text
    assert obfuscator.rot13_encode(text) != text
    assert obfuscator.unicode_homoglyph_smuggling(text) != text

# --- 7. core/jailbreak_engine.py tests ---
from core.jailbreak_engine import jailbreak_engine
def test_jailbreak_engine_techniques():
    assert "Logical Entrapment" in jailbreak_engine.techniques
    with patch('core.provider.provider.chat', return_value="Jailbreak Prompt"), \
         patch('core.sentry.sentry.validate_input', return_value=("safe", True, 0.1)):
        res = jailbreak_engine.run_dynamic_probe("Semantic Masking", "Policy")
        assert res["status"] == "PASSED"
