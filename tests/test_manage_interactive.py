import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from cli.manage import run_manage

@patch("cli.manage.questionary.select")
@patch("cli.manage.questionary.text")
@patch("cli.manage.provider.chat")
@patch("cli.manage.provider.validate_setup")
@patch("cli.manage.MANIFEST_PATH")
@patch("cli.manage.sentry")
@patch("cli.manage.WORKSPACE_DIR")
def test_run_manage_interactive_flow(mock_workspace, mock_sentry, mock_manifest_path, mock_validate, mock_chat, mock_text, mock_select):
    # Setup mocks
    mock_validate.return_value = True
    mock_manifest_path.exists.return_value = True
    mock_sentry.get_status.return_value = {"input_scanners": ["Toxicity"], "output_scanners": ["PII"]}
    
    # Mock questionary sequence
    # 1. Main Action: interactive
    # 2. Prompt: "Hello"
    # 3. Advisory Kill-Switch (if violation detected)
    # 4. Prompt: "exit"
    # 5. Main Action: exit
    mock_select.return_value.ask.side_effect = ["interactive", "kill", "exit"]
    mock_text.return_value.ask.side_effect = ["unsafe prompt", "exit"]
    
    # Mock sentry violation
    mock_sentry.validate_input.side_effect = [
        ("unsafe", False, 0.9), # First call
    ]
    
    run_manage()
    
    assert mock_sentry.validate_input.called
    assert mock_select.called

@patch("cli.manage.questionary.select")
@patch("cli.manage.provider.validate_setup")
@patch("cli.manage.MANIFEST_PATH")
def test_run_manage_exit(mock_manifest_path, mock_validate, mock_select):
    mock_validate.return_value = True
    mock_manifest_path.exists.return_value = True
    mock_select.return_value.ask.return_value = "exit"
    
    run_manage()
    assert mock_select.called

@patch("cli.manage.questionary.select")
@patch("cli.manage.provider.validate_setup")
@patch("cli.manage.MANIFEST_PATH")
def test_run_manage_measure_jump(mock_manifest_path, mock_validate, mock_select):
    mock_validate.return_value = True
    mock_manifest_path.exists.return_value = True
    mock_select.return_value.ask.return_value = "measure"
    
    with patch("cli.measure.run_measure") as mock_run_measure:
        run_manage()
        assert mock_run_measure.called
