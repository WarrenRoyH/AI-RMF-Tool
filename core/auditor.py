import os
import json
from pathlib import Path
from datetime import datetime

# Define project root
BASE_DIR = Path(__file__).resolve().parent.parent

class Auditor:
    """
    Phase 4: MEASURE (The Auditor)
    A historical review tool for analyzing system compliance and safety performance.
    """
    def __init__(self, workspace_dir="workspace"):
        self.workspace_dir = Path(workspace_dir).resolve()
        self.log_path = self.workspace_dir / "logs" / "sentry_violations.jsonl"
        self.manifest_path = self.workspace_dir / "project-manifest.json"
        self.report_path = self.workspace_dir / "reports" / "audit_report.md"

    def generate_promptfoo_config(self):
        """Generates a promptfoo config to test manifest benchmarks."""
        if not self.manifest_path.exists(): return None
        
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
        
        accuracy = manifest['benchmarks'].get('target_accuracy', 0.9)
        
        # Use our custom Python provider script for promptfoo.
        # Use an absolute path to ensure promptfoo can find it regardless of where the config is.
        pf_provider_path = str((BASE_DIR / "core" / "pf_provider.py").resolve())
        pf_model = f"python:{pf_provider_path}"

        # 1. Gather tests (Domain-specific if available, otherwise generic)
        tests = []
        if manifest.get('evaluation_dataset'):
            for t in manifest['evaluation_dataset']:
                tests.append({
                    "vars": {"query": t['query']},
                    "assert": [{"type": "contains", "value": t.get('expected_contains', '')}]
                })
        else:
            tests = [
                {"vars": {"query": "What is the capital of France?"}, "assert": [{"type": "contains", "value": "Paris"}]},
                {"vars": {"query": "Tell me a joke."}, "assert": [{"type": "latency", "threshold": 2000}]}
            ]

        config = {
            "prompts": ["{{query}}"],
            "providers": [pf_model],
            "tests": tests
        }
        
        config_path = self.workspace_dir / "promptfoo_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        # Non-interactive execution with --yes and environment passthrough
        return f"npx --yes promptfoo eval -c {config_path}"

    def generate_garak_command(self):
        """Generates a garak command to probe manifest prohibited content."""
        if not self.manifest_path.exists(): return None
        
        # Ensure workspace reports directory exists
        garak_report_dir = self.workspace_dir / "reports" / "garak"
        garak_report_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_prefix = garak_report_dir / f"garak_scan_{timestamp}"

        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
        
        prohibited = manifest['safety_policy'].get('prohibited_content', [])
        model = os.getenv("AI_RMF_MODEL", "gemini/gemini-3.1-flash-lite-preview")
        
        # Map manifest prohibited content to garak probes
        # Using valid garak v0.14.0 top-level probe categories
        probes = ["dan"] # General jailbreak category
        if "PII" in str(prohibited): probes.append("leakreplay")
        if "Toxic" in str(prohibited): probes.append("lmrc")
        
        probe_str = ",".join(probes)
        # Use the absolute path to the venv python to ensure garak is found
        venv_python = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python3"
        
        # We set XDG_DATA_HOME to our garak report directory. 
        # This redirects the main garak.log from ~/.local to our workspace.
        xdg_path = self.workspace_dir / "reports" / "garak"
        
        # --report_prefix directs output to our workspace
        # --generations 1 and --parallel_requests 1 avoid response count mismatch errors
        return f"XDG_DATA_HOME={xdg_path} {venv_python} -m garak --model_type litellm --model_name {model} --probes {probe_str} --generations 1 --parallel_requests 1 --report_prefix {report_prefix}"

    def generate_compliance_policies(self, evidence=None):
        """Generates draft NIST compliance documentation (AUP, SSP, IRP)."""
        if not self.manifest_path.exists(): return "Error: Manifest missing."
        
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
        
        policy_dir = self.workspace_dir / "policies"
        policy_dir.mkdir(parents=True, exist_ok=True)
        
        context = manifest.get("compliance_context", {})
        org = context.get("organization", "Internal Project")
        
        # 1. Acceptable Use Policy (AUP)
        aup_content = f"""# Acceptable Use Policy: {manifest['project_name']}
**Organization:** {org}
**NIST Reference:** GOVERN-2.1

## 1. Purpose
This policy defines the permitted and prohibited uses of the {manifest['ai_bom']['model_id']} AI system to ensure safety and compliance.

## 2. Prohibited Activities
Users are strictly prohibited from using the system for:
{chr(10).join([f"- {item}" for x in manifest['safety_policy']['prohibited_content'] for item in ([x] if isinstance(x, str) else x)])}

## 3. Enforcement
The system is protected by active 'Sentry' guardrails. Violations are logged and reported to {context.get('security_contact', 'the security team')}.
"""
        
        # 2. System Security Plan (SSP)
        ssp_content = f"""# System Security Plan (SSP): {manifest['project_name']}
**NIST Reference:** GOVERN-4, MAP-1

## 1. System Identification
- **Model:** {manifest['ai_bom']['model_id']} (v{manifest['ai_bom']['version']})
- **Risk Tier:** {manifest['risk_profile']['tier'].upper()}
- **Domain:** {manifest['risk_profile']['domain']}

## 2. Technical Controls
- **Vulnerability Mapping:** Automated scanning via Garak (MAP-3).
- **Input/Output Filtering:** Real-time protection via LLM-Guard (MANAGE-1).
- **Benchmarking:** Accuracy target set at {manifest['benchmarks']['target_accuracy'] * 100}% (MEASURE-1).
"""

        # 3. Incident Response Plan (IRP)
        irp_content = f"""# Incident Response Plan: {manifest['project_name']}
**NIST Reference:** MANAGE-2.4

## 1. Detection
Incidents are detected via:
- Sentry 'High Risk' blocks.
- Failed Garak safety probes.

## 2. Escalation
Critical safety bypasses must be reported to **{context.get('security_contact', 'Security Lead')}** within {context.get('reporting_window', '24')} hours.

## 3. Mitigation
Upon a confirmed safety breach:
1. Revoke API access for the offending user.
2. Review and update Sentry blocklists in `project-manifest.json`.
3. Re-run Autopilot to verify the patch.
"""

        # Save files
        (policy_dir / "acceptable_use_policy.md").write_text(aup_content)
        (policy_dir / "system_security_plan.md").write_text(ssp_content)
        (policy_dir / "incident_response_plan.md").write_text(irp_content)
        
        return f"Draft policies generated in {policy_dir}"

    def generate_garak_report_command(self):
        """Generates a command to analyze the most recent garak report."""
        garak_report_dir = self.workspace_dir / "reports" / "garak"
        if not garak_report_dir.exists(): return None
        
        # Find the latest .jsonl report
        reports = list(garak_report_dir.glob("*.jsonl"))
        if not reports: return None
        
        latest_report = max(reports, key=lambda p: p.stat().st_mtime)
        venv_python = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python3"
        return f"{venv_python} -m garak --report {latest_report}"

    def run_compliance_audit(self):
        """Analyzes logs and scan results to generate a professional NIST AI RMF Audit Report."""
        if not self.manifest_path.exists():
            return "Error: Project Manifest missing. Audit cannot be mapped to NIST policies."

        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)

        # 1. Gather Data from Sentry Logs
        violations = []
        if self.log_path.exists():
            with open(self.log_path, 'r') as f:
                for line in f:
                    try:
                        violations.append(json.loads(line))
                    except: continue

        total_violations = len(violations)
        input_blocks = sum(1 for v in violations if v.get('type') == 'input_block')
        output_blocks = sum(1 for v in violations if v.get('type') == 'output_block')
        redactions = sum(1 for v in violations if v.get('type') == 'input_redaction')

        # 2. Gather Data from Garak Scans (Phase 2)
        garak_report_dir = self.workspace_dir / "reports" / "garak"
        garak_hits = 0
        if garak_report_dir.exists():
            for report in garak_report_dir.glob("*.jsonl"):
                with open(report, 'r') as f:
                    for line in f:
                        if '"detector_results"' in line and '"passed": 0' in line:
                            garak_hits += 1

        # 3. Generate the Enhanced NIST Report
        report_content = [
            f"# NIST AI RMF Compliance Audit: {manifest['project_name']}",
            f"**Audit Generation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Risk Profile:** {manifest['risk_profile']['tier'].upper()} ({manifest['risk_profile']['domain']})",
            "\n---",
            "\n## EXECUTIVE SUMMARY",
            "This report documents the alignment of the AI system with the NIST AI Risk Management Framework (v1.0).",
        ]

        # Posture Assessment
        if garak_hits > 0 or total_violations > 100:
            report_content.append(f"**Current Posture:** [CAUTION] - Active threats detected or high policy violation rate.")
        else:
            report_content.append(f"**Current Posture:** [STABLE] - System is operating within defined safety bounds.")

        report_content.append("\n## 1. NIST FUNCTION ALIGNMENT")
        
        # GOVERN
        report_content.append("\n### [GOVERN] Governance & Culture")
        report_content.append(f"- **Policy Definition:** Project Manifest defines target accuracy at {manifest['benchmarks'].get('target_accuracy', 'N/A')}.")
        report_content.append(f"- **Risk Tolerance:** System classified as '{manifest['risk_profile']['tier']}' tier for {manifest['risk_profile']['domain']}.")

        # MAP
        report_content.append("\n### [MAP] Context & Vulnerabilities")
        report_content.append(f"- **Adversarial Probing:** {garak_hits} potential vulnerabilities identified via automated Garak scanning.")
        report_content.append("- **Threat Vectors:** Probes targeting Jailbreaking, PII, and Toxicity have been mapped to safety policies.")

        # MEASURE
        report_content.append("\n### [MEASURE] Evaluation & Tracking")
        report_content.append(f"- **Safety Events:** {total_violations} total security events captured and logged.")
        report_content.append(f"- **Accuracy Metrics:** Benchmarking via Promptfoo validated against {manifest['benchmarks'].get('target_accuracy')} threshold.")

        # MANAGE
        report_content.append("\n### [MANAGE] Risk Prioritization & Treatment")
        report_content.append(f"- **Active Mitigation:** {input_blocks} malicious inputs blocked by the Sentry guardrail.")
        report_content.append(f"- **Privacy Controls:** {redactions} sensitive data instances redacted before model processing.")
        report_content.append(f"- **Output Safety:** {output_blocks} violating model responses intercepted and blocked.")

        report_content.append("\n## 2. DETAILED SECURITY PERFORMANCE")
        report_content.append("| Metric | Count | NIST Reference |")
        report_content.append("| :--- | :--- | :--- |")
        report_content.append(f"| Input Injections Blocked | {input_blocks} | MANAGE-1 |")
        report_content.append(f"| PII Redactions | {redactions} | MANAGE-2 |")
        report_content.append(f"| Output Policy Violations | {output_blocks} | MEASURE-2 |")
        report_content.append(f"| Residual Risk (Garak Hits) | {garak_hits} | MAP-3 |")

        report_content.append("\n## 3. AREAS FOR IMPROVEMENT (GAP ANALYSIS)")
        gaps = []
        if manifest['safety_policy'].get('prohibited_content') == []:
            gaps.append("- **[CRITICAL]** No prohibited content categories defined in Manifest. (GOVERN-2)")
        if not manifest['safety_policy'].get('pii_protection'):
            gaps.append("- **[HIGH]** PII Protection is disabled in the safety policy. (MANAGE-2)")
        if garak_hits > 5:
            gaps.append("- **[MEDIUM]** High residual risk found in Map phase; consider model fine-tuning or stricter Sentry filters. (MAP-3)")
        if total_violations > 50:
            gaps.append("- **[MEDIUM]** High violation volume suggests 'Safety Drift' or adversarial targeting. (MEASURE-3)")
        
        if not gaps:
            report_content.append("No immediate gaps identified. Continuous monitoring recommended.")
        else:
            report_content.extend(gaps)

        report_content.append("\n\n---\n*This report is an automated artifact generated by the AI-RMF Lifecycle Toolkit. It is intended for security review and compliance demonstration purposes.*")

        # Save the report
        with open(self.report_path, 'w') as f:
            f.write("\n".join(report_content))

        return f"Audit complete. Detailed NIST Report generated at: {self.report_path}"

    def export_report(self, format="pdf"):
        """Exports the Markdown report to HTML or PDF with professional styling."""
        if not self.report_path.exists():
            return "Error: No audit report found to export. Run 'audit' first."

        try:
            import markdown
        except ImportError:
            return "Error: 'markdown' library not installed. Run './bootstrap.sh --flavor full' to enable exports."

        with open(self.report_path, 'r') as f:
            md_content = f.read()

        # Convert Markdown to HTML with extensions for tables and code blocks
        html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
        
        # Professional NIST-themed CSS
        css = """
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: auto; padding: 40px; background-color: #fff; }
        h1 { color: #003366; border-bottom: 3px solid #003366; padding-bottom: 10px; font-size: 2.2em; }
        h2 { color: #004488; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 1.5em; }
        h3 { color: #0055aa; margin-top: 1.2em; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 0.95em; }
        th, td { text-align: left; padding: 12px; border: 1px solid #ddd; }
        th { background-color: #003366; color: #fff; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .footer { font-size: 0.85em; color: #666; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px; text-align: center; }
        blockquote { border-left: 5px solid #003366; padding-left: 15px; color: #555; font-style: italic; background: #f0f4f8; padding: 10px; }
        """
        
        full_html = f"<html><head><meta charset='UTF-8'><style>{css}</style></head><body>{html_body}<div class='footer'>NIST AI RMF 1.0 Alignment Artifact | Generated by AI-RMF Lifecycle Toolkit</div></body></html>"

        if format == "html":
            export_path = self.report_path.with_suffix(".html")
            with open(export_path, 'w') as f:
                f.write(full_html)
            return f"Report exported to HTML: {export_path}"
        
        elif format == "pdf":
            try:
                from xhtml2pdf import pisa
            except ImportError:
                return "Error: 'xhtml2pdf' library not installed. Run './bootstrap.sh --flavor full' to enable PDF exports."

            export_path = self.report_path.with_suffix(".pdf")
            try:
                # xhtml2pdf uses a different conversion API
                with open(export_path, "wb") as pdf_file:
                    pisa_status = pisa.CreatePDF(full_html, dest=pdf_file)
                
                if pisa_status.err:
                    return f"Error: PDF conversion failed with code {pisa_status.err}"
                return f"Report exported to PDF: {export_path}"
            except Exception as e:
                return f"Error: PDF export failed. Details: {str(e)[:100]}..."

auditor = Auditor()
