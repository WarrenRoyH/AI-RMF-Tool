import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from pathlib import Path
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.verify import run_verify

class TestVerify(unittest.TestCase):

    @patch('cli.verify.check_setup')
    @patch('cli.verify.WORKSPACE_DIR')
    def test_run_verify_no_manifest(self, mock_workspace_dir, mock_check_setup):
        mock_manifest_path = mock_workspace_dir / "project-manifest.json"
        mock_manifest_path.exists.return_value = False
        with patch('builtins.print') as mock_print:
            run_verify()
            mock_print.assert_any_call("[!] Error: Manifest missing.")

    @patch('cli.verify.check_setup')
    @patch('cli.verify.WORKSPACE_DIR')
    @patch('cli.verify.provider.chat')
    @patch('cli.verify.sentry.validate_input')
    @patch('cli.verify.sentry.validate_output')
    def test_run_verify_with_failures(self, mock_validate_output, mock_validate_input, mock_chat, mock_workspace_dir, mock_check_setup):
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = True
        mock_manifest_path.__str__.return_value = "project-manifest.json"

        mock_summary_path = MagicMock()
        mock_summary_path.exists.return_value = True
        mock_summary_path.__str__.return_value = "summary.json"

        mock_pf_results_path = MagicMock()
        mock_pf_results_path.exists.return_value = True
        mock_pf_results_path.__str__.return_value = "promptfoo_results.json"

        # Setup chaining: WORKSPACE_DIR / "project-manifest.json"
        reports_mock = MagicMock()
        mock_workspace_dir.__truediv__.side_effect = lambda x: {
            "project-manifest.json": mock_manifest_path,
            "reports": reports_mock
        }.get(x, MagicMock())
        
        reports_mock.__truediv__.side_effect = lambda y: {
            "summary.json": mock_summary_path,
            "promptfoo_results.json": mock_pf_results_path,
            "garak": MagicMock()
        }.get(y, MagicMock())

        mock_garak_report_dir = mock_workspace_dir / "reports" / "garak"
        mock_garak_report_dir.exists.return_value = False
        
        mock_manifest = {"safety_policy": {"hardened_prompt": "Hardened"}}
        mock_pf_results = {"results": [{"success": False, "vars": {"query": "bad prompt"}, "assert": [{"value": "refuse"}]}]}
        
        def open_side_effect(path, mode='r', *args, **kwargs):
            p = str(path)
            if "project-manifest.json" in p:
                return mock_open(read_data=json.dumps(mock_manifest)).return_value
            if "promptfoo_results.json" in p:
                return mock_open(read_data=json.dumps(mock_pf_results)).return_value
            if "summary.json" in p:
                return mock_open(read_data='{}').return_value
            return mock_open().return_value

        mock_validate_input.return_value = ("sanitized", True, 0.1)
        mock_chat.side_effect = ["Model Response", "SUCCESS"] # Model chat, then Eval chat
        mock_validate_output.return_value = ("safe", True, 0.1)
        
        with patch('builtins.open', side_effect=open_side_effect), \
             patch('pathlib.Path.glob', return_value=[]):
            run_verify()
            
            # Verify passed count
            mock_chat.assert_called()
            # Check if verification.json was written
            pass

    @patch('cli.verify.check_setup')
    @patch('cli.verify.WORKSPACE_DIR')
    @patch('cli.verify.provider.chat')
    @patch('cli.verify.sentry.validate_input')
    @patch('cli.verify.sentry.validate_output')
    def test_run_verify_garak(self, mock_validate_output, mock_validate_input, mock_chat, mock_workspace_dir, mock_check_setup):
        mock_manifest_path = MagicMock()
        mock_manifest_path.exists.return_value = True
        mock_manifest_path.__str__.return_value = "project-manifest.json"
        
        mock_reports_dir = MagicMock()
        mock_reports_dir.exists.return_value = True
        
        mock_garak_dir = MagicMock()
        mock_garak_dir.exists.return_value = True
        
        mock_workspace_dir.__truediv__.side_effect = lambda x: {
            "project-manifest.json": mock_manifest_path,
            "reports": mock_reports_dir
        }.get(x, MagicMock())
        
        mock_reports_dir.__truediv__.side_effect = lambda y: {
            "garak": mock_garak_dir,
            "summary.json": MagicMock(exists=lambda: False),
            "promptfoo_results.json": MagicMock(exists=lambda: False)
        }.get(y, MagicMock())
        
        mock_hitlog = MagicMock()
        mock_hitlog.__str__.return_value = "test.hitlog.jsonl"
        mock_garak_dir.glob.return_value = [mock_hitlog]
        
        mock_manifest = {"safety_policy": {}}
        mock_garak_line = json.dumps({"prompt": "garak prompt", "probe": "test_probe"})
        
        def open_side_effect(path, mode='r', *args, **kwargs):
            if "project-manifest.json" in str(path):
                return mock_open(read_data=json.dumps(mock_manifest)).return_value
            if "hitlog.jsonl" in str(path):
                return mock_open(read_data=mock_garak_line).return_value
            return mock_open().return_value

        mock_validate_input.return_value = ("sanitized", True, 0.1)
        mock_chat.side_effect = ["Model Response", "SUCCESS"]
        mock_validate_output.return_value = ("safe", True, 0.1)
        
        with patch('builtins.open', side_effect=open_side_effect):
            run_verify()
            mock_chat.assert_called()

if __name__ == '__main__':
    unittest.main()
