import sys
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.discovery import ModelDiscovery

def test_find_running_models_mock():
    """Test finding running models with mocked psutil."""
    discovery = ModelDiscovery()
    
    # Mock psutil.process_iter
    mock_proc1 = MagicMock()
    mock_proc1.info = {'name': 'ollama', 'cmdline': ['ollama', 'serve']}
    mock_proc1.pid = 123
    
    mock_proc2 = MagicMock()
    mock_proc2.info = {'name': 'python', 'cmdline': ['python', '-m', 'vllm.entrypoints.openai.api_server']}
    mock_proc2.pid = 456
    
    with patch('psutil.process_iter', return_value=[mock_proc1, mock_proc2]):
        running = discovery.find_running_models()
        assert len(running) == 2
        assert any(r['type'] == 'Ollama' for r in running)
        assert any(r['type'] == 'vLLM' for r in running)

def test_scan_local_storage_mock():
    """Test scanning local storage with mocked os.walk."""
    discovery = ModelDiscovery()
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('os.walk', return_value=[('/root', ('subdir',), ('model.gguf', 'config.json'))]):
        models = discovery.scan_local_storage()
        assert len(models) > 0
        assert any("model.gguf" in m for m in models)

def test_scan_project_code_mock():
    """Test scanning project code for AI libraries."""
    discovery = ModelDiscovery()
    
    # Mocking Path.read_text to simulate dependency files
    mock_requirements = "openai\nlangchain\ntorch"
    
    with patch('pathlib.Path.exists', side_effect=lambda: True), \
         patch('pathlib.Path.read_text', return_value=mock_requirements), \
         patch('os.walk', return_value=[(str(Path.cwd()), ('subdir',), ('main.py',))]):
        findings = discovery.scan_project_code()
        assert any(l["file"] == "requirements.txt" and l["keyword"] == "openai" for l in findings["libraries"])
        assert any(l["file"] == "requirements.txt" and l["keyword"] == "langchain" for l in findings["libraries"])

def test_detect_purpose_mock():
    """Test purpose detection."""
    discovery = ModelDiscovery()
    
    with patch('pathlib.Path.cwd', return_value=Path('/home/user/my-chat-bot')):
        hints = discovery.detect_purpose()
        assert "Customer Interaction / Support" in hints

def test_scan_network_interfaces_mock():
    """Test scanning network interfaces with mocked socket."""
    discovery = ModelDiscovery()
    
    mock_socket = MagicMock()
    mock_socket.__enter__.return_value = mock_socket
    mock_socket.connect_ex.return_value = 0 # Simulate port open
    
    with patch('socket.socket', return_value=mock_socket):
        interfaces = discovery.scan_network_interfaces()
        assert len(interfaces) > 0
        assert any(i['name'] == 'Ollama' for i in interfaces)

def test_verify_ollama_models_mock():
    """Test verification of Ollama models via API mock."""
    discovery = ModelDiscovery()
    
    mock_tags_response = json.dumps({
        "models": [
            {"name": "llama3:latest", "size": 8.5 * 1024**3},
            {"name": "phi3:latest", "size": 2.3 * 1024**3}
        ]
    }).encode()
    
    mock_ps_response = json.dumps({
        "models": [
            {"name": "llama3:latest"}
        ]
    }).encode()
    
    # Mock urllib.request.urlopen responses
    mock_resp_tags = MagicMock()
    mock_resp_tags.status = 200
    mock_resp_tags.read.return_value = mock_tags_response
    mock_resp_tags.__enter__.return_value = mock_resp_tags
    
    mock_resp_ps = MagicMock()
    mock_resp_ps.status = 200
    mock_resp_ps.read.return_value = mock_ps_response
    mock_resp_ps.__enter__.return_value = mock_resp_ps
    
    with patch('urllib.request.urlopen', side_effect=[mock_resp_tags, mock_resp_ps]):
        models = discovery.verify_ollama_models()
        assert len(models) == 2
        assert models[0]['name'] == "llama3:latest"
        assert models[0]['status'] == "Loaded"
        assert models[1]['name'] == "phi3:latest"
        assert models[1]['status'] == "Installed"
