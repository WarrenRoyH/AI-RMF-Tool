import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from pathlib import Path
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.manage import run_manage

class TestManage(unittest.TestCase):

    @patch('cli.manage.check_setup')
    def test_run_manage_dry_run(self, mock_check_setup):
        with patch('builtins.print') as mock_print:
            run_manage(is_dry_run=True)
            mock_print.assert_any_call("\n[!] Dry Run complete for Phase 3.")

    @patch('cli.manage.check_setup')
    @patch('cli.manage.MANIFEST_PATH')
    def test_run_manage_no_manifest(self, mock_manifest_path, mock_check_setup):
        mock_manifest_path.exists.return_value = False
        with patch('builtins.print') as mock_print:
            run_manage()
            mock_print.assert_any_call("\n[!] Error: Project Manifest not found. Please run 'govern' first.")

    @patch('cli.manage.check_setup')
    @patch('cli.manage.MANIFEST_PATH')
    @patch('cli.manage.sentry.get_status')
    @patch('cli.manage.provider.chat')
    @patch('cli.manage.sentry.validate_input')
    @patch('cli.manage.WORKSPACE_DIR')
    @patch('builtins.open', new_callable=mock_open, read_data='{"safety_policy": "test"}')
    def test_run_manage_autopilot(self, mock_file, mock_workspace_dir, mock_validate, mock_chat, mock_status, mock_manifest_path, mock_check_setup):
        mock_manifest_path.exists.return_value = True
        mock_status.return_value = {"input_scanners": ["S1"], "output_scanners": ["S2"]}
        mock_chat.return_value = '["high-risk prompt"]'
        mock_validate.return_value = ("sanitized", False, 0.9)
        mock_workspace_dir.__truediv__.return_value = Path("workspace/logs/sentry_violations.jsonl")
        
        run_manage(is_autopilot=True)
        
        mock_validate.assert_called_once_with("high-risk prompt")
        mock_chat.assert_called_once()

    @patch('cli.manage.check_setup')
    @patch('cli.manage.MANIFEST_PATH')
    @patch('cli.manage.sentry.get_status')
    @patch('cli.manage.questionary.select')
    @patch('cli.manage.provider.chat')
    @patch('cli.manage.sentry.validate_input')
    @patch('builtins.open', new_callable=mock_open, read_data='{"safety_policy": "test"}')
    def test_run_manage_stress(self, mock_file, mock_validate, mock_chat, mock_select, mock_status, mock_manifest_path, mock_check_setup):
        mock_manifest_path.exists.return_value = True
        mock_status.return_value = {"input_scanners": ["S1"], "output_scanners": ["S2"]}
        mock_select.return_value.ask.side_effect = ["stress", "exit"]
        mock_chat.return_value = '["stress test prompt"]'
        mock_validate.return_value = ("sanitized", True, 0.0)
        
        run_manage()
        
        mock_chat.assert_called_once()
        mock_validate.assert_called_once_with("stress test prompt")

    @patch('cli.manage.check_setup')
    @patch('cli.manage.MANIFEST_PATH')
    @patch('cli.manage.sentry.get_status')
    @patch('cli.manage.questionary.select')
    @patch('cli.manage.questionary.text')
    @patch('cli.manage.provider.chat')
    @patch('cli.manage.sentry.validate_input')
    @patch('cli.manage.sentry.validate_output')
    def test_run_manage_interactive(self, mock_validate_out, mock_validate_in, mock_chat, mock_text, mock_select, mock_status, mock_manifest_path, mock_check_setup):
        mock_manifest_path.exists.return_value = True
        mock_status.return_value = {"input_scanners": ["S1"], "output_scanners": ["S2"]}
        mock_select.return_value.ask.side_effect = ["interactive", "exit"]
        mock_text.return_value.ask.side_effect = ["Hello", "exit"]
        mock_validate_in.return_value = ("Hello", True, 0.0)
        mock_chat.return_value = "Hi"
        mock_validate_out.return_value = ("Hi", True, 0.0)
        
        run_manage()
        
        mock_validate_in.assert_called_once_with("Hello")
        mock_chat.assert_called_once()

if __name__ == '__main__':
    unittest.main()
