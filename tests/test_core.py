import sys
import os
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Mock llm_guard before importing sentry to avoid OOM in some environments
with patch("llm_guard.input_scanners.PromptInjection"), \
     patch("llm_guard.input_scanners.Toxicity"), \
     patch("llm_guard.input_scanners.Anonymize"), \
     patch("llm_guard.input_scanners.Secrets"), \
     patch("llm_guard.input_scanners.Gibberish"), \
     patch("llm_guard.input_scanners.BanSubstrings"), \
     patch("llm_guard.output_scanners.NoRefusal"), \
     patch("llm_guard.output_scanners.Sensitive"), \
     patch("llm_guard.output_scanners.Toxicity"), \
     patch("llm_guard.output_scanners.Deanonymize"), \
     patch("llm_guard.output_scanners.BanSubstrings"), \
     patch("llm_guard.output_scanners.Bias"), \
     patch("llm_guard.output_scanners.Relevance"):
    from core.discovery import discovery
    from core.sentry import sentry, Sentry
    from core.provider import provider

def test_discovery_basic():
    """Verify discovery logic returns project structure."""
    report = discovery.get_discovery_report()
    assert isinstance(report, dict)
    assert "code" in report
    assert "interfaces" in report
    assert "running" in report

def test_sentry_initialization():
    """Verify Sentry loads default policy if manifest missing."""
    with patch("pathlib.Path.exists", return_value=False):
        custom_sentry = Sentry("nonexistent.json")
        status = custom_sentry.get_status()
        assert len(status["input_scanners"]) >= 4
        # Since we mock at module level, they might appear by name
        assert any(s in status["input_scanners"] for s in ["PromptInjection", "MagicMock"])

def test_provider_model_selection():
    """Verify provider maps models correctly."""
    with patch.dict(os.environ, {"AI_RMF_MODEL": "gemini-3.1-pro"}):
        from core.provider import LLMProvider
        p = LLMProvider()
        # Mocking the actual call or just checking the property
        assert "gemini" in p.model.lower()

def test_sentry_validation_mock():
    """Verify Sentry validation logic with mocked llm_guard."""
    with patch("core.sentry.scan_prompt", return_value=("safe prompt", True, 0.0)):
        res, is_valid, score = sentry.validate_input("Hello")
        assert is_valid is True
        assert res == "safe prompt"

def test_manifest_existence():
    """Verify project manifest is present in workspace."""
    manifest_path = BASE_DIR / "workspace" / "project-manifest.json"
    assert manifest_path.exists()
    with open(manifest_path, 'r') as f:
        data = json.load(f)
        assert "project_name" in data
