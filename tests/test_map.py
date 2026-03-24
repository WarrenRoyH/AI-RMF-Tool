import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from pathlib import Path
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.map import run_map

class TestMap(unittest.TestCase):

    @patch('cli.map.check_setup')
    def test_run_map_dry_run(self, mock_check_setup):
        with patch('builtins.print') as mock_print:
            run_map(is_dry_run=True)
            mock_print.assert_any_call("\n[!] Dry Run complete for Phase 2.")

    @patch('cli.map.check_setup')
    @patch('cli.map.MANIFEST_PATH')
    def test_run_map_no_manifest(self, mock_manifest_path, mock_check_setup):
        mock_manifest_path.exists.return_value = False
        with patch('builtins.print') as mock_print:
            run_map()
            mock_print.assert_any_call("\n[!] Error: Project Manifest not found. Please run 'govern' first.")

    @patch('cli.map.check_setup')
    @patch('cli.map.MANIFEST_PATH')
    @patch('cli.map.discovery.get_discovery_report')
    @patch('cli.map.ADVERSARY_PROMPT_PATH')
    @patch('cli.map.provider.chat')
    @patch('cli.map.questionary.select')
    @patch('cli.map.os.system')
    @patch('builtins.open', new_callable=mock_open, read_data='{"project_name": "Test"}')
    def test_run_map_full(self, mock_file, mock_os_system, mock_select, mock_chat, mock_prompt_path, mock_discovery, mock_manifest_path, mock_check_setup):
        mock_manifest_path.exists.return_value = True
        mock_discovery.return_value = {"found": "ollama"}
        mock_chat.return_value = "Adversary Analysis with THREAT_MAP"
        mock_select.return_value.ask.return_value = "exit"
        
        # We need to handle multiple open calls
        # 1. MANIFEST_PATH
        # 2. ADVERSARY_PROMPT_PATH
        # 3. Artifact export
        
        handles = [
            mock_open(read_data='{"project_name": "Test"}').return_value,
            mock_open(read_data='System Prompt').return_value,
            mock_open().return_value
        ]
        mock_file.side_effect = handles
        
        run_map(is_autopilot=False)
        
        mock_chat.assert_called_once()
        mock_select.assert_called_once()

    @patch('cli.map.check_setup')
    @patch('cli.map.MANIFEST_PATH')
    @patch('cli.map.discovery.get_discovery_report')
    @patch('cli.map.ADVERSARY_PROMPT_PATH')
    @patch('cli.map.provider.chat')
    @patch('cli.map.auditor.generate_garak_command')
    @patch('cli.map.os.system')
    @patch('builtins.open', new_callable=mock_open, read_data='{"project_name": "Test"}')
    def test_run_map_autopilot(self, mock_file, mock_os_system, mock_garak, mock_chat, mock_prompt_path, mock_discovery, mock_manifest_path, mock_check_setup):
        mock_manifest_path.exists.return_value = True
        mock_discovery.return_value = {"found": "ollama"}
        mock_chat.return_value = "Analysis"
        mock_garak.return_value = "garak --test"
        
        handles = [
            mock_open(read_data='{"project_name": "Test"}').return_value,
            mock_open(read_data='System Prompt').return_value,
            mock_open().return_value
        ]
        mock_file.side_effect = handles
        
        run_map(is_autopilot=True)
        
        mock_os_system.assert_called_with("garak --test")

if __name__ == '__main__':
    unittest.main()
