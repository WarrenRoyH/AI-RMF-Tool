import unittest
from unittest.mock import patch, MagicMock, mock_open
import csv
from pathlib import Path
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from librarian.data_factory import DataFactory

class TestDataFactory(unittest.TestCase):

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_adversarial_csv(self, mock_file, mock_mkdir):
        factory = DataFactory(output_dir="test_data")
        path = factory.generate_adversarial_csv(num_rows=10)
        
        self.assertIn("test_data", path)
        mock_file.assert_called()
        # Verify CSV writing
        handle = mock_file()
        # csv.writer calls write multiple times
        self.assertTrue(handle.write.called)

if __name__ == '__main__':
    unittest.main()
