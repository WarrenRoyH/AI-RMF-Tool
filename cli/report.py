import questionary
from cli.utils import check_setup
from core.auditor import auditor

def run_report(report_format=None):
    check_setup()
    print("\n" + "="*60)
    print("--> Phase 4: MEASURE (Unified Report Generator)")
    print("="*60)
    
    if not report_format:
        report_format = questionary.select(
            "Select report format:",
            choices=["html", "pdf"]
        ).ask()

    print(f"\n[STEP 1]: Exporting the latest compliance audit to {report_format.upper()}...")
    res = auditor.export_report(format=report_format)
    print(f"--> [RESULT]: {res}")
    
    if "pdf" in report_format and "xhtml2pdf" not in res:
        print("\n[INFO]: For PDF export, ensure 'xhtml2pdf' is installed in the environment.")
