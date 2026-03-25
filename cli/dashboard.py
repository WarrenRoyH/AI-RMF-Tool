import webbrowser
import os
import json
import uvicorn
import asyncio
import subprocess
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from cli.utils import check_setup
from core.utils import WORKSPACE_DIR, MANIFEST_PATH, LOG_DIR, BASE_DIR

app = FastAPI()

# Global paths
SUMMARY_PATH = WORKSPACE_DIR / "reports" / "summary.json"
INDEX_PATH = BASE_DIR / "index.html"
EXEC_LOG_PATH = LOG_DIR / "ai-rmf.log"

@app.get("/", response_class=HTMLResponse)
async def read_index():
    if not INDEX_PATH.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    with open(INDEX_PATH, "r") as f:
        return f.read()

@app.get("/manifest")
async def get_manifest():
    if not MANIFEST_PATH.exists():
        return {}
    with open(MANIFEST_PATH, 'r') as f:
        return json.load(f)

@app.get("/audit-data")
async def get_audit_data():
    if not SUMMARY_PATH.exists():
        return {}
    with open(SUMMARY_PATH, 'r') as f:
        return json.load(f)

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
        
        LOG_PATH = LOG_DIR / "sentry_violations.jsonl"
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

@app.get("/logs/stream")
async def stream_logs():
    async def log_generator():
        if not EXEC_LOG_PATH.exists():
            yield "data: [SYSTEM] Execution log not found yet.\n\n"
            # Wait for it to be created
            while not EXEC_LOG_PATH.exists():
                await asyncio.sleep(1)
        
        # Open the file and seek to the end or start depending on preference
        # For now, let's just start from the beginning of the current session
        with open(EXEC_LOG_PATH, "r") as f:
            # Optionally seek to the end if you only want new logs: f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                yield f"data: {line}\n\n"

    return StreamingResponse(log_generator(), media_type="text/event-stream")

@app.post("/run/{command}")
async def run_command(command: str):
    allowed_commands = ["govern", "map", "measure", "manage", "autopilot", "verify", "remediate", "health"]
    if command not in allowed_commands:
        raise HTTPException(status_code=400, detail="Command not allowed")
    
    # We run the command as a subprocess using the ai-rmf wrapper
    # This ensures it runs in the same environment and logs to ai-rmf.log
    cmd_list = ["./ai-rmf", command]
    
    # Run in background to not block FastAPI
    try:
        env = os.environ.copy()
        env["AI_RMF_SUBPROCESS"] = "true"
        subprocess.Popen(cmd_list, cwd=str(BASE_DIR), env=env)
        return {"status": "success", "message": f"Command '{command}' started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def get_health_status():
    # Basic connectivity check for the Connectivity Matrix
    # 1. Auditor (API Check)
    # 2. Proxy (Running?)
    # 3. Target (Is proxy reachable?)
    # 4. Vault (Is isolation active?)
    status = {
        "auditor": "online",
        "proxy": "offline",
        "target": "offline",
        "vault": "missing"
    }
    
    # Check Vault Status
    sensitive_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
    has_host = any(os.getenv(f"HOST_{k}") for k in sensitive_keys)
    has_target = any(os.getenv(f"TARGET_{k}") for k in sensitive_keys)
    has_bleed = any(os.getenv(k) for k in sensitive_keys)
    
    identical = False
    for k in sensitive_keys:
        h = os.getenv(f"HOST_{k}")
        t = os.getenv(f"TARGET_{k}")
        if h and t and h == t:
            identical = True
            break

    if has_bleed or identical:
        status["vault"] = "insecure"
    elif has_host and has_target:
        status["vault"] = "online" # We'll use 'online' to match the dot color logic (success)
    else:
        status["vault"] = "missing"

    # Check if proxy is running (port 8000)
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('localhost', 8000)) == 0:
            status["proxy"] = "online"
            status["target"] = "online"
            
    return status

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
    try:
        webbrowser.open("http://localhost:8888")
    except:
        pass
    
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="error")
