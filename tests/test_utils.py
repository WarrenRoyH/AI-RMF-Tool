import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.utils import check_setup

class TestUtils(unittest.TestCase):

    @patch('cli.utils.WORKSPACE_DIR')
    @patch('cli.utils.provider')
    def test_check_setup_ok(self, mock_provider, mock_workspace_dir):
        mock_provider.validate_setup.return_value = True
        with patch('builtins.print'):
            check_setup()
            mock_provider.validate_setup.assert_called_once()
            # Verify mkdir calls
            mock_workspace_dir.mkdir.assert_called()

    @patch('cli.utils.WORKSPACE_DIR')
    @patch('cli.utils.provider')
    @patch('sys.exit')
    def test_check_setup_fail(self, mock_exit, mock_provider, mock_workspace_dir):
        mock_provider.validate_setup.side_effect = ValueError("Missing key")
        with patch('builtins.print'):
            check_setup()
            mock_exit.assert_called_with(1)

if __name__ == '__main__':
    unittest.main()
