import sys
import json
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Mock before importing
with patch('core.utils.MANIFEST_PATH', Path("nonexistent.json")):
    import core.pf_provider as pf

def test_pf_provider_call_api():
    """Test the call_api function of the promptfoo provider."""
    with patch('core.pf_provider.provider.chat', return_value="Test response") as mock_chat:
        res = pf.call_api("Hello", {}, {})
        assert res["output"] == "Test response"
        mock_chat.assert_called_once()

def test_pf_provider_grounding_with_manifest():
    """Test if grounding message is correctly built from manifest."""
    mock_manifest = {
        "project_name": "Test Project",
        "safety_policy": {"prohibited_content": ["Hate Speech", "Violence"]},
        "accountability": {"security_contact": "security@example.com"},
        "risk_profile": {"tier": "high", "domain": "finance"},
        "benchmarks": {"target_accuracy": 0.95}
    }
    
    # We need to mock MANIFEST_PATH itself to return True for exists()
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True
    
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_manifest))), \
         patch('core.pf_provider.MANIFEST_PATH', mock_path):
        
        import importlib
        importlib.reload(pf)
        
        assert "Test Project" in pf.grounding_msg
        assert "Hate Speech, Violence" in pf.grounding_msg
        assert "security@example.com" in pf.grounding_msg
        assert "high" in pf.grounding_msg
        assert "95.0%" in pf.grounding_msg

def test_pf_provider_grounding_load_error():
    """Test handling of manifest loading error."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True

    with patch('builtins.open', side_effect=Exception("Read error")), \
         patch('core.pf_provider.MANIFEST_PATH', mock_path):
        
        import importlib
        importlib.reload(pf)
        
        assert "Context loading error" in pf.grounding_msg
