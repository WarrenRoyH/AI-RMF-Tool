---
name: ai-rmf-optimizer
description: Autonomous loop for testing, designing, coding, and integrating improvements into the AI-RMF-Tools project. Use this skill to execute a continuous improvement cycle that ensures code stability via automated testing and Git-based recovery.
---

# AI-RMF-Optimizer Workflow

This skill implements a four-phase autonomous improvement cycle.

## Phase 1: Testing & Baselining
1.  **Identify Entry Points**: Locate test suites or execution scripts (e.g., `bootstrap.sh`, `pytest`, or manual verification scripts).
2.  **Establish Baseline**: Run all existing tests. If any fail, the cycle must prioritize fixing existing regressions before proceeding.
3.  **Snapshot State**: Ensure the Git working directory is clean or documented (`git status`).

## Phase 2: Design Improvements
1.  **Analyze Feedback**: Review test results, `TODO` comments, and architecture patterns.
2.  **Architectural Alignment**: Propose changes that align with existing modular patterns (e.g., `core/`, `librarian/`).
3.  **UX & Accessibility First**: Actively seek ways to make the toolkit more intuitive for non-technical users. Prioritize plain-language outputs, interactive/zero-friction setup, and hiding complex technical hurdles behind intelligent defaults.
4.  **Risk Assessment**: Identify components that are high-risk for breakage.

## Phase 3: Code Development
1.  **Incremental Edits**: Apply changes using surgical tools (`replace`, `write_file`).
2.  **Local Validation**: Run tests specifically for the modified module immediately after editing.
3.  **Refactor with Caution**: Do not introduce new dependencies without verifying their availability in the environment.

## Phase 4: Integration & Versioning
1.  **Full Test Suite**: Run the comprehensive test suite to ensure no global regressions.
2.  **Git Checkpoint**:
    *   If tests pass: Commit with a descriptive message (`feat: ...`, `fix: ...`).
    *   If tests fail and cannot be fixed quickly: Roll back using `git restore .` or `git checkout HEAD -- <file>` to return to the last trusted state.
3.  **Documentation**: Update `README.md` or internal logs if the improvement introduces new capabilities.

## Safety & Continuity
*   **YOLO Mode**: This skill assumes `--approval-mode=yolo` for autonomous execution.
*   **Quota Management**: If an API quota error occurs, the process will naturally terminate. Ensure the last action was a Git checkpoint to avoid losing work.
*   **Loop Condition**: Continue this cycle until no further immediate improvements are identified or external limits are reached.
