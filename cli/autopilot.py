import questionary
import time
import sys
from cli.utils import check_setup, MANIFEST_PATH
from cli.govern import run_govern
from cli.map import run_map
from cli.manage import run_manage
from cli.measure import run_measure
from cli.remediate import run_remediate
from cli.verify import run_verify

def run_autopilot(is_dry_run=False, interval=0):
    check_setup()
    
    first_run = True
    while True:
        print("\n" + "="*60)
        print(f"--> AUTOPILOT: Full NIST AI RMF Security Pipeline{' [DRY RUN MODE]' if is_dry_run else ''}")
        if interval > 0:
            print(f"    (Scheduled Loop Active: Running every {interval} seconds)")
        print("="*60)
        
        # 0. GOVERN
        if not MANIFEST_PATH.exists():
            run_govern(is_autopilot=True, is_dry_run=is_dry_run)
        else:
            if not is_dry_run and first_run:
                # Only ask for rerun on the first loop of a session
                if questionary.confirm("\n[STEP 0]: Existing Manifest detected. Rerun GOVERN?").ask():
                    run_govern(is_autopilot=True, is_dry_run=is_dry_run)
            else:
                if first_run:
                    print("\n[STEP 0]: Dry Run - Skipping GOVERN (Manifest exists).")
                else:
                    print("\n[STEP 0]: Skipping GOVERN for this cycle (Manifest exists).")

        if not MANIFEST_PATH.exists() and not is_dry_run: return

        # 1. MAP
        run_map(is_autopilot=True, is_dry_run=is_dry_run)
        
        # 2. MANAGE
        run_manage(is_autopilot=True, is_dry_run=is_dry_run)
        
        # 3. MEASURE & 4. REPORT
        run_measure(is_autopilot=True, is_dry_run=is_dry_run)

        # 5. REMEDIATE & 6. VERIFY (Fix-Audit-Verify Loop)
        if not is_dry_run:
            from cli.utils import WORKSPACE_DIR
            import json
            summary_path = WORKSPACE_DIR / "reports" / "summary.json"
            if summary_path.exists():
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                
                # Check for adversarial failures or accuracy failures
                metrics = summary.get('metrics', {})
                garak_hits = metrics.get('garak_hits', 0)
                accuracy_val = float(metrics.get('accuracy', '100%').replace('%', ''))
                
                if garak_hits > 0 or accuracy_val < 90:
                    print("\n[AUTOPILOT]: FAILURES DETECTED. Starting Self-Healing Loop...")
                    run_remediate()
                    run_verify()
                else:
                    print("\n[AUTOPILOT]: No critical failures detected. Skipping remediation.")

        if interval <= 0:
            break
        
        first_run = False
        print(f"\n[AUTOPILOT]: Cycle complete. Sleeping for {interval} seconds...")
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[AUTOPILOT]: Scheduled scans terminated by user.")
            break
