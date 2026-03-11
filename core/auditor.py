import json
from pathlib import Path
from datetime import datetime

class Auditor:
    """
    Phase 4: MEASURE (The Auditor)
    A historical review tool for analyzing system compliance and safety performance.
    """
    def __init__(self, workspace_dir="workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.log_path = self.workspace_dir / "logs" / "sentry_violations.jsonl"
        self.manifest_path = self.workspace_dir / "project-manifest.json"
        self.report_path = self.workspace_dir / "reports" / "audit_report.md"

    def run_compliance_audit(self):
        """Analyzes logs against manifest policies and generates a report."""
        if not self.log_path.exists():
            return "No violation logs found. System is clean or 'manage' has not been run."

        if not self.manifest_path.exists():
            return "Error: Project Manifest missing. Audit cannot be mapped to policies."

        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)

        violations = []
        with open(self.log_path, 'r') as f:
            for line in f:
                violations.append(json.loads(line))

        # Perform analysis
        total_violations = len(violations)
        input_blocks = sum(1 for v in violations if v['type'] == 'input_block')
        output_blocks = sum(1 for v in violations if v['type'] == 'output_block')
        redactions = sum(1 for v in violations if v['type'] == 'input_redaction')

        # Generate the Report
        report_content = [
            f"# NIST AI RMF Audit Report: {manifest['project_name']}",
            f"**Audit Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Risk Tier:** {manifest['risk_profile']['tier'].upper()}",
            "\n## 1. Safety Performance Summary",
            f"- **Total Security Events Captured:** {total_violations}",
            f"- **Attacker Inputs Blocked (Map-related):** {input_blocks}",
            f"- **Policy-Violating Outputs Blocked (Manage-related):** {output_blocks}",
            f"- **Sensitive Data Redacted (Privacy-related):** {redactions}",
            "\n## 2. Policy Compliance Mapping",
        ]

        # Check against Benchmarks
        accuracy_target = manifest['benchmarks'].get('target_accuracy', 0.90)
        # Simple heuristic: high violation count might indicate "Safety Drift"
        if total_violations > 50:
            report_content.append(f"**[WARNING]** High violation count detected. Risk tier may need reassessment (MAP-3).")
        else:
            report_content.append(f"**[OK]** System performance is within expected NIST safety bounds.")

        report_content.append("\n## 3. Recommended Actions")
        if input_blocks > 0:
            report_content.append("- Review Phase 2 (MAP) scan results to identify recurring injection patterns.")
        if output_blocks > 0:
            report_content.append("- Refine Phase 1 (GOVERN) policies; the model is consistently generating prohibited content.")

        # Save the report
        with open(self.report_path, 'w') as f:
            f.write("\n".join(report_content))

        return f"Audit complete. Report generated at: {self.report_path}"

auditor = Auditor()
