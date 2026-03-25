import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.jailbreak_engine import JailbreakEngine

def test_run_dynamic_probe_with_obfuscation():
    """Test jailbreak probe with Unicode Smuggling obfuscation."""
    engine = JailbreakEngine()
    
    with patch('core.provider.provider.chat', return_value="apple"), \
         patch('core.sentry.sentry.validate_input', return_value=("", True, 0.1)), \
         patch('core.utils.obfuscator.unicode_homoglyph_smuggling', return_value="аррlе") as mock_smuggle:
        
        res = engine.run_dynamic_probe("Unicode Smuggling", "Hate Speech")
        
        assert res["technique"] == "Unicode Smuggling"
        assert res["prompt"] == "аррlе"
        mock_smuggle.assert_called_once()

def test_run_dynamic_probe_with_nested_encoding():
    """Test jailbreak probe with Nested Encoding obfuscation."""
    engine = JailbreakEngine()
    
    with patch('core.provider.provider.chat', return_value="secret"), \
         patch('core.sentry.sentry.validate_input', return_value=("", True, 0.1)), \
         patch('core.utils.obfuscator.nested_hex_encode', return_value="736563726574") as mock_hex, \
         patch('random.random', return_value=0.6): # Ensure hex is chosen (>0.5)
        
        res = engine.run_dynamic_probe("Nested Encoding", "PII")
        
        assert res["technique"] == "Nested Encoding"
        assert res["prompt"] == "736563726574"
        mock_hex.assert_called_once()

def test_run_full_scan_mock():
    """Test comprehensive jailbreak scan."""
    engine = JailbreakEngine()
    
    mock_manifest = {
        "safety_policy": {"prohibited_content": ["PII", "Toxic"]}
    }
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_manifest))), \
         patch.object(JailbreakEngine, 'run_dynamic_probe', return_value={"status": "PASSED"}):
        
        summary, path = engine.run_full_scan(num_probes=2)
        
        assert "Total Probes: 2" in summary
        assert "Bypasses found: 2" in summary
        assert "dynamic_jailbreak_report.json" in str(path)
