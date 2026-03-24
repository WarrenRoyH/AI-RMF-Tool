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

def test_run_compliance_audit_mock():
    """Test full compliance audit report generation."""
    auditor = Auditor()
    
    mock_manifest = {
        "project_name": "Test Project",
        "safety_policy": {"prohibited_content": ["Hate"], "pii_protection": True},
        "ai_bom": {"model_id": "test-model"},
        "risk_profile": {"tier": "low", "domain": "test"},
        "accountability": {"security_contact": "test@example.com"},
        "benchmarks": {"target_accuracy": 0.9}
    }
    
    with patch('core.auditor.discovery.get_discovery_report', return_value={}), \
         patch.object(Auditor, 'run_sast_scan', return_value=["No risks"]), \
         patch.object(Auditor, 'run_infra_audit', return_value=["Secure"]), \
         patch.object(Auditor, 'run_supply_chain_scan', return_value=("✅ No vulnerabilities", [])), \
         patch.object(Auditor, 'run_bias_scan', return_value="99%"), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_manifest))), \
         patch('pathlib.Path.glob', return_value=[]), \
         patch('pathlib.Path.write_text'):
        
        # We need to mock the violations log read too
        # open() is already mocked for manifest
        # Let's use a side_effect for open
        
        manifest_json = json.dumps(mock_manifest)
        violations_jsonl = '{"type": "input_block", "risk_score": 0.9}\n'
        pf_results_json = json.dumps({"results": {"stats": {"successes": 10, "failures": 0}}})
        
        def open_side_effect(path, mode='r', *args, **kwargs):
            p = str(path)
            if "project-manifest.json" in p:
                return mock_open(read_data=manifest_json).return_value
            if "sentry_violations.jsonl" in p:
                return mock_open(read_data=violations_jsonl).return_value
            if "promptfoo_results.json" in p:
                return mock_open(read_data=pf_results_json).return_value
            if "summary.json" in p:
                return mock_open().return_value
            if "index.html" in p:
                return mock_open(read_data="const LATEST_AUDIT_DATA = {};").return_value
            return mock_open().return_value

        with patch('builtins.open', side_effect=open_side_effect):
            res = auditor.run_compliance_audit()
            assert "NIST Compliance Report Updated" in res

def test_generate_nutrition_label_direct():
    auditor = Auditor()
    mock_manifest = {
        "ai_bom": {"model_id": "test"},
        "risk_profile": {"tier": "low"},
        "safety_policy": {"pii_protection": True}
    }
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_manifest))), \
         patch('pathlib.Path.write_text'):
        res = auditor.generate_nutrition_label()
        assert "Nutrition Label generated" in res

def test_run_adversarial_sim_direct():
    auditor = Auditor()
    with patch('core.provider.provider.chat', return_value="{}"), \
         patch('core.sentry.sentry.validate_input', return_value=("", True, 0.0)), \
         patch('pathlib.Path.write_text'):
        res = auditor.run_adversarial_sim()
        assert "Adversarial simulation complete" in res

def test_export_report_direct():
    auditor = Auditor()
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.read_text', return_value="# Title"), \
         patch('pathlib.Path.write_text'), \
         patch('markdown.markdown', return_value="<html></html>"):
        res = auditor.export_report(format="html")
        assert "Report exported to HTML" in res

def test_bundle_evidence_package_mock():
    """Test evidence package bundling."""
    auditor = Auditor()
    
    with patch('zipfile.ZipFile'), \
         patch('core.auditor.calculate_sha256', return_value="hash"), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open()):
        res = auditor.bundle_evidence_package()
        assert "NIST RMF Evidence Package" in res

def test_verify_evidence_package_mock():
    """Test evidence package verification."""
    auditor = Auditor()
    
    mock_registry = {"file1": "hash1"}
    
    with patch('zipfile.ZipFile'), \
         patch('tempfile.TemporaryDirectory') as mock_tmp, \
         patch('pathlib.Path.exists', return_value=True), \
         patch('core.auditor.calculate_sha256', return_value="hash1"), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_registry))):
        
        mock_tmp.return_value.__enter__.return_value = "/tmp"
        res = auditor.verify_evidence_package("package.zip")
        assert "EVIDENCE INTEGRITY REPORT: SECURE" in res
        assert "file1: Verified" in res

def test_generate_promptfoo_config_mock():
    """Test promptfoo config generation."""
    auditor = Auditor()
    mock_manifest = {
        "evaluation_dataset": [{"query": "test?", "expected": "yes", "grading_type": "contains"}]
    }
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_manifest))), \
         patch('pathlib.Path.write_text'):
        cmd = auditor.generate_promptfoo_config()
        assert "promptfoo eval" in cmd

def test_generate_garak_command_mock():
    """Test garak command generation."""
    auditor = Auditor()
    mock_manifest = {
        "safety_policy": {"prohibited_content": ["PII", "Toxic"]}
    }
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_manifest))), \
         patch('pathlib.Path.mkdir'):
        cmd = auditor.generate_garak_command()
        assert "garak" in cmd
        assert "leakreplay" in cmd # Because PII is in prohibited

def test_run_bias_scan_mock():
    """Test bias scan execution."""
    auditor = Auditor()
    mock_manifest = {}
    mock_bias_res = {"results": {"stats": {"successes": 10, "failures": 0}}}
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_bias_res))), \
         patch('os.system'):
        res = auditor.run_bias_scan(mock_manifest)
        assert res == "100.0%"
