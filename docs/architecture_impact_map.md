# Architecture Impact Map

## 1. Sprint S001-2026-03-25: Recursive Jailbreaking & Hylton Portal
**Status**: DESIGN Phase
**Current Impact**:
- `core/jailbreak_engine.py`: `RecursiveJailbreakEngine` implementation.
- `core/remediator.py`: `RuleRegistry` and DSL parser.
- `config/remediation_rules.json`: Rule schema definition.
- `docs/Hylton_Compliance_Portal_Architecture.md`: Blueprint for secure vaulting.

## 2. Phase 21 Implementation Plan: Multi-Modal Remediation
**Goal**: Implement NIST AI RMF **Manage 1.1, 1.2** via dynamic sentry injection and model routing.

### 2.1 Remediation DSL Parser (`core/remediator.py`)
- **Objective**: Implement a high-performance parser for `config/remediation_rules.json`.
- **Architectural Shift**: Transition from static regex filters to a dynamic, multi-vector rule engine.
- **Key Symbols**: `RuleRegistry`, `DSLParser`, `ActionExecutor`.

### 2.2 Dynamic Sentry Injection
- **Objective**: Enable `Sentry` to ingest new rules without downtime.
- **Mechanism**: Use an internal signal or IPC mechanism to notify `Sentry` of rule updates in the `RuleRegistry`.
- **Key Symbols**: `Sentry.update_rules()`, `SignalHandler`.

### 2.3 Dynamic Model Routing (`core/proxy.py`)
- **Objective**: Route requests based on the Risk-Utility-Tradeoff (RUT) score.
- **Mechanism**: If risk > threshold, route to a "High-Safety" model (e.g., Llama-3-Guard) instead of the primary target.
- **Key Symbols**: `Router`, `RUTScoreCalculator`, `PFProvider.get_safe_model()`.

## 3. Phase 22 Implementation Plan: Autonomic "Heal-on-Failure" Loop
**Goal**: Implement NIST AI RMF **Manage 2.1, 2.3** via a closed-loop remediation trigger.

### 3.1 The "Healer" Orchestrator (`core/healer.py`)
- **Objective**: Automate rule generation from audit findings.
- **Mechanism**: Parse `latest_audit_report.md` (LLM-assisted) to identify vulnerabilities and map them to new DSL rules.
- **Key Symbols**: `Healer`, `AuditParser`, `RuleGenerator`.

### 3.2 Closed-Loop Autopilot (`cli/autopilot.py`)
- **Objective**: Orchestrate the `Measure -> Remediate -> Verify` sequence.
- **Mechanism**: A CLI-driven loop that repeats until all P1 vulnerabilities are mitigated and verified.
- **Key Symbols**: `Autopilot.run_healing_cycle()`.

### 3.3 Utility-Aware Verification
- **Objective**: Ensure remediation doesn't break application utility.
- **Mechanism**: Run `core/auditor.py` benchmarks before and after rule application. Rollback if `bert-score` drops > 15%.
- **Key Symbols**: `UtilityGuard`, `BenchmarkRunner`.
