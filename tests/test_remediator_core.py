import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from pathlib import Path
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.remediator import Remediator

class TestRemediatorCore(unittest.TestCase):

    def test_suggest_patch(self):
        remediator = Remediator(workspace_dir="test_workspace")
        
        mock_report_path = MagicMock(spec=Path)
        mock_report_path.exists.return_value = True
        mock_report_path.__str__.return_value = "report.md"
        
        mock_manifest_path = MagicMock(spec=Path)
        mock_manifest_path.exists.return_value = True
        mock_manifest_path.__str__.return_value = "project-manifest.json"
        remediator.manifest_path = mock_manifest_path
        
        mock_provider = MagicMock()
        mock_provider.chat.return_value = "```text\nHardened Prompt\n```"
        
        def open_side_effect(path, mode='r', *args, **kwargs):
            if "report.md" in str(path):
                return mock_open(read_data='Report content').return_value
            if "project-manifest.json" in str(path):
                return mock_open(read_data='{}').return_value
            return mock_open().return_value

        with patch('builtins.open', side_effect=open_side_effect), \
             patch('core.remediator.provider', mock_provider), \
             patch('pathlib.Path.write_text'):
            res = remediator.suggest_patch(mock_report_path)
            assert "Patch suggested" in res
            mock_provider.chat.assert_called_once()

    def test_apply_patch(self):
        remediator = Remediator(workspace_dir="test_workspace")
        
        mock_manifest_path = MagicMock(spec=Path)
        mock_manifest_path.exists.return_value = True
        mock_manifest_path.__str__.return_value = "project-manifest.json"
        remediator.manifest_path = mock_manifest_path
        
        def open_side_effect(path, mode='r', *args, **kwargs):
            if "project-manifest.json" in str(path):
                return mock_open(read_data='{}').return_value
            return mock_open().return_value

        path_mock = MagicMock(spec=Path)
        path_mock.exists.return_value = True
        path_mock.read_text.return_value = "Hardened Snippet"
        path_mock.__truediv__.return_value = path_mock

        with patch('pathlib.Path.__truediv__', return_value=path_mock), \
             patch('builtins.open', side_effect=open_side_effect):
            res = remediator.apply_patch()
            assert "Patch applied" in res

if __name__ == '__main__':
    unittest.main()
