import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.jailbreak_engine import JailbreakEngine

def test_run_dynamic_probe_mock():
    """Test dynamic jailbreak probe generation and Sentry check."""
    engine = JailbreakEngine()
    
    with patch('core.provider.provider.chat', return_value="JAILBREAK PROMPT"), \
         patch('core.sentry.sentry.validate_input', return_value=("", False, 0.9)):
        
        res = engine.run_dynamic_probe("Cognitive Overload", "Hate Speech")
        
        assert res["technique"] == "Cognitive Overload"
        assert res["status"] == "BLOCKED"
        assert res["risk_score"] == 0.9
        assert res["prompt"] == "JAILBREAK PROMPT"

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
