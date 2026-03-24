import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.measure import run_measure

class TestMeasure(unittest.TestCase):

    @patch('cli.measure.check_setup')
    def test_run_measure_dry_run(self, mock_check_setup):
        with patch('builtins.print') as mock_print:
            run_measure(is_dry_run=True)
            mock_print.assert_any_call("\n[!] Dry Run complete for Phase 4.")

    @patch('cli.measure.check_setup')
    @patch('cli.measure.auditor')
    @patch('cli.measure.os.system')
    def test_run_measure_autopilot(self, mock_os_system, mock_auditor, mock_check_setup):
        mock_auditor.generate_promptfoo_config.return_value = "promptfoo --test"
        mock_auditor.export_report.return_value = "Report Exported"
        
        run_measure(is_autopilot=True)
        
        mock_auditor.run_adversarial_sim.assert_called_once()
        mock_os_system.assert_called_with("promptfoo --test")
        mock_auditor.run_compliance_audit.assert_called_once()
        mock_auditor.generate_nutrition_label.assert_called_once()

    @patch('cli.measure.check_setup')
    @patch('cli.measure.auditor')
    def test_run_measure_cli_trigger_audit(self, mock_auditor, mock_check_setup):
        run_measure(assessment_type="audit")
        mock_auditor.run_compliance_audit.assert_called_once()

    @patch('cli.measure.check_setup')
    @patch('cli.measure.auditor')
    @patch('cli.measure.os.system')
    def test_run_measure_cli_trigger_promptfoo(self, mock_os_system, mock_auditor, mock_check_setup):
        mock_auditor.generate_promptfoo_config.return_value = "pf --run"
        run_measure(assessment_type="promptfoo")
        mock_os_system.assert_called_with("pf --run")

    @patch('cli.measure.check_setup')
    @patch('cli.measure.auditor')
    @patch('cli.measure.questionary.select')
    def test_run_measure_manual_exit(self, mock_select, mock_auditor, mock_check_setup):
        mock_select.return_value.ask.return_value = "exit"
        run_measure()
        mock_select.assert_called_once()

if __name__ == '__main__':
    unittest.main()
