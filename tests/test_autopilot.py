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

@patch("cli.autopilot.MANIFEST_PATH")
@patch("cli.autopilot.run_govern")
@patch("cli.autopilot.run_map")
@patch("cli.autopilot.run_manage")
@patch("cli.autopilot.run_measure")
@patch("cli.autopilot.run_remediate")
@patch("cli.autopilot.run_verify")
@patch("cli.autopilot.check_setup")
@patch("questionary.confirm")
def test_autopilot_remediation_loop(mock_confirm, mock_check_setup, mock_verify, mock_remediate, mock_measure, mock_manage, mock_map, mock_govern, mock_manifest):
    """Verify autopilot triggers remediation if metrics are low."""
    mock_manifest.exists.return_value = True
    mock_confirm.return_value.ask.return_value = False # Don't rerun govern
    
    # Mock summary.json with low accuracy
    mock_summary = {
        "metrics": {
            "garak_hits": 5,
            "accuracy": "85.0%"
        }
    }
    
    with patch("builtins.open", MagicMock(side_effect=[MagicMock(), MagicMock()])) as mock_file, \
         patch("pathlib.Path.exists", side_effect=[True, True, True, True]): # Manifest, Summary
        # First call is to open manifest in run_map or somewhere? 
        # No, autopilot opens summary.json
        
        # We need to mock open specifically for summary.json
        import json
        from unittest.mock import mock_open as unittest_mock_open
        def open_side_effect(path, mode='r', *args, **kwargs):
            if "summary.json" in str(path):
                m = unittest_mock_open(read_data=json.dumps(mock_summary)).return_value
                return m
            return unittest_mock_open().return_value

        with patch("builtins.open", side_effect=open_side_effect):
            run_autopilot(is_dry_run=False, interval=0)
            
            mock_remediate.assert_called_once()
            mock_verify.assert_called_once()

@patch("cli.autopilot.MANIFEST_PATH")
@patch("cli.autopilot.run_govern")
@patch("cli.autopilot.check_setup")
def test_autopilot_missing_manifest_aborts(mock_check_setup, mock_govern, mock_manifest):
    """Verify autopilot aborts if govern fails to create manifest."""
    mock_manifest.exists.side_effect = [False, False] # Before and after govern
    
    run_autopilot(is_dry_run=False, interval=0)
    
    mock_govern.assert_called_once()
