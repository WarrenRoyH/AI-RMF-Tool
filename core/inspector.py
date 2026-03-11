import os
import subprocess
import time
from pathlib import Path

class Inspector:
    """
    Phase 4: MEASURE (The Inspector)
    Provides continuous monitoring and observability using Arize Phoenix.
    """
    def __init__(self, workspace_dir="workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.log_dir = self.workspace_dir / "logs"
        self.port = 6006 # Default Phoenix port

    def start_observability_server(self):
        """Launches the Arize Phoenix local dashboard."""
        print(f"--> [INSPECTOR]: Launching local observability dashboard on http://localhost:{self.port}...")
        
        # In a real environment, we'd use the phoenix library directly, 
        # but for this CLI we'll simulate the launch.
        try:
            # Check if phoenix is already running
            import requests
            requests.get(f"http://localhost:{self.port}", timeout=1)
            return f"Dashboard is already active at http://localhost:{self.port}"
        except:
            # Launch phoenix as a background process
            # phoenix.launch() would be the internal call
            cmd = ["python3", "-m", "phoenix.server.main", "--port", str(self.port)]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Observability server started. Access it at http://localhost:{self.port}"

    def get_monitoring_status(self):
        """Checks the health of the monitoring logs."""
        log_file = self.log_dir / "sentry_violations.jsonl"
        if not log_file.exists():
            return "Warning: No live traffic logs found. Continuous monitoring is idle."
        
        file_size = log_file.stat().st_size
        return f"Monitoring active. Log size: {file_size / 1024:.2f} KB. Dashboard ready for analysis."

inspector = Inspector()
