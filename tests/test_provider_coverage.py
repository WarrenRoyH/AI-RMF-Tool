import sys
import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.provider import LLMProvider, APIAdapter, LocalAdapter, WebAdapter, ProgramAdapter, QuotaExceededError

def test_api_adapter_chat():
    """Test APIAdapter chat functionality."""
    with patch('core.provider.completion') as mock_completion:
        mock_completion.return_value.choices[0].message.content = "API Response"
        adapter = APIAdapter(model="gpt-4o")
        res = adapter.chat([{"role": "user", "content": "Hi"}])
        assert res == "API Response"

def test_api_adapter_quota_exceeded():
    """Test APIAdapter handling of 429 errors."""
    with patch('core.provider.completion', side_effect=Exception("Rate limit 429")):
        adapter = APIAdapter(model="gpt-4o")
        try:
            adapter.chat([{"role": "user", "content": "Hi"}])
        except QuotaExceededError as e:
            assert "Quota reached" in str(e)

def test_local_adapter_chat():
    """Test LocalAdapter chat functionality."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {"message": {"content": "Local Response"}}
        adapter = LocalAdapter(endpoint="http://localhost:11434/api/chat", model="llama3")
        res = adapter.chat([{"role": "user", "content": "Hi"}])
        assert res == "Local Response"

def test_program_adapter_chat():
    """Test ProgramAdapter chat functionality."""
    with patch('subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("Program Output", "")
        mock_popen.return_value = mock_process
        
        adapter = ProgramAdapter(binary_path="/usr/bin/test")
        res = adapter.chat([{"role": "user", "content": "Hi"}])
        assert res == "Program Output"

def test_llm_provider_chat_modes():
    """Test different chat modes in LLMProvider."""
    provider = LLMProvider()
    
    # Mock adapters
    provider.adapter = MagicMock()
    provider.target_adapter = MagicMock()
    provider.test_adapters = {m: MagicMock() for m in provider.test_model_pool}
    
    provider.chat("msg")
    provider.adapter.chat.assert_called_with("msg")
    
    provider.chat("msg", use_target=True)
    provider.target_adapter.chat.assert_called_with("msg")
    
    provider.chat("msg", use_test_model=True)
    # Check if one of test_adapters was called
    any_called = any(a.chat.called for a in provider.test_adapters.values())
    assert any_called

def test_llm_provider_validate_setup():
    """Test validate_setup method."""
    provider = LLMProvider()
    provider.adapter = MagicMock()
    provider.adapter.api_key = "test_key"
    assert provider.validate_setup() is True
    
    provider.adapter.api_key = None
    try:
        provider.validate_setup()
    except ValueError as e:
        assert "API Key missing" in str(e)
