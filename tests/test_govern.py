import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from pathlib import Path
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.govern import run_govern, librarian_verify

class TestGovern(unittest.TestCase):

    @patch('cli.govern.check_setup')
    def test_run_govern_dry_run(self, mock_check_setup):
        with patch('builtins.print') as mock_print:
            run_govern(is_dry_run=True)
            mock_print.assert_any_call("\n[!] Dry Run: Skipping Librarian interview and policy drafting.")

    @patch('cli.govern.check_setup')
    @patch('cli.govern.MANIFEST_PATH')
    @patch('cli.govern.questionary.confirm')
    @patch('cli.govern.librarian_verify')
    def test_run_govern_resume(self, mock_librarian_verify, mock_confirm, mock_manifest_path, mock_check_setup):
        mock_manifest_path.exists.return_value = True
        mock_confirm.return_value.ask.return_value = True
        
        mock_manifest_content = json.dumps({
            "project_name": "Test Project",
            "ai_bom": {"model_id": "gpt-4", "version": "1.0", "provider": "OpenAI"}
        })
        
        with patch('builtins.open', mock_open(read_data=mock_manifest_content)):
            run_govern(is_autopilot=False)
            
            mock_librarian_verify.assert_called_once()
            draft_manifest = mock_librarian_verify.call_args[0][0]
            self.assertEqual(draft_manifest["project_name"], "Test Project")
            self.assertIsInstance(draft_manifest["ai_bom"], list)
            self.assertEqual(draft_manifest["ai_bom"][0]["component_id"], "gpt-4")

    @patch('cli.govern.check_setup')
    @patch('cli.govern.MANIFEST_PATH')
    @patch('cli.govern.discovery.get_discovery_report')
    @patch('cli.govern.questionary')
    @patch('cli.govern.librarian_verify')
    @patch('builtins.open', new_callable=mock_open, read_data='{"Template": {"risk_profile": {"tier": "low", "domain": "General"}, "safety_policy": {"prohibited_content": ["Hate"]}}}')
    def test_run_govern_full_interview(self, mock_file, mock_librarian_verify, mock_questionary, mock_discovery, mock_manifest_path, mock_check_setup):
        mock_manifest_path.exists.return_value = False
        mock_discovery.return_value = "Discovery Report"
        
        # Mock questionary sequence
        # select: 1. Template, 2. Comp Type, 3. Risk Tier, 4. Perf Standard, 5. PII Risk
        mock_questionary.select.return_value.ask.side_effect = ["Template", "model", "low", "standard", "low"]
        
        # text: 1. Project Name, 2. Comp ID, 3. Version, 4. Provider, 5. Domain, 
        #       6. Custom Prohibited, 7. Org Name, 8. Security Contact, 9. Reporting Window,
        #       10. HITL, 11. Training, 12. Provenance, 13. Tradeoffs
        mock_questionary.text.return_value.ask.side_effect = [
            "Project X", "Comp1", "1.1", "Prov1", "General", 
            "CustomHate", "Org1", "sec@org.com", "24", 
            "HITL", "Training", "Data", "Tradeoffs"
        ]
        
        # confirm: 1. Add another comp?, 2. PII Anonymize, 3. Flag high-risk, 4. Licenses cleared
        mock_questionary.confirm.return_value.ask.side_effect = [False, True, True, True]
        
        mock_questionary.checkbox.return_value.ask.return_value = ["Hate"]
        
        run_govern(is_autopilot=False)
        
        mock_librarian_verify.assert_called_once()
        draft_manifest = mock_librarian_verify.call_args[0][0]
        self.assertEqual(draft_manifest["project_name"], "Project X")
        self.assertEqual(len(draft_manifest["ai_bom"]), 1)
        self.assertEqual(draft_manifest["ai_bom"][0]["component_id"], "Comp1")
        self.assertEqual(draft_manifest["risk_profile"]["tier"], "low")

    @patch('cli.govern.LIBRARIAN_PROMPT_PATH')
    @patch('cli.govern.provider.chat')
    @patch('cli.govern.questionary.select')
    @patch('cli.govern.questionary.confirm')
    @patch('cli.govern.MANIFEST_PATH')
    @patch('cli.govern.auditor.generate_compliance_policies')
    @patch('cli.govern.WORKSPACE_DIR')
    @patch('builtins.open', new_callable=mock_open, read_data='System Prompt')
    def test_librarian_verify_finalize(self, mock_file, mock_workspace_dir, mock_policies, mock_manifest_path, mock_confirm, mock_select, mock_chat, mock_prompt_path):
        mock_chat.side_effect = [
            "Initial Review", # First chat call
            "Here is your manifest: ```json\n{\"project_name\": \"Final Project\"}\n```", # Finalize call
            "```json\n[{\"query\": \"test\"}]\n```" # Dataset call
        ]
        mock_select.return_value.ask.return_value = "finalize"
        mock_confirm.return_value.ask.return_value = True # Dataset confirmation
        mock_manifest_path.__str__.return_value = "workspace/project-manifest.json"
        mock_workspace_dir.__truediv__.return_value = Path("workspace/reports")
        
        draft_manifest = {"project_name": "Initial Project"}
        
        librarian_verify(draft_manifest, is_autopilot=True)
        
        # Verify provider.chat was called (Initial, Finalize, Dataset)
        self.assertEqual(mock_chat.call_count, 3)
        mock_policies.assert_called_once()

if __name__ == '__main__':
    unittest.main()
