import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.swarm import Swarm
from core.auditor import Auditor

def test_swarm_run_consensus_mock():
    """Test swarm consensus logic with mocked provider."""
    swarm = Swarm()
    
    # Mock provider.chat to return different values based on call count
    # First 3 calls: Individual reports
    # 4th call: Consensus report
    mock_responses = [
        "Policy Expert: All good.",
        "Compliance Officer: Metrics look solid.",
        "Red Teamer: No vulnerabilities found.",
        "# Consensus Report\nScore: 95\nStatus: Approved"
    ]
    
    with patch('core.provider.provider.chat', side_effect=mock_responses), \
         patch('pathlib.Path.mkdir'), \
         patch('builtins.open', mock_open()):
        
        manifest = {"project_name": "Test"}
        results = {"sast": []}
        logs = []
        
        consensus, individuals = swarm.run_consensus(manifest, results, logs)
        
        assert "Policy Expert" in individuals
        assert "Compliance Officer" in individuals
        assert "Red Teamer" in individuals
        assert "Score: 95" in consensus
        assert "Approved" in consensus

def test_auditor_run_swarm_audit_mock():
    """Test Auditor integration with Swarm."""
    auditor = Auditor()
    
    mock_manifest = {
        "project_name": "Test Project"
    }
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_manifest))), \
         patch('core.swarm.swarm.run_consensus', return_value=("# Consensus", {})), \
         patch.object(Auditor, 'run_sast_scan', return_value=[]), \
         patch.object(Auditor, 'run_infra_audit', return_value=[]), \
         patch.object(Auditor, 'run_supply_chain_scan', return_value=("✅", [])), \
         patch('pathlib.Path.write_text'):
        
        res = auditor.run_swarm_audit()
        assert "Swarm Consensus Report generated" in res
