# AI-RMF-Optimizer Roadmap

This file tracks the long-term goals and progress of the AI-RMF-Tools project. The optimizer picks the next available task in each cycle.

## Phase 1: Core Stability & Infrastructure
- [x] Establish a `pytest` suite for the `core/` modules (discovery, auditor, etc.).
- [x] Implement robust error handling in `ai_rmf_core.py` for missing API keys.
- [x] Refactor `ai_rmf_core.py` to move CLI logic into a dedicated `cli/` folder.

## Phase 2: Feature Parity & UI
- [x] Implement the `measure` subcommand functionality (currently a placeholder).
- [x] Synchronize `index.html` with the `workspace/project-manifest.json` for live status.
- [x] Add a "Dry Run" mode to `./ai-rmf autopilot`.

## Phase 3: Advanced Guardrails
- [x] Integrate `llm-guard` more deeply into the `sentry.py` module.
- [x] Add support for local `Ollama` model verification in `discovery.py`.

## Phase 4: Autonomous Red Teaming & Remediation
- [x] Implement automated execution of Red Teamer's `garak` or `promptfoo` plans.
- [x] Implement automatic application of remediation patches to the `project-manifest.json` safety policy.
- [x] Create a `report` subcommand to aggregate all findings into a single PDF or HTML report.

## Phase 5: Observability & Continuous Monitoring
- [x] Fully integrate `Arize Phoenix` with `Sentry` for trace-level monitoring (NIST MA-1).
- [x] Implement a `dashboard` CLI command to launch the `index.html` UI or Phoenix dashboard.
- [x] Add `autopilot` support for periodic scheduled scans (e.g., via `cron` or internal loop).

## Phase 6: Comprehensive Verification & Hardening
- [x] Add `test_autopilot.py` for scheduled scans verification.
- [x] Add `test_inspector.py` for observability verification.
- [x] Implement automated regression testing in `bootstrap.sh`.

## Completed Tasks
- [x] Initial project structure and `bootstrap.sh`.
- [x] Basic `govern` subcommand flow.
- [x] AI-RMF-Optimizer Skill integration.
