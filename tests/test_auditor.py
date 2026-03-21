import sys
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core.auditor import Auditor

def test_run_sast_scan_mock():
    """Test SAST scan with mocked subprocess."""
    auditor = Auditor()
    
    # Mock subprocess.run for grep commands
    mock_res = MagicMock()
    mock_res.stdout = "example_file.py:API_KEY=12345"
    mock_res.returncode = 0
    
    with patch('subprocess.run', return_value=mock_res):
        results = auditor.run_sast_scan()
        assert len(results) > 0
        assert "Potential Secrets Found" in results[0]

def test_run_supply_chain_scan_mock():
    """Test supply chain scan with mocked pip-audit."""
    auditor = Auditor()
    
    # Mock pip-audit output
    mock_audit_out = json.dumps({
        "dependencies": [
            {
                "name": "vulnerable-pkg",
                "version": "1.0.0",
                "vulns": [{"id": "CVE-2024-1234"}]
            }
        ]
    })
    
    mock_res = MagicMock()
    mock_res.stdout = mock_audit_out
    mock_res.returncode = 1 # Found vulnerabilities
    
    with patch('subprocess.run', return_value=mock_res):
        msg, vulns = auditor.run_supply_chain_scan()
        assert "FOUND 1 unique vulnerabilities" in msg
        assert len(vulns) == 1

def test_generate_compliance_policies_mock():
    """Test policy generation logic."""
    auditor = Auditor()
    
    mock_manifest = {
        "project_name": "Test Project",
        "safety_policy": {"prohibited_content": ["Test Content"], "pii_protection": True},
        "ai_bom": {"model_id": "test-model"},
        "risk_profile": {"tier": "low", "domain": "test"},
        "accountability": {"security_contact": "test@example.com"}
    }
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_manifest))), \
         patch('pathlib.Path.mkdir'), \
         patch('pathlib.Path.write_text'):
        res = auditor.generate_compliance_policies()
        assert "NIST policies generated" in res

def test_check_drift_mock():
    """Test drift calculation logic."""
    auditor = Auditor()
    
    # Mock glob and file reading for previous audit reports
    with patch('pathlib.Path.glob', return_value=[Path("audit_report_1.md"), Path("audit_report_2.md")]), \
         patch('os.path.getmtime', side_effect=[200, 100]), \
         patch('pathlib.Path.read_text', return_value="System achieved 90.0% accuracy"):
        drift = auditor.check_drift("95.0%")
        assert drift == "+5.0%"

def test_run_infra_audit_mock():
    """Test infrastructure audit."""
    auditor = Auditor()
    
    # Mock .env file status
    mock_stat = MagicMock()
    mock_stat.st_mode = 0o600 # Secure permissions
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.stat', return_value=mock_stat):
        findings = auditor.run_infra_audit()
        assert any("Secure .env" in f for f in findings)
