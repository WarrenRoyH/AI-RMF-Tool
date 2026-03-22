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
            "Select report type:",
            choices=[
                "HTML: Browser-friendly compliance report",
                "PDF: Formal auditor-ready report",
                "BUNDLE: Complete NIST RMF Evidence Package (ZIP)"
            ]
        ).ask()

    if "HTML" in report_format or report_format == "html":
        print("\n[STEP 1]: Exporting the latest compliance audit to HTML...")
        res = auditor.export_report(format="html")
        print(f"--> [RESULT]: {res}")
    elif "PDF" in report_format or report_format == "pdf":
        print("\n[STEP 1]: Exporting the latest compliance audit to PDF...")
        res = auditor.export_report(format="pdf")
        print(f"--> [RESULT]: {res}")
    elif "BUNDLE" in report_format:
        print("\n[STEP 1]: Aggregating all NIST-mapped artifacts into a zip package...")
        res = auditor.bundle_evidence_package()
        print(f"--> [RESULT]: {res}")

    
    if "pdf" in report_format and "xhtml2pdf" not in res:
        print("\n[INFO]: For PDF export, ensure 'xhtml2pdf' is installed in the environment.")
