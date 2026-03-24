import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from pathlib import Path
import sys
import os
from fastapi.testclient import TestClient

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.proxy import app

class TestProxy(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch('core.proxy.sentry.validate_input')
    @patch('core.proxy.provider.chat')
    @patch('core.proxy.sentry.validate_output')
    @patch('core.proxy.log_violation')
    def test_chat_proxy_success(self, mock_log, mock_validate_output, mock_chat, mock_validate_input):
        mock_validate_input.return_value = ("safe input", True, 0.0)
        mock_chat.return_value = "raw response"
        mock_validate_output.return_value = ("safe response", True, 0.0)
        
        request_body = {"messages": [{"role": "user", "content": "Hi"}]}
        response = self.client.post("/v1/chat/completions", json=request_body)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["choices"][0]["message"]["content"], "safe response")

    @patch('core.proxy.sentry.validate_input')
    @patch('core.proxy.log_violation')
    @patch('core.proxy.sentry.shadow_mode', False)
    def test_chat_proxy_input_blocked(self, mock_log, mock_validate_input):
        mock_validate_input.return_value = ("unsafe", False, 0.9)
        
        request_body = {"messages": [{"role": "user", "content": "Bad"}]}
        response = self.client.post("/v1/chat/completions", json=request_body)
        
        self.assertEqual(response.status_code, 200) # Fast API returns 200 with error info in body for this app
        data = response.json()
        self.assertIn("violates safety policies", data["choices"][0]["message"]["content"])
        mock_log.assert_called_once()

    @patch('core.proxy.sentry.validate_input')
    @patch('core.proxy.provider.chat')
    @patch('core.proxy.sentry.validate_output')
    @patch('core.proxy.log_violation')
    @patch('core.proxy.sentry.shadow_mode', False)
    def test_chat_proxy_output_blocked(self, mock_log, mock_validate_output, mock_chat, mock_validate_input):
        mock_validate_input.return_value = ("safe input", True, 0.0)
        mock_chat.return_value = "unsafe response"
        mock_validate_output.return_value = ("unsafe response", False, 0.9)
        
        request_body = {"messages": [{"role": "user", "content": "Hi"}]}
        response = self.client.post("/v1/chat/completions", json=request_body)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response was blocked", data["choices"][0]["message"]["content"])
        mock_log.assert_called_once()

    @patch('core.proxy.sentry.validate_input')
    @patch('core.proxy.provider.chat')
    @patch('core.proxy.sentry.validate_output')
    @patch('core.proxy.log_violation')
    @patch('core.proxy.sentry.shadow_mode', True)
    def test_chat_proxy_shadow_mode(self, mock_log, mock_validate_output, mock_chat, mock_validate_input):
        mock_validate_input.return_value = ("unsafe input", False, 0.9)
        mock_chat.return_value = "response"
        mock_validate_output.return_value = ("safe response", True, 0.0)
        
        request_body = {"messages": [{"role": "user", "content": "Bad"}]}
        response = self.client.post("/v1/chat/completions", json=request_body)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["choices"][0]["message"]["content"], "safe response")
        mock_log.assert_called_once()

if __name__ == '__main__':
    unittest.main()
