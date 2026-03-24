import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from pathlib import Path
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.red_team import run_red_team

class TestRedTeamCli(unittest.TestCase):

    @patch('cli.red_team.check_setup')
    @patch('cli.red_team.MANIFEST_PATH')
    @patch('cli.red_team.red_teamer')
    def test_run_red_team_from_manifest(self, mock_red_teamer, mock_manifest_path, mock_check_setup):
        mock_manifest_path.exists.return_value = True
        mock_manifest_content = json.dumps({"ai_bom": {"target_url": "http://test.ai"}})
        
        with patch('builtins.open', mock_open(read_data=mock_manifest_content)):
            run_red_team()
            mock_red_teamer.run_stress_test.assert_called_once_with(target_url="http://test.ai")

    @patch('cli.red_team.check_setup')
    @patch('cli.red_team.MANIFEST_PATH')
    @patch('cli.red_team.red_teamer')
    @patch('questionary.text')
    def test_run_red_team_interactive(self, mock_text, mock_red_teamer, mock_manifest_path, mock_check_setup):
        mock_manifest_path.exists.return_value = False
        mock_text.return_value.ask.return_value = "http://manual.ai"
        
        with patch.dict(os.environ, {}, clear=True):
            if "AI_RMF_TARGET_URL" in os.environ: del os.environ["AI_RMF_TARGET_URL"]
            run_red_team()
            mock_red_teamer.run_stress_test.assert_called_once_with(target_url="http://manual.ai")

if __name__ == '__main__':
    unittest.main()
