import questionary
from cli.utils import check_setup, MANIFEST_PATH
from cli.govern import run_govern
from cli.map import run_map
from cli.manage import run_manage
from cli.measure import run_measure

def run_autopilot(is_dry_run=False):
    check_setup()
    print("\n" + "="*60)
    print(f"--> AUTOPILOT: Full NIST AI RMF Security Pipeline{' [DRY RUN MODE]' if is_dry_run else ''}")
    print("="*60)
    
    # 0. GOVERN
    if not MANIFEST_PATH.exists():
        run_govern(is_autopilot=True, is_dry_run=is_dry_run)
    else:
        if not is_dry_run:
            if questionary.confirm("\n[STEP 0]: Existing Manifest detected. Rerun GOVERN?").ask():
                run_govern(is_autopilot=True, is_dry_run=is_dry_run)
        else:
            print("\n[STEP 0]: Dry Run - Skipping GOVERN (Manifest exists).")

    if not MANIFEST_PATH.exists() and not is_dry_run: return

    # 1. MAP
    run_map(is_autopilot=True, is_dry_run=is_dry_run)
    
    # 2. MANAGE
    run_manage(is_autopilot=True, is_dry_run=is_dry_run)
    
    # 3. MEASURE & 4. REPORT
    run_measure(is_autopilot=True, is_dry_run=is_dry_run)
