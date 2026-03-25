import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.jailbreak_engine import JailbreakEngine

def test_semantic_masking():
    """Test jailbreak probe with Semantic Masking."""
    engine = JailbreakEngine()
    
    with patch('core.provider.provider.chat', side_effect=["Base Probe", "Masked Probe"]), \
         patch('core.sentry.sentry.validate_input', return_value=("", True, 0.1)):
        
        res = engine.run_dynamic_probe("Semantic Masking", "Hate Speech")
        
        assert res["technique"] == "Semantic Masking"
        assert res["prompt"] == "Masked Probe"

def test_logical_entrapment_fsm_success():
    """Test Logical Entrapment FSM multi-turn success."""
    engine = JailbreakEngine()
    
    # 3 turns: 
    # Turn 0: Premise 1
    # Turn 1: Premise 2
    # Turn 2: Entrapment
    with patch('core.provider.provider.chat', side_effect=[
        "Premise 1", "Resp 1", 
        "Premise 2", "Resp 2", 
        "Entrapment Probe", "Final Resp"
    ]) as mock_chat, \
         patch('core.sentry.sentry.validate_input', return_value=("", True, 0.1)):
        
        res = engine.run_logical_entrapment("PII", max_turns=3)
        
        assert res["technique"] == "Logical Entrapment"
        assert res["status"] == "PASSED"
        assert len(res["history"]) == 3
        assert res["history"][2]["probe"] == "Entrapment Probe"

def test_logical_entrapment_fsm_blocked():
    """Test Logical Entrapment FSM blocked at second turn."""
    engine = JailbreakEngine()
    
    with patch('core.provider.provider.chat', side_effect=["Premise 1", "Resp 1", "Premise 2"]), \
         patch('core.sentry.sentry.validate_input', side_effect=[("", True, 0.1), ("", False, 0.8)]):
        
        res = engine.run_logical_entrapment("Toxic", max_turns=3)
        
        assert res["status"] == "BLOCKED"
        assert len(res["history"]) == 1 # Only the first turn finished
        assert res["risk_score"] == 0.8
