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
    print(f"--> Benchmarks (npx/promptfoo): {'[OK]' if npx.returncode == 0 else '[MISSING]'}")

    pip_audit = subprocess.run(["which", "pip-audit"], capture_output=True, text=True)
    if pip_audit.returncode != 0:
        # Check in venv
        pip_audit_venv = WORKSPACE_DIR.parent / ".venv" / "bin" / "pip-audit"
        if pip_audit_venv.exists():
            print(f"--> Supply Chain (pip-audit): [OK] (Venv)")
        else:
            print(f"--> Supply Chain (pip-audit): [MISSING]")
    else:
        print(f"--> Supply Chain (pip-audit): [OK]")

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
