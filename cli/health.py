import subprocess
from cli.utils import WORKSPACE_DIR
from core.provider import provider

def run_health():
    """Verify environment, dependencies, and API connectivity."""
    print("\n" + "="*60)
    print("--> HEALTH CHECK: Environment & Connectivity")
    print("="*60)
    
    # 1. Workspace
    print(f"--> Workspace: {'[OK]' if WORKSPACE_DIR.exists() else '[MISSING]'}")
    
    # 2. Dependencies
    try:
        import llm_guard
        print(f"--> LLM-Guard: [OK]")
    except ImportError:
        print("--> LLM-Guard: [MISSING]")
        
    # Check for external tools
    bwrap = subprocess.run(["which", "bwrap"], capture_output=True, text=True)
    print(f"--> Sandbox (bwrap): {'[OK]' if bwrap.returncode == 0 else '[MISSING]'}")
    
    npx = subprocess.run(["which", "npx"], capture_output=True, text=True)
    if npx.returncode == 0:
        pf_v = subprocess.run(["npx", "--yes", "promptfoo", "--version"], capture_output=True, text=True)
        v_str = pf_v.stdout.strip() if pf_v.returncode == 0 else "N/A"
        print(f"--> Benchmarks (npx/promptfoo): [OK] (v{v_str})")
    else:
        print(f"--> Benchmarks (npx/promptfoo): [MISSING]")

    pip_audit = subprocess.run(["which", "pip-audit"], capture_output=True, text=True)
    if pip_audit.returncode != 0:
        # Check in venv
        pip_audit_venv = WORKSPACE_DIR.parent / ".venv" / "bin" / "pip-audit"
        if pip_audit_venv.exists():
            v_cmd = subprocess.run([str(pip_audit_venv), "--version"], capture_output=True, text=True)
            v_str = v_cmd.stdout.strip() if v_cmd.returncode == 0 else "Venv"
            print(f"--> Supply Chain (pip-audit): [OK] ({v_str})")
        else:
            print(f"--> Supply Chain (pip-audit): [MISSING]")
    else:
        v_cmd = subprocess.run(["pip-audit", "--version"], capture_output=True, text=True)
        v_str = v_cmd.stdout.strip() if v_cmd.returncode == 0 else "OK"
        print(f"--> Supply Chain (pip-audit): [OK] (v{v_str})")

    # Check for Garak version
    garak_venv = WORKSPACE_DIR.parent / ".venv" / "bin" / "python3"
    garak_v = subprocess.run([str(garak_venv), "-m", "garak", "--version"], capture_output=True, text=True)
    if garak_v.returncode == 0:
        print(f"--> Red Teaming (garak): [OK] (v{garak_v.stdout.strip()})")
    else:
        print(f"--> Red Teaming (garak): [MISSING or FAILED]")

    # 3. API Connectivity
    print("--> Testing API Connectivity...")
    try:
        provider.validate_setup()
        print(f"--> API Configuration: [OK]")
    except ValueError as e:
        print(f"--> API Configuration: [FAILED] - {e}")

    try:
        test_msg = [{"role": "user", "content": "Ping"}]
        # Test primary model
        res = provider.chat(test_msg)
        if "API Error" in res or "Error" in res:
            print(f"--> Primary Model ({provider.model}): [FAILED] - {res}")
        else:
            print(f"--> Primary Model ({provider.model}): [OK]")
            
        # Test test model pool
        res_test = provider.chat(test_msg, use_test_model=True)
        if "API Error" in res_test or "Error" in res_test:
            print(f"--> Test Model Pool: [FAILED] - {res_test}")
        else:
            print(f"--> Test Model Pool: [OK]")
    except Exception as e:
        print(f"--> API Connectivity: [CRITICAL ERROR] - {e}")

    print("="*60)
