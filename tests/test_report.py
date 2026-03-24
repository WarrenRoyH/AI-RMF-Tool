import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.report import run_report

class TestReport(unittest.TestCase):

    @patch('cli.report.check_setup')
    @patch('cli.report.auditor')
    def test_run_report_html(self, mock_auditor, mock_check_setup):
        mock_auditor.export_report.return_value = "Exported HTML"
        run_report(report_format="html")
        mock_auditor.export_report.assert_called_once_with(format="html")

    @patch('cli.report.check_setup')
    @patch('cli.report.auditor')
    def test_run_report_pdf(self, mock_auditor, mock_check_setup):
        mock_auditor.export_report.return_value = "Exported PDF"
        run_report(report_format="pdf")
        mock_auditor.export_report.assert_called_once_with(format="pdf")

    @patch('cli.report.check_setup')
    @patch('cli.report.auditor')
    def test_run_report_bundle(self, mock_auditor, mock_check_setup):
        mock_auditor.bundle_evidence_package.return_value = "Bundled"
        run_report(report_format="BUNDLE")
        mock_auditor.bundle_evidence_package.assert_called_once()

    @patch('cli.report.check_setup')
    @patch('cli.report.auditor')
    @patch('cli.report.questionary.select')
    def test_run_report_manual(self, mock_select, mock_auditor, mock_check_setup):
        mock_select.return_value.ask.return_value = "HTML: ..."
        mock_auditor.export_report.return_value = "Exported"
        run_report()
        mock_select.assert_called_once()
        mock_auditor.export_report.assert_called_with(format="html")

if __name__ == '__main__':
    unittest.main()
