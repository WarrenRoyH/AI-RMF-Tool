import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from pathlib import Path
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.red_teamer import RedTeamer

class TestRedTeamerCore(unittest.TestCase):

    def test_run_stress_test(self):
        red_teamer = RedTeamer(workspace_dir="test_workspace")
        
        mock_manifest_path = MagicMock(spec=Path)
        mock_manifest_path.exists.return_value = True
        mock_manifest_path.__str__.return_value = "project-manifest.json"
        red_teamer.manifest_path = mock_manifest_path
        
        mock_prompt_path = MagicMock(spec=Path)
        mock_prompt_path.__str__.return_value = "red_teamer_prompt.md"
        red_teamer.prompt_path = mock_prompt_path
        
        mock_data_factory = MagicMock()
        mock_data_factory.generate_adversarial_csv.return_value = "data.csv"
        red_teamer.data_factory = mock_data_factory
        
        mock_provider = MagicMock()
        mock_provider.chat.return_value = "Plan with garak command."
        
        def open_side_effect(path, mode='r', *args, **kwargs):
            if "project-manifest.json" in str(path):
                return mock_open(read_data='{"project_name": "Test"}').return_value
            if "red_teamer_prompt.md" in str(path):
                return mock_open(read_data='System Prompt').return_value
            return mock_open().return_value

        with patch('builtins.open', side_effect=open_side_effect), \
             patch('core.red_teamer.provider', mock_provider), \
             patch('os.system'), \
             patch('core.auditor.auditor.generate_garak_command', return_value="garak --test"):
            res = red_teamer.run_stress_test()
            assert "Red Team session complete" in res
            mock_provider.chat.assert_called_once()

if __name__ == '__main__':
    unittest.main()
