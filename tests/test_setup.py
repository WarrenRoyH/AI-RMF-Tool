import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from pathlib import Path
from cli.setup import run_setup

class TestSetup(unittest.TestCase):
    @patch('cli.setup.check_setup')
    @patch('cli.setup.MANIFEST_PATH')
    @patch('cli.setup.questionary.confirm')
    @patch('cli.setup.questionary.text')
    @patch('cli.setup.provider.chat')
    @patch('cli.setup.open', new_callable=mock_open, read_data="# System Prompt")
    def test_run_setup_success(self, mock_file, mock_chat, mock_text, mock_confirm, mock_manifest_path, mock_check):
        # Setup mocks
        mock_manifest_path.exists.return_value = False
        
        # Mock questionary.text().ask()
        mock_text_ask = MagicMock()
        mock_text_ask.ask.side_effect = ["My cool AI project", "exit"]
        mock_text.return_value = mock_text_ask
        
        # Mock questionary.confirm().ask()
        mock_confirm_ask = MagicMock()
        mock_confirm_ask.ask.return_value = True
        mock_confirm.return_value = mock_confirm_ask
        
        mock_chat.return_value = "I've drafted a manifest: ```json\n{\"project_name\": \"cool-ai\"}\n```"
        
        # Run setup
        run_setup()
        
        # Verify
        mock_check.assert_called_once()
        mock_chat.assert_called()
        
        # Verify JSON was saved
        # Filter for 'w' mode calls
        write_calls = [call for call in mock_file.call_args_list if call.args[1] == 'w']
        self.assertTrue(len(write_calls) > 0)
        
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn("cool-ai", written_content)

if __name__ == '__main__':
    unittest.main()
