# Hook: Post-Task Validation

## Trigger

**Event:** `postTaskExecution`

This hook fires automatically after a coding task completes — specifically when the coding agent finishes generating or modifying source code for a feature that has associated specification files.

## Activation Conditions

The hook activates ONLY when ALL of the following are true:

1. The completed task modified source code (not just docs, configs, or tests)
2. Requirements files exist in the project (files matching `**/requirements.md`, `**/requirements/*.md`, or `**/specs/*.md`)
3. The modifications are in a domain that has corresponding requirements

If any condition is not met, the hook exits silently.

> **Note:** A hand-written technical design document is NOT required for activation. The agent ALWAYS generates the technical design by running tree-sitter extraction against the codebase (see `steering/spec-validation/brownfield-discovery.md`). A hand-written `tech.md` / `DESIGN.md`, when present, supplements the extracted signatures with business/semantic intent.

## Workflow

```
┌─────────────────────────────────────┐
│ Coding Agent completes task         │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ Hook: Check activation conditions   │
│ - Source code modified?             │
│ - Requirements files exist?         │
└─────────────────┬───────────────────┘
                  │ (all true)
                  ▼
┌─────────────────────────────────────┐
│ Invoke spec-validator sub-agent     │
│ Inputs:                             │
│   requirementsPath: {detected}      │
│   codebasePath: {detected}          │
│   techDocPath: {detected, optional} │
│   testFramework: auto-detect        │
│   executeTests: true                │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ ALWAYS run tree-sitter extraction   │
│ → generated-tech.md (all signatures)│
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ Sub-agent ALWAYS generates NEW tests│
│ from specs (never sees source code) │
│ — even if tests already exist       │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ Execute generated tests             │
└─────────────────┬───────────────────┘
                  │
          ┌───────┴───────┐
          │               │
     All Pass         Failures
          │               │
          ▼               ▼
┌──────────────┐  ┌──────────────────────┐
│ Report:      │  │ Classify violations  │
│ "Spec-       │  │ Feed to coding agent │
│  compliant"  │  │ Auto-repair cycle    │
└──────────────┘  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Re-execute tests     │
                  │ (max 3 iterations)   │
                  └──────────┬───────────┘
                             │
                     ┌───────┴───────┐
                     │               │
                All Pass         Still Failing
                     │               │
                     ▼               ▼
              ┌────────────┐  ┌────────────────┐
              │ Report:    │  │ Report:        │
              │ "Fixed,    │  │ "Unresolved    │
              │  now spec- │  │  violations —  │
              │  compliant"│  │  human review  │
              └────────────┘  │  required"     │
                              └────────────────┘
```

## File Discovery Logic

```
# Requirements discovery (in priority order):
1. Look for directories named: requirements/, specs/, specifications/
2. Look for files matching: **/requirements.md, **/specs.md
3. Look for files containing REQ-* patterns

# Technical design doc discovery (OPTIONAL — supplements always-run extraction).
# Resolved per requirements file; first match wins; a miss is never an error:
1. Explicit techDocPath, if given and the file exists (if missing: warn, continue)
2. design.md, then tech.md, in the SAME directory as the requirements file
   (Kiro layout: .kiro/specs/<spec-name>/design.md), matched case-insensitively
3. DESIGN.md or tech.md (case-insensitive) in project root, then docs/
4. None found -> brownfield mode for that spec (generated-tech.md only)
# NOTE: tree-sitter extraction ALWAYS runs to produce generated-tech.md,
# whether or not a hand-written design doc is found above.
```

## Output

The hook writes its results to:
- `TestsToSpecCoverage.md` — coverage of specs/requirements by E2E and integration tests
- `spec-validation-violations.md` — failure report (if any)

And reports a summary to the user:

```
✓ Spec Validation: 79 integration + 12 e2e tests generated
✓ Integration test coverage: 85% of testable requirements
✓ End-to-end test coverage: 60% of testable requirements
✓ Combined coverage: 92% of testable requirements
✓ TestsToSpecCoverage.md report generated
✗ 3 violations detected (2 P2, 1 P3) — auto-repairing...
✓ All violations resolved after 1 repair cycle
```
