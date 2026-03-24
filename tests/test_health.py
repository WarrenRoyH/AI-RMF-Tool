import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.health import run_health

class TestHealth(unittest.TestCase):

    @patch('cli.health.WORKSPACE_DIR')
    @patch('subprocess.run')
    @patch('cli.health.provider')
    def test_run_health_ok(self, mock_provider, mock_run, mock_workspace_dir):
        mock_workspace_dir.exists.return_value = True
        
        # Mock subprocess.run for various tools
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "/usr/bin/tool"
        mock_run.return_value = mock_res
        
        mock_provider.model = "test-model"
        mock_provider.chat.return_value = "Pong"
        
        with patch('builtins.print') as mock_print:
            run_health()
            mock_print.assert_any_call("--> Workspace: [OK]")
            mock_print.assert_any_call("--> API Configuration: [OK]")

    @patch('cli.health.WORKSPACE_DIR')
    @patch('subprocess.run')
    @patch('cli.health.provider')
    def test_run_health_missing(self, mock_provider, mock_run, mock_workspace_dir):
        mock_workspace_dir.exists.return_value = False
        
        # Mock subprocess.run for various tools to fail
        mock_res = MagicMock()
        mock_res.returncode = 1
        mock_res.stdout = ""
        mock_run.return_value = mock_res
        
        mock_provider.validate_setup.side_effect = ValueError("Missing Key")
        mock_provider.chat.return_value = "API Error: 401"
        
        with patch('builtins.print') as mock_print:
            run_health()
            mock_print.assert_any_call("--> Workspace: [MISSING]")
            mock_print.assert_any_call("--> API Configuration: [FAILED] - Missing Key")

if __name__ == '__main__':
    unittest.main()
