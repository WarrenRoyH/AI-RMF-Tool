import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from cli.govern import run_govern

@patch("cli.govern.questionary.confirm")
@patch("cli.govern.questionary.text")
@patch("cli.govern.questionary.select")
@patch("cli.govern.questionary.checkbox")
@patch("cli.govern.provider.chat")
@patch("cli.govern.provider.validate_setup")
@patch("cli.govern.MANIFEST_PATH")
@patch("cli.govern.discovery.get_discovery_report")
@patch("cli.govern.auditor.generate_compliance_policies")
def test_run_govern_full_flow(mock_policy, mock_discovery, mock_manifest_path, mock_validate, mock_chat, mock_checkbox, mock_select, mock_text, mock_confirm):
    # Setup mocks
    mock_validate.return_value = True
    mock_manifest_path.exists.return_value = False
    mock_discovery.return_value = {"test": "data"}
    mock_policy.return_value = "Policies generated."
    
    # Mock template loading
    mock_templates = {
        "General AI": {
            "risk_profile": {"tier": "medium", "domain": "General"},
            "safety_policy": {"prohibited_content": ["Hate Speech"]}
        }
    }
    
    # Mock questionary sequence
    mock_select.return_value.ask.side_effect = [
        "General AI", # STEP 0: Template
        "model",       # STEP 2: Component Type
        "medium",      # STEP 3: Risk Tier
        "standard",    # STEP 5: Performance Standard
        "low",         # STEP 7: PII Risk
        "finalize"     # Librarian action
    ]
    
    mock_text.return_value.ask.side_effect = [
        "My Project",  # STEP 1: Project Name
        "Primary Model", # STEP 2: Component ID
        "v1",           # STEP 2: Version
        "Provider",     # STEP 2: Provider
        "General",      # STEP 3: Domain
        "Custom Prohibited", # STEP 4: Custom
        "Org Name",     # STEP 6: Org
        "Contact",      # STEP 6: Contact
        "24",           # STEP 6: Reporting
        "HITL",         # STEP 7: HITL
        "Training",     # STEP 7: Training
        "Data",         # STEP 7: Data
        "Tradeoffs"     # STEP 7: Tradeoffs
    ]
    
    mock_confirm.return_value.ask.side_effect = [
        False, # Add another AI component?
        True,  # PII Protection
        True,  # Manual Review
        True,  # Data audited
        True,  # Would you like to generate a dataset?
        False  # Governance complete. Would you like to start Phase 2?
    ]
    
    mock_checkbox.return_value.ask.return_value = ["Hate Speech"]
    
    # Provider chat responses
    mock_chat.side_effect = [
        "Librarian: I am reviewing your draft.", # Seed response
        "Librarian: Finalizing. ```json\n{\"project_name\": \"My Project\"}\n```", # Finalize response
        "```json\n[{\"query\": \"test\", \"expected\": \"safe\", \"grading_type\": \"contains\"}]\n```" # Dataset response
    ]

    # Mock MANIFEST_PATH to return a string for open()
    mock_manifest_path.__fspath__.return_value = "/tmp/manifest.json"
    mock_manifest_path.__str__.return_value = "/tmp/manifest.json"

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_templates))):
        run_govern()
        
    # Verify manifest was saved
    # First call is to read templates, second is to read librarian prompt, third is to write manifest
    assert mock_chat.called
