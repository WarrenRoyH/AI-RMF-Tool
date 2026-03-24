import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from pathlib import Path
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.remediate import run_remediate

class TestRemediate(unittest.TestCase):

    @patch('cli.remediate.check_setup')
    @patch('cli.remediate.WORKSPACE_DIR')
    def test_run_remediate_no_summary(self, mock_workspace_dir, mock_check_setup):
        mock_summary_path = mock_workspace_dir / "reports" / "summary.json"
        mock_summary_path.exists.return_value = False
        with patch('builtins.print') as mock_print:
            run_remediate()
            mock_print.assert_any_call("\n[!] Error: No audit summary found. Run 'measure' first.")

    @patch('cli.remediate.check_setup')
    @patch('cli.remediate.WORKSPACE_DIR')
    @patch('cli.remediate.remediator')
    def test_run_remediate_dry_run(self, mock_remediator, mock_workspace_dir, mock_check_setup):
        mock_summary_path = MagicMock()
        mock_summary_path.exists.return_value = True
        mock_summary_path.__str__.return_value = "summary.json"

        mock_report_path = MagicMock()
        mock_report_path.exists.return_value = True
        mock_report_path.__str__.return_value = "latest_audit_report.md"

        mock_patch_path = MagicMock()
        mock_patch_path.exists.return_value = True
        mock_patch_path.__str__.return_value = "suggested_patch.md"

        # Chaining
        reports_mock = MagicMock()
        mock_workspace_dir.__truediv__.side_effect = lambda x: {
            "reports": reports_mock
        }.get(x, MagicMock())

        reports_mock.__truediv__.side_effect = lambda y: {
            "summary.json": mock_summary_path,
            "latest_audit_report.md": mock_report_path,
            "suggested_patch.md": mock_patch_path
        }.get(y, MagicMock())

        mock_remediator.suggest_patch.return_value = "Patch Suggested"

        with patch('builtins.open', mock_open(read_data='{"timestamp": "2026-03-23"}')):
            run_remediate(is_dry_run=True)
            mock_remediator.suggest_patch.assert_called_once()
            mock_remediator.apply_patch.assert_not_called()
    @patch('cli.remediate.check_setup')
    @patch('cli.remediate.WORKSPACE_DIR')
    @patch('cli.remediate.remediator')
    @patch.dict(os.environ, {"AI_RMF_YOLO": "true"})
    def test_run_remediate_yolo(self, mock_remediator, mock_workspace_dir, mock_check_setup):
        mock_summary_path = mock_workspace_dir / "reports" / "summary.json"
        mock_summary_path.exists.return_value = True
        
        mock_report_path = mock_workspace_dir / "reports" / "latest_audit_report.md"
        mock_report_path.exists.return_value = True
        
        mock_patch_path = mock_workspace_dir / "reports" / "suggested_patch.md"
        mock_patch_path.exists.return_value = True
        
        # Chaining
        reports_mock = MagicMock()
        mock_workspace_dir.__truediv__.side_effect = lambda x: {
            "reports": reports_mock
        }.get(x, MagicMock())
        
        reports_mock.__truediv__.side_effect = lambda y: {
            "summary.json": mock_summary_path,
            "latest_audit_report.md": mock_report_path,
            "suggested_patch.md": mock_patch_path
        }.get(y, MagicMock())

        mock_remediator.suggest_patch.return_value = "Patch Suggested"
        mock_remediator.apply_patch.return_value = "Patch Applied"
        
        with patch('builtins.open', mock_open(read_data='{}')):
            run_remediate(is_dry_run=False)
            mock_remediator.apply_patch.assert_called_once()

if __name__ == '__main__':
    unittest.main()
