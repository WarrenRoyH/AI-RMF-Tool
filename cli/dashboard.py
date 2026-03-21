import webbrowser
import os
from pathlib import Path
from cli.utils import check_setup
from core.inspector import inspector

def run_dashboard():
    check_setup()
    print("\n" + "="*60)
    print("--> Phase 5: OBSERVABILITY (The Dashboard)")
    print("="*60)
    
    # 1. Start Arize Phoenix in the background
    res = inspector.start_observability_server()
    print(f"--> [INSPECTOR]: {res}")
    
    # 2. Check for the local index.html
    base_dir = Path(__file__).resolve().parent.parent
    index_path = base_dir / "index.html"
    
    if index_path.exists():
        print(f"\n[STEP 1]: Launching Unified AI-RMF Dashboard...")
        webbrowser.open(f"file://{index_path.resolve()}")
    else:
        print(f"\n[!] Error: Dashboard index.html not found.")

    print("\n[INFO]: Keeping the Phoenix server active. Press Ctrl+C to stop this session.")
    print("        (The dashboard will remain open in your browser)")
