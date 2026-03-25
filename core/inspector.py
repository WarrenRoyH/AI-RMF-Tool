import os
import sys
import subprocess
import time
from pathlib import Path
from core.utils import WORKSPACE_DIR

class Inspector:
    """
    Phase 4: MEASURE (The Inspector)
    Provides continuous monitoring and observability using Arize Phoenix.
    """
    def __init__(self, workspace_dir=None):
        self.workspace_dir = Path(workspace_dir).resolve() if workspace_dir else WORKSPACE_DIR
        self.log_dir = self.workspace_dir / "logs"
        self.port = 6006 # Default Phoenix port

    def start_observability_server(self):
        """Launches the Arize Phoenix local dashboard and configures environment."""
        print(f"--> [INSPECTOR]: Launching unified observability dashboard on http://localhost:{self.port}...")
        
        # Phoenix expects traces on port 6006 by default via OTLP
        os.environ["PHOENIX_PORT"] = str(self.port)
        os.environ["PHOENIX_PROJECT_NAME"] = "ai-rmf-sentry"

        try:
            import requests
            # Check if already running
            requests.get(f"http://localhost:{self.port}", timeout=1)
            return f"Dashboard is already active at http://localhost:{self.port}"
        except:
            # Launch phoenix as a background process using the module runner
            # We use 'phoenix.server.main' which is the standard entry point
            cmd = [sys.executable, "-m", "phoenix.server.main", "serve", "--port", str(self.port)]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for startup
            print("    Waiting for dashboard to initialize (this may take 5-10 seconds)...")
            time.sleep(8)
            return f"Unified Observability server started. Access it at http://localhost:{self.port}"

    def get_monitoring_status(self):
        """Checks the health of the monitoring logs and scan artifacts."""
        status_reports = []
        
        # 1. Phoenix Status
        try:
            import requests
            requests.get(f"http://localhost:{self.port}", timeout=0.5)
            status_reports.append(f"  * Phoenix Dashboard: [ONLINE] (http://localhost:{self.port})")
        except:
            status_reports.append("  * Phoenix Dashboard: [OFFLINE] (Run 'dashboard' to start)")

        # 2. Sentry Traffic
        log_file = self.log_dir / "sentry_violations.jsonl"
        if log_file.exists():
            size = log_file.stat().st_size / 1024
            status_reports.append(f"  * Sentry Violation Logs: [ACTIVE] ({size:.2f} KB)")
        else:
            status_reports.append("  * Sentry Violation Logs: [IDLE] (No violations detected yet)")

        # 2. Garak Scans
        garak_dir = self.workspace_dir / "reports" / "garak"
        if garak_dir.exists():
            scan_count = len(list(garak_dir.glob("*.jsonl")))
            status_reports.append(f"  * Garak Vulnerability Scans: [FOUND] ({scan_count} reports)")
        
        # 3. Promptfoo Evals
        pf_config = self.workspace_dir / "promptfoo_config.json"
        if pf_config.exists():
            status_reports.append(f"  * Accuracy Benchmarks: [CONFIGURED] (Ready for Phoenix import)")

        return "\n".join(status_reports)

inspector = Inspector()
