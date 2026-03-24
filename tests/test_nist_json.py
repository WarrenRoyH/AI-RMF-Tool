import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.auditor import Auditor

def test_generate_nist_json_direct():
    """Test the formal NIST JSON artifact generation."""
    auditor = Auditor()
    
    mock_manifest = {"project_name": "Test Project"}
    mock_cat_data = {
        "GV-1": ("✅ MET", "Summary of GV-1"),
        "MP-1": ("⚠️ FAIL", "Summary of MP-1")
    }
    
    with patch('builtins.open', mock_open()), \
         patch('pathlib.Path.write_text'):
        path = auditor.generate_nist_json(mock_manifest, mock_cat_data, 50.0)
        assert "nist_rmf_audit.json" in str(path)
        
        # Verify call arguments if possible, or just trust the logic
        # We can also check the structure by capturing the json.dump call
        with patch('json.dump') as mock_dump:
            auditor.generate_nist_json(mock_manifest, mock_cat_data, 50.0)
            args, _ = mock_dump.call_args
            report = args[0]
            assert report["project"] == "Test Project"
            assert report["overall_compliance_score"] == "50.0%"
            
            # Check for specific functions
            func_names = [f["name"] for f in report["functions"]]
            assert "GOVERN" in func_names
            assert "MAP" in func_names
            
            # Check for specific category status
            govern_func = next(f for f in report["functions"] if f["name"] == "GOVERN")
            gv1 = next(c for c in govern_func["categories"] if c["id"] == "GV-1")
            assert gv1["status"] == "MET"
            assert gv1["summary"] == "Summary of GV-1"
            
            map_func = next(f for f in report["functions"] if f["name"] == "MAP")
            mp1 = next(c for c in map_func["categories"] if c["id"] == "MP-1")
            assert mp1["status"] == "FAIL"
