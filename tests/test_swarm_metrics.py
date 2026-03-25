import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.swarm import Swarm, Persona

def test_persona_loading_with_metrics():
    """Test Persona loading with NIST metrics weights."""
    mock_json = {
        "name": "Privacy Officer",
        "nist_metrics_weights": {"Privacy": 0.8, "Data": 0.2},
        "system_prompt_path": "p.md"
    }
    
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_json))), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value="Prompt"):
        
        persona = Persona(Path("p.json"))
        assert persona.nist_metrics_weights["Privacy"] == 0.8

def test_swarm_weighted_scoring():
    """Test explicit weighted scoring engine with NIST characteristics."""
    swarm = Swarm()
    persona = MagicMock(spec=Persona)
    # Use formal NIST name
    persona.nist_metrics_weights = {"Privacy-Enhanced": 0.8, "Ethics": 0.2}
    
    report_text = """
    Assessment Summary:
    - Privacy-Enhanced Score: 90/100
    - Ethics Score: 50/100
    """
    
    res = swarm.calculate_weighted_score(persona, report_text)
    
    # 90 * 0.8 = 72
    # 50 * 0.2 = 10
    # Final = 82
    assert res["final_score"] == 82.0
    assert "Privacy-Enhanced: 90.0 * 0.8 = 72.0" in res["audit_trail"]

def test_swarm_fuzzy_mapping():
    """Test substring/fuzzy mapping for NIST categories."""
    swarm = Swarm()
    persona = MagicMock(spec=Persona)
    persona.nist_metrics_weights = {"Fair \u2013 with Harmful Bias Managed": 1.0}
    
    # LLM might just output 'Fairness' or 'Bias Managed'
    report_text = "Bias Managed Score: 80/100"
    
    res = swarm.calculate_weighted_score(persona, report_text)
    assert res["final_score"] == 80.0
    assert "matched with 'Bias Managed'" in res["audit_trail"][0]

def test_swarm_extract_scores_various_formats():
    """Test regex extraction of scores."""
    swarm = Swarm()
    text = "- Data Protection Score: 85/100\n* Fairness Score: 70/100"
    scores = swarm._extract_scores(text)
    
    assert scores["Data Protection"] == 85.0
    assert scores["Fairness"] == 70.0
