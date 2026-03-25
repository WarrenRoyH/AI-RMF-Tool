import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.swarm import Swarm, Persona, PersonaLoader

def test_persona_initialization():
    """Test Persona class loading from JSON and MD."""
    mock_json = {
        "name": "Test Persona",
        "role": "auditor",
        "nist_focus": ["GOVERN"],
        "allowed_namespaces": ["HOST"],
        "system_prompt_path": "test_prompt.md"
    }
    
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_json))), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value="System Prompt Content"):
        
        persona = Persona(Path("test.json"))
        assert persona.name == "Test Persona"
        assert persona.system_prompt == "System Prompt Content"
        assert "HOST" in persona.allowed_namespaces

def test_persona_loader():
    """Test dynamic persona loading."""
    with patch('pathlib.Path.glob', return_value=[Path("p1.json"), Path("p2.json")]), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('core.swarm.Persona', side_effect=[MagicMock(name="P1"), MagicMock(name="P2")]):
        
        loader = PersonaLoader(personas_dir="/tmp/personas")
        personas = loader.load_all()
        assert len(personas) == 2

def test_swarm_iam_scoping():
    """Test that IAM scoping redacts context for restricted personas."""
    swarm = Swarm()
    persona = MagicMock(spec=Persona)
    persona.allowed_namespaces = ["TARGET"] # No HOST access
    persona.name = "Red Teamer"
    persona.role = "adversary"
    
    context = {
        "manifest": {
            "project_name": "SecureApp",
            "infrastructure": {"internal_keys": "SECRET"}
        }
    }
    
    filtered = swarm._enforce_iam_scoping(persona, context)
    assert filtered["manifest"]["infrastructure"] == "[REDACTED - ADVERSARY ROLE INSUFFICIENT]"
    assert filtered["manifest"]["project_name"] == "SecureApp"

def test_swarm_run_consensus_with_iam():
    """Test run_consensus logic with mocked provider and IAM check."""
    # Ensure personas are loaded for the test
    with patch('core.swarm.PersonaLoader.load_all') as mock_load:
        p1 = MagicMock(spec=Persona)
        p1.name = "P1"
        p1.role = "auditor"
        p1.nist_focus = ["GOVERN"]
        p1.scoring_weight = 0.2
        p1.nist_metrics_weights = {"Govern": 1.0}
        p1.allowed_namespaces = ["HOST", "TARGET"]
        p1.system_prompt = "P1 Prompt"
        
        p2 = MagicMock(spec=Persona)
        p2.name = "P2"
        p2.role = "adversary"
        p2.nist_focus = ["MAP"]
        p2.scoring_weight = 0.1
        p2.nist_metrics_weights = {"Map": 1.0}
        p2.allowed_namespaces = ["TARGET"]
        p2.system_prompt = "P2 Prompt"
        
        mock_load.return_value = [p1, p2]
        swarm = Swarm()
        
        # 1. P1 (HOST+TARGET) -> use_test_model=True, use_target=False
        # 2. P2 (TARGET only) -> use_test_model=False, use_target=True
        # 3. Consensus -> use_test_model=False, use_target=False
        
        with patch('core.provider.provider.chat', side_effect=["R1", "R2", "# Consensus"]) as mock_chat:
            manifest = {"project_name": "Test"}
            res, individuals = swarm.run_consensus(manifest, {}, [])
            
            assert individuals["P1"] == "R1"
            assert individuals["P2"] == "R2"
            assert "# Consensus" in res
            
            # Verify call arguments for IAM enforcement
            # Call 1: use_test_model=True, use_target=False
            args1, kwargs1 = mock_chat.call_args_list[0]
            assert kwargs1["use_test_model"] is True
            assert kwargs1["use_target"] is False
            
            # Call 2: use_test_model=False, use_target=True (P2 restricted)
            args2, kwargs2 = mock_chat.call_args_list[1]
            assert kwargs2["use_test_model"] is False
            assert kwargs2["use_target"] is True
