import webbrowser
import os
import json
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from cli.utils import check_setup
from core.inspector import inspector

app = FastAPI()

# Global paths
BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR / "workspace"
MANIFEST_PATH = WORKSPACE_DIR / "project-manifest.json"
SUMMARY_PATH = WORKSPACE_DIR / "reports" / "summary.json"
INDEX_PATH = BASE_DIR / "index.html"

@app.get("/", response_class=HTMLResponse)
async def read_index():
    if not INDEX_PATH.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    with open(INDEX_PATH, "r") as f:
        return f.read()

@app.post("/sync")
async def sync_manifest(request: Request):
    try:
        updated_manifest = await request.json()
        
        # 1. Update project-manifest.json
        with open(MANIFEST_PATH, 'w') as f:
            json.dump(updated_manifest, f, indent=2)
        
        # 2. Update index.html via run_sync to maintain parity
        run_sync()
        
        return {"status": "success", "message": "Manifest updated and synchronized."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/violations")
async def get_violations():
    LOG_PATH = WORKSPACE_DIR / "logs" / "sentry_violations.jsonl"
    violations = []
    if LOG_PATH.exists():
        with open(LOG_PATH, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("status") == "pending":
                        violations.append(entry)
                except: continue
    return violations

@app.post("/sentry_action")
async def sentry_action(request: Request):
    try:
        data = await request.json()
        index = data.get("index")
        action = data.get("action")
        
        LOG_PATH = WORKSPACE_DIR / "logs" / "sentry_violations.jsonl"
        if not LOG_PATH.exists(): return {"status": "error", "message": "Log not found"}
        
        lines = []
        with open(LOG_PATH, 'r') as f:
            lines = f.readlines()
        
        # Find the Nth pending violation
        pending_count = 0
        target_line_idx = -1
        for i, line in enumerate(lines):
            entry = json.loads(line)
            if entry.get("status") == "pending":
                if pending_count == index:
                    target_line_idx = i
                    break
                pending_count += 1
        
        if target_line_idx != -1:
            entry = json.loads(lines[target_line_idx])
            entry["status"] = "killed" if action == "kill" else "allowed"
            entry["resolved_at"] = __import__("datetime").datetime.now().isoformat()
            lines[target_line_idx] = json.dumps(entry) + "\n"
            
            with open(LOG_PATH, 'w') as f:
                f.writelines(lines)
            
            return {"status": "success"}
        return {"status": "error", "message": "Violation not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_sync():
    """Manually synchronizes the workspace state with the GUI (index.html)."""
    check_setup()
    print("\n" + "="*60)
    print("--> Phase 9: SYNC (Universal Interface Synchronization)")
    print("="*60)
    
    if not INDEX_PATH.exists():
        print("[!] Error: index.html not found.")
        return

    # Load latest data
    manifest = {}
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f: manifest = json.load(f)
    
    summary = {}
    if SUMMARY_PATH.exists():
        with open(SUMMARY_PATH, 'r') as f: summary = json.load(f)

    # Perform synchronization
    try:
        with open(INDEX_PATH, 'r') as f: content = f.read()
        
        # Sync Audit Data
        if "const LATEST_AUDIT_DATA = " in content:
            parts = content.split("const LATEST_AUDIT_DATA = ")
            rest = parts[1].split(";", 1)
            if len(rest) > 1:
                content = parts[0] + "const LATEST_AUDIT_DATA = " + json.dumps(summary) + ";" + rest[1]
        
        # Sync Project Manifest
        if "const PROJECT_MANIFEST = " in content:
            parts = content.split("const PROJECT_MANIFEST = ")
            rest = parts[1].split(";", 1)
            if len(rest) > 1:
                content = parts[0] + "const PROJECT_MANIFEST = " + json.dumps(manifest) + ";" + rest[1]
        
        with open(INDEX_PATH, 'w') as f: f.write(content)
        print("--> [SYNC]: GUI (index.html) updated with latest workspace state.")
    except Exception as e:
        print(f"[!] Sync failed: {e}")

def run_dashboard():
    check_setup()
    print("\n" + "="*60)
    print("--> Phase 10: DASHBOARD (Interactive Remediation)")
    print("="*60)
    
    # First, ensure index is synced
    run_sync()
    
    print("--> [STARTING]: Interactive Dashboard Server on http://localhost:8888")
    print("--> [HINT]: Use the 'Safety Policy Editor' in the UI to push changes back to the CLI.")
    
    # Open browser in a separate thread/process or just before starting uvicorn
    webbrowser.open("http://localhost:8888")
    
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="error")
