import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from cli.setup import run_setup

@patch("cli.setup.questionary.confirm")
@patch("cli.setup.questionary.text")
@patch("cli.setup.provider.chat")
@patch("cli.setup.provider.validate_setup")
@patch("cli.setup.MANIFEST_PATH")
@patch("cli.setup.SETUP_PROMPT_PATH")
@patch("cli.setup.discovery.get_discovery_report")
@patch("cli.setup.discovery.suggest_manifest_fragment")
def test_run_setup_full_flow(mock_suggest, mock_discovery, mock_prompt_path, mock_manifest_path, mock_validate, mock_chat, mock_text, mock_confirm):
    # Setup mocks
    mock_validate.return_value = True
    mock_manifest_path.exists.return_value = False
    mock_prompt_path.exists.return_value = True
    mock_discovery.return_value = {"test": "data"}
    mock_suggest.return_value = {"fragment": "data"}
    
    # Mock questionary sequence
    mock_text.return_value.ask.side_effect = ["My Project", "exit"]
    mock_chat.return_value = "Librarian response with ```json\n{\"project_name\": \"My Project\"}\n```"
    mock_confirm.return_value.ask.return_value = True
    
    with patch("builtins.open", mock_open(read_data="system prompt content")):
        run_setup()
        
    # Verify manifest was saved
    mock_confirm.return_value.ask.assert_called()

@patch("cli.setup.questionary.confirm")
@patch("cli.setup.provider.validate_setup")
def test_run_setup_cancel_on_overwrite(mock_validate, mock_confirm, MANIFEST_PATH_MOCK):
    mock_validate.return_value = True
    with patch("cli.setup.MANIFEST_PATH", MANIFEST_PATH_MOCK):
        MANIFEST_PATH_MOCK.exists.return_value = True
        mock_confirm.return_value.ask.return_value = False
        
        run_setup()
        mock_confirm.assert_called_with("\n[!] Existing Project Manifest found. Overwrite it?")
        mock_confirm.return_value.ask.assert_called()

@pytest.fixture
def MANIFEST_PATH_MOCK():
    return MagicMock()
