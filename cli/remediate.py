import json
from cli.utils import check_setup, WORKSPACE_DIR
from core.remediator import remediator

def run_remediate(is_dry_run=False):
    check_setup()
    print("\n" + "="*60)
    print(f"--> Phase 3: MANAGE (The Remediator){' [DRY RUN MODE]' if is_dry_run else ''}")
    print("="*60)
    
    summary_path = WORKSPACE_DIR / "reports" / "summary.json"
    if not summary_path.exists():
        print("\n[!] Error: No audit summary found. Run 'measure' first.")
        return

    with open(summary_path, 'r') as f:
        summary = json.load(f)

    print(f"\n[STEP 1]: Analyzing failures from the latest audit ({summary.get('timestamp')})...")
    
    # Try to find the most relevant report file
    report_path = WORKSPACE_DIR / "reports" / "latest_audit_report.md"
    if not report_path.exists():
        report_path = summary_path # Fallback to summary JSON

    res = remediator.suggest_patch(report_path)
    print(f"--> [SUCCESS]: {res}")
    
    patch_path = WORKSPACE_DIR / "reports" / "suggested_patch.md"
    if patch_path.exists():
        with open(patch_path, 'r') as f:
            print("\n" + "-"*40)
            print("SUGGESTED SYSTEM PROMPT PATCH:")
            print("-"*40)
            print(f.read())
            print("-"*40)

        if is_dry_run:
            print("\n[!] Dry Run complete. Patch NOT applied.")
            return

        # In a real CLI, we might use questionary.confirm
        # But for autonomous cycles, we apply it.
        import os
        if os.getenv("AI_RMF_YOLO") == "true":
            print("\n[YOLO]: Applying patch automatically...")
            res = remediator.apply_patch()
            print(f"--> [APPLIED]: {res}")
        else:
            print("\n[INFO]: Run with AI_RMF_YOLO=true to apply the patch automatically.")
