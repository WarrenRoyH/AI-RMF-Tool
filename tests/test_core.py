import sys
import os
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

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
    with patch.dict(os.environ, {"AI_RMF_AUDITOR_MODEL": "gemini-3.1-pro"}):
        from core.provider import LLMProvider
        p = LLMProvider()
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

def test_api_adapter_mock():
    """Test APIAdapter chat logic."""
    from core.provider import APIAdapter
    adapter = APIAdapter("gpt-4")
    
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "GPT Response"
    
    with patch('core.provider.completion', return_value=mock_response):
        res = adapter.chat([{"role": "user", "content": "Hi"}])
        assert res == "GPT Response"

def test_local_adapter_mock():
    """Test LocalAdapter chat logic."""
    from core.provider import LocalAdapter
    adapter = LocalAdapter("http://localhost:11434", "llama3")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "Llama Response"}}
    
    with patch('requests.post', return_value=mock_response):
        res = adapter.chat([{"role": "user", "content": "Hi"}])
        assert res == "Llama Response"

def test_program_adapter_mock():
    """Test ProgramAdapter chat logic."""
    from core.provider import ProgramAdapter
    adapter = ProgramAdapter("/usr/bin/python3")
    
    with patch('subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("Program Output", "")
        mock_popen.return_value = mock_process
        
        res = adapter.chat([{"role": "user", "content": "Hi"}])
        assert res == "Program Output"

def test_provider_chat_pooling():
    """Verify test model pooling logic."""
    from core.provider import LLMProvider
    p = LLMProvider()
    
    # Mock all test adapters
    for model_id in p.test_model_pool:
        p.test_adapters[model_id] = MagicMock()
        p.test_adapters[model_id].chat.return_value = f"Response from {model_id}"
    
    res1 = p.chat([{"role": "user", "content": "Hi"}], use_test_model=True)
    assert res1 == f"Response from {p.test_model_pool[0]}"
    
    res2 = p.chat([{"role": "user", "content": "Hi"}], use_test_model=True)
    assert res2 == f"Response from {p.test_model_pool[1]}"

def test_sentry_validate_output_mock():
    """Verify Sentry output validation logic."""
    with patch("core.sentry.scan_output", return_value=("safe output", True, 0.0)):
        res, is_valid, score = sentry.validate_output("Prompt", "Response")
        assert is_valid is True
        assert res == "safe output"

def test_sentry_load_policy_high_risk():
    """Verify Sentry loads extra scanners for high-risk tier."""
    mock_manifest = {
        "safety_policy": {"pii_protection": True, "prohibited_content": ["bad"]},
        "risk_profile": {"tier": "high"}
    }
    
    class MockScanner:
        def __init__(self, *args, **kwargs): pass

    # Mock all potential scanners to avoid real llm-guard initialization
    scanners_to_mock = [
        "PromptInjection", "Toxicity", "Secrets", "Gibberish", 
        "NoRefusal", "OutputToxicity", "Anonymize", "BanSubstrings",
        "Deanonymize", "Sensitive", "OutputBanSubstrings", "Bias", "Relevance"
    ]
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_manifest))):
        
        with patch("core.sentry.Vault", return_value=MagicMock()):
            # Use a dictionary to store mock classes
            mocks = {}
            for s in scanners_to_mock:
                # We need to mock them in core.sentry
                # Toxicity is imported as Toxicity and OutputToxicity
                target = f"core.sentry.{s}"
                m = patch(target, side_effect=lambda *args, **kwargs: MagicMock())
                # This is tricky because some are already imported.
                # Let's just mock the ones we check.
            
            AnonymizeMock = type("Anonymize", (MockScanner,), {})
            DeanonymizeMock = type("Deanonymize", (MockScanner,), {})
            BiasMock = type("Bias", (MockScanner,), {})

            with patch("core.sentry.PromptInjection", side_effect=MockScanner), \
                 patch("core.sentry.Toxicity", side_effect=MockScanner), \
                 patch("core.sentry.Secrets", side_effect=MockScanner), \
                 patch("core.sentry.Gibberish", side_effect=MockScanner), \
                 patch("core.sentry.NoRefusal", side_effect=MockScanner), \
                 patch("core.sentry.OutputToxicity", side_effect=MockScanner), \
                 patch("core.sentry.Anonymize", side_effect=AnonymizeMock), \
                 patch("core.sentry.Deanonymize", side_effect=DeanonymizeMock), \
                 patch("core.sentry.Bias", side_effect=BiasMock), \
                 patch("core.sentry.Relevance", side_effect=MockScanner), \
                 patch("core.sentry.Sensitive", side_effect=MockScanner), \
                 patch("core.sentry.OutputBanSubstrings", side_effect=MockScanner), \
                 patch("core.sentry.BanSubstrings", side_effect=MockScanner):

                custom_sentry = Sentry("manifest.json")
                status = custom_sentry.get_status()
                assert "Bias" in status["output_scanners"]
                assert "Anonymize" in status["input_scanners"]
@patch('core.sentry.os.getenv', return_value="fake_key")
@patch('resend.Emails.send')
def test_sentry_send_notification(mock_resend_send, mock_getenv):
    """Verify Sentry sends notifications on violation."""
    log_entry = {
        "type": "input_violation",
        "original": "bad prompt",
        "risk_score": 0.9,
        "timestamp": "2026-03-23"
    }
    sentry.send_notification(log_entry)
    mock_resend_send.assert_called_once()

def test_sentry_log_violation():
    """Verify Sentry logs violations to file."""
    with patch("pathlib.Path.mkdir"), \
         patch("builtins.open", mock_open()) as mocked_file, \
         patch("core.sentry.Sentry.send_notification"):
        log_entry = sentry.log_violation("test_type", "original", 0.5)
        assert log_entry["type"] == "test_type"
        mocked_file().write.assert_called()

def test_sentry_validate_input_invalid():
    """Verify Sentry handles invalid input detection."""
    with patch("core.sentry.scan_prompt", return_value=("sanitized", False, 0.8)), \
         patch("core.sentry.Sentry.log_violation") as mock_log:
        res, is_valid, score = sentry.validate_input("bad prompt")
        assert is_valid is False
        mock_log.assert_called_once()
