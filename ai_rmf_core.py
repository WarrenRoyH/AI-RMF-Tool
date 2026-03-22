import os

# --- Log Suppression (NIST-Ready Silent Mode) ---
# Suppress TensorFlow C++ logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
# Suppress HuggingFace/Transformers logs
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'

import logging
# Configure Python logging to suppress debug noise from external libs
logging.basicConfig(level=logging.ERROR)
logging.getLogger("llm_guard").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

import argparse
import sys
from core.provider import QuotaExceededError

# Import CLI modules
from cli.govern import run_govern
from cli.map import run_map
from cli.manage import run_manage
from cli.measure import run_measure
from cli.remediate import run_remediate
from cli.red_team import run_red_team
from cli.report import run_report
from cli.dashboard import run_dashboard, run_sync
from cli.autopilot import run_autopilot
from cli.health import run_health
from cli.verify import run_verify

def main():
    parser = argparse.ArgumentParser(description="AI-RMF Lifecycle Tools (NIST 1.0)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging for NIST mapping")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("govern")
    subparsers.add_parser("map")
    subparsers.add_parser("manage")
    
    measure_parser = subparsers.add_parser("measure")
    measure_parser.add_argument("--type", choices=["audit", "promptfoo", "garak"], help="Assessment type to run")
    measure_parser.add_argument("--autopilot", action="store_true", help="Run in autopilot mode")
    
    remediate_parser = subparsers.add_parser("remediate")
    remediate_parser.add_argument("--dry-run", action="store_true", help="Suggest patch without applying it")
    
    subparsers.add_parser("red_teamer")
    subparsers.add_parser("dashboard")
    subparsers.add_parser("verify")
    subparsers.add_parser("sync")
    
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--format", choices=["html", "pdf", "bundle"], default="html", help="Report format (default: html)")

    autopilot_parser = subparsers.add_parser("autopilot")
    autopilot_parser.add_argument("--dry-run", action="store_true", help="Run without making external changes or API calls")
    autopilot_parser.add_argument("--interval", type=int, default=0, help="Interval in seconds for periodic scheduled scans (0 = run once)")
    
    subparsers.add_parser("health")

    args = parser.parse_args()
    if args.verbose:
        os.environ["AI_RMF_VERBOSE"] = "true"
        logging.getLogger().setLevel(logging.INFO)

    try:
        if args.command == "govern": run_govern()
        elif args.command == "map": run_map()
        elif args.command == "manage": run_manage()
        elif args.command == "measure": 
            run_measure(is_autopilot=args.autopilot, assessment_type=args.type)
        elif args.command == "remediate": run_remediate(is_dry_run=args.dry_run)
        elif args.command == "red_teamer": run_red_team()
        elif args.command == "report": run_report(report_format=args.format)
        elif args.command == "dashboard": run_dashboard()
        elif args.command == "autopilot": run_autopilot(is_dry_run=args.dry_run, interval=args.interval)
        elif args.command == "health": run_health()
        elif args.command == "verify": run_verify()
        elif args.command == "sync": run_sync()
        else: parser.print_help()
    except QuotaExceededError as e:
        print(f"\n[QUOTA EXCEEDED]: {e}")
        print("Daily reasoning limit reached. Stopping cycle for today.")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\nSession interrupted.")
        sys.exit(0)

if __name__ == "__main__":
    main()
