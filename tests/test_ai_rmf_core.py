import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_rmf_core import main

class TestAiRmfCore(unittest.TestCase):

    @patch('ai_rmf_core.run_govern')
    def test_main_govern(self, mock_run_govern):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'govern']):
            main()
            mock_run_govern.assert_called_once()

    @patch('ai_rmf_core.run_map')
    def test_main_map(self, mock_run_map):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'map']):
            main()
            mock_run_map.assert_called_once()

    @patch('ai_rmf_core.run_manage')
    def test_main_manage(self, mock_run_manage):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'manage']):
            main()
            mock_run_manage.assert_called_once()

    @patch('ai_rmf_core.start_proxy')
    def test_main_proxy(self, mock_start_proxy):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'proxy']):
            main()
            mock_start_proxy.assert_called_once()

    @patch('ai_rmf_core.run_measure')
    def test_main_measure(self, mock_run_measure):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'measure', '--type', 'audit', '--autopilot']):
            main()
            mock_run_measure.assert_called_once_with(is_autopilot=True, assessment_type='audit')

    @patch('ai_rmf_core.run_remediate')
    def test_main_remediate(self, mock_run_remediate):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'remediate', '--dry-run']):
            main()
            mock_run_remediate.assert_called_once_with(is_dry_run=True)

    @patch('ai_rmf_core.run_red_team')
    def test_main_red_team(self, mock_run_red_team):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'red_teamer']):
            main()
            mock_run_red_team.assert_called_once()

    @patch('ai_rmf_core.run_report')
    def test_main_report(self, mock_run_report):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'report', '--format', 'pdf']):
            main()
            mock_run_report.assert_called_once_with(report_format='pdf')

    @patch('ai_rmf_core.run_dashboard')
    def test_main_dashboard(self, mock_run_dashboard):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'dashboard']):
            main()
            mock_run_dashboard.assert_called_once()

    @patch('ai_rmf_core.run_autopilot')
    def test_main_autopilot(self, mock_run_autopilot):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'autopilot', '--dry-run', '--interval', '60']):
            main()
            mock_run_autopilot.assert_called_once_with(is_dry_run=True, interval=60)

    @patch('ai_rmf_core.run_health')
    def test_main_health(self, mock_run_health):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'health']):
            main()
            mock_run_health.assert_called_once()

    @patch('ai_rmf_core.run_verify')
    def test_main_verify(self, mock_run_verify):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'verify']):
            main()
            mock_run_verify.assert_called_once()

    @patch('ai_rmf_core.auditor.verify_evidence_package')
    @patch('builtins.print')
    def test_main_verify_artifacts(self, mock_print, mock_verify):
        mock_verify.return_value = "Verified"
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'verify-artifacts', '--package', 'test.zip']):
            main()
            mock_verify.assert_called_once_with('test.zip')
            mock_print.assert_called_with("Verified")

    @patch('ai_rmf_core.run_sync')
    def test_main_sync(self, mock_run_sync):
        with patch.object(sys, 'argv', ['ai_rmf_core.py', 'sync']):
            main()
            mock_run_sync.assert_called_once()

if __name__ == '__main__':
    unittest.main()
