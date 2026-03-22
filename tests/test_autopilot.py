import pytest
from unittest.mock import patch, MagicMock
from cli.autopilot import run_autopilot
from pathlib import Path

@patch("cli.autopilot.MANIFEST_PATH")
@patch("cli.autopilot.run_govern")
@patch("cli.autopilot.run_map")
@patch("cli.autopilot.run_manage")
@patch("cli.autopilot.run_measure")
@patch("cli.autopilot.time.sleep")
@patch("questionary.confirm")
def test_autopilot_single_run(mock_confirm, mock_sleep, mock_measure, mock_manage, mock_map, mock_govern, mock_manifest):
    """Verify autopilot runs exactly once when interval is 0."""
    mock_manifest.exists.return_value = True
    
    # Run once
    run_autopilot(is_dry_run=True, interval=0)
    
    # Verify each phase was called
    # run_govern should not be called in dry-run if manifest exists
    mock_govern.assert_not_called()
    mock_map.assert_called_once()
    mock_manage.assert_called_once()
    mock_measure.assert_called_once()
    mock_sleep.assert_not_called()

@patch("cli.autopilot.MANIFEST_PATH")
@patch("cli.autopilot.run_govern")
@patch("cli.autopilot.run_map")
@patch("cli.autopilot.run_manage")
@patch("cli.autopilot.run_measure")
@patch("cli.autopilot.time.sleep")
def test_autopilot_loop(mock_sleep, mock_measure, mock_manage, mock_map, mock_govern, mock_manifest):
    """Verify autopilot loops when interval is > 0."""
    mock_manifest.exists.return_value = True
    
    # We'll make it loop twice and then raise KeyboardInterrupt to break the while True
    # Side effects for time.sleep to control the loop
    mock_sleep.side_effect = [None, KeyboardInterrupt]
    
    run_autopilot(is_dry_run=True, interval=1)
    
    # Should have run twice before interruption
    assert mock_map.call_count == 2
    assert mock_manage.call_count == 2
    assert mock_measure.call_count == 2
    assert mock_sleep.call_count == 2
