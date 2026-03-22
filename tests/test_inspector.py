import pytest
from unittest.mock import patch, MagicMock
from core.inspector import Inspector
from pathlib import Path
import sys

@pytest.fixture
def inspector():
    return Inspector(workspace_dir="test_workspace")

@patch("subprocess.Popen")
@patch("time.sleep")
@patch("requests.get")
def test_start_observability_server_new(mock_get, mock_sleep, mock_popen, inspector):
    """Verify server starts if not already running."""
    # First get fails (server offline)
    mock_get.side_effect = Exception("Offline")
    
    res = inspector.start_observability_server()
    
    assert "Unified Observability server started" in res
    mock_popen.assert_called_once()
    assert mock_sleep.call_count == 1

@patch("requests.get")
def test_start_observability_server_existing(mock_get, inspector):
    """Verify server reuse if already running."""
    # Get succeeds (server online)
    mock_get.return_value = MagicMock()
    
    res = inspector.start_observability_server()
    
    assert "already active" in res

def test_get_monitoring_status(inspector):
    """Verify status report generation."""
    with patch("pathlib.Path.exists") as mock_exists, \
         patch("pathlib.Path.stat") as mock_stat, \
         patch("requests.get") as mock_get:
        
        # Mocking existence of various logs
        # 1. Phoenix Online
        # 2. Sentry Violation Logs Exist
        # 3. Garak dir exists
        # 4. Promptfoo config exists
        mock_get.return_value = MagicMock()
        mock_exists.side_effect = [True, True, True] # Sentry, Garak, Promptfoo
        mock_stat.return_value.st_size = 1024 # 1KB
        
        # We also need to mock glob for Garak
        with patch("pathlib.Path.glob") as mock_glob:
            mock_glob.return_value = [Path("rep1.jsonl"), Path("rep2.jsonl")]
            
            status = inspector.get_monitoring_status()
            
            assert "Phoenix Dashboard: [ONLINE]" in status
            assert "Sentry Violation Logs: [ACTIVE]" in status
            assert "Garak Vulnerability Scans: [FOUND] (2 reports)" in status
            assert "Accuracy Benchmarks: [CONFIGURED]" in status
