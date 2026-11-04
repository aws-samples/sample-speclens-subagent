# Spec-to-Code Validation SubAgent (SpecLens)

A Kiro subagent distributed as an aws-samples code package that independently validates whether generated code conforms to its specification. It generates executable integration and end-to-end tests solely from requirements and technical design documents — without ever reading source code — then executes those tests against the implementation to detect specification violations.

## Requirements

- Python 3.10 or newer
- `pip` (bundled with Python)
- [`pipx`](https://pipx.pypa.io/) for the recommended global install (`brew install pipx` on macOS)
- A current version of Kiro

## Quick Start: run SpecLens as a Kiro subagent

Run these commands verbatim. Replace only `/path/to/your/target/project` with the
project you want to validate.

**1. Install the extractor CLI and copy the agent into your project:**

```bash
git clone https://github.com/aws-samples/sample-speclens-subagent.git
cd sample-speclens-subagent

pipx install .
pipx ensurepath

export TARGET=/path/to/your/target/project
mkdir -p "$TARGET/.kiro" && cp -R .kiro/. "$TARGET/.kiro/"
```

Open a new terminal after `pipx ensurepath` so the updated `PATH` takes effect.

**2. Check that the CLI resolves from your project:**

```bash
cd /path/to/your/target/project
extract-api-surface --help
```

If you see `command not found`, see [Verifying the installation](#verifying-the-installation).

**3. Open your project in Kiro.** Open the target project folder in Kiro. If it
was already open, quit and restart Kiro so it re-reads `.kiro/agents/`.

**4. Check that Kiro registered the agent:**

```bash
grep "profile load error" "$(ls -d ~/.kiro/logs/*/ | tail -1)kiro.log" | grep spec-validator
```

No output means the agent loaded. Any output means Kiro rejected the profile; see
[Troubleshooting](#troubleshooting-the-agent-is-not-registered).

**5. Run the agent from Kiro chat.** Paste this prompt and edit the paths:

```
Run the spec-validator subagent with these inputs:
- requirementsPath: ./.kiro/specs/payments/requirements.md
- codebasePath: .
- outputDir: ./src/test/
```

Only `requirementsPath` and `codebasePath` are needed. `techDocPath`,
`testFramework`, `outputDir`, `executeTests` and `maxRepairIterations` are
optional; see [Agent inputs](#agent-inputs). You don't need `techDocPath` for Kiro
specs: the agent uses the `design.md` next to each `requirements.md`; see
[How the design document is found](#how-the-design-document-is-found).

> **Large spec sets:** Run one requirements file per invocation. Hundreds of
> SHALL criteria across many specs won't fit in a single agent session. Kiro then
> splits the work into a multi-step workflow instead of running the subagent.

### Troubleshooting: the agent is not registered

If Kiro replies with something like *"spec-validator.json isn't registered with the
workflow engine"* and starts a workflow instead of the subagent, Kiro refused to load
the agent profile. Find the reason:

```bash
grep -h "profile load error" ~/.kiro/logs/*/kiro.log | grep spec-validator | tail -1
```

The most common cause is a `.kiro/agents/spec-validator.json` copied from an older
SpecLens release. That file used fields such as `systemPrompt`, `toolsSettings` and
`steeringDocs`, which current Kiro rejects
(`Agent profile uses fields this agent engine does not support: toolsSettings`).
Fix it by pulling the latest SpecLens and copying the agent profile again:

```bash
cd sample-speclens-subagent
git pull
cp .kiro/agents/spec-validator.json /path/to/your/target/project/.kiro/agents/
```

Then restart Kiro and repeat step 4 above.

If step 4 prints nothing but Kiro still says the agent isn't registered, check
where the profile actually is. It must be at `.kiro/agents/spec-validator.json`.
On macOS, `cp -r .kiro/ "$TARGET"` (note the trailing slash) copies the
*contents* of `.kiro` into the project root, which leaves `agents/`, `hooks/` and
`steering/` there, where Kiro never looks:

```bash
ls "$TARGET/.kiro/agents/spec-validator.json" "$TARGET/agents/spec-validator.json" 2>&1
```

If it's in `$TARGET/agents/`, delete the stray copies and re-copy using the
command in step 1.

## Installation

Setting up SpecLens in the project you want to validate ("your target project")
has **two independent parts**:

1. **Per-project configuration** — copy the `.kiro/` directory *into your target
   project*. Kiro discovers the agent, hooks, and skills from the `.kiro/` in the
   project you have open.
2. **The `extract-api-surface` CLI** — install the `speclens` package into a
   Python environment that is **on `PATH` when Kiro runs commands inside your
   target project**. The agent shells out to `extract-api-surface`, so if the CLI
   is not resolvable from your target project, extraction fails.

> ⚠️ **The most common mistake:** installing the CLI into a virtual environment
> that lives inside the *cloned SpecLens repo*. That venv is not active while you
> work in your target project, so the agent won't find `extract-api-surface`.
> Install the CLI **globally** (Option 1) or **into your target project's own
> environment** (Option 2) instead.

### Option 1: `pipx` — global CLI, works in every project (recommended)

`pipx` installs `extract-api-surface` onto your global `PATH` in an isolated
environment, so it resolves from *any* target project regardless of which venv
that project uses. This is the most robust setup for running the agent in your
target repo.

```bash
git clone https://github.com/aws-samples/sample-speclens-subagent.git
cd sample-speclens-subagent

# Install the CLI globally (isolated; no need to activate anything later)
pipx install .            # or: python3 -m pip install --user .

# Copy the subagent configuration into the project you want to validate
mkdir -p /path/to/your/target/project/.kiro
cp -R .kiro/. /path/to/your/target/project/.kiro/
```

Now, from `/path/to/your/target/project`, `extract-api-surface` is on `PATH` and
the agent can run.

### Option 2: Install into your target project's environment

If your target project uses its own virtual environment (recommended for Python
projects), install the CLI **into that environment** so it is present whenever the
project's venv is active.

```bash
git clone https://github.com/aws-samples/sample-speclens-subagent.git

# Activate YOUR TARGET PROJECT's environment first
cd /path/to/your/target/project
source .venv/bin/activate          # your project's venv, not SpecLens's

# Install the CLI into it, and copy the configuration in
pip install /path/to/sample-speclens-subagent
mkdir -p .kiro && cp -R /path/to/sample-speclens-subagent/.kiro/. .kiro/
```

The CLI is now available whenever this project's venv is active — including when
Kiro runs the agent from within the project.

### Option 3: Install script

The bundled script copies `.kiro/` into the target and installs the CLI into the
**currently active interpreter**. To get a working target-repo setup, activate the
environment you want the CLI in *before* running it — your target project's venv
(Option 2), or none at all for a `--user`/global install.

```bash
git clone https://github.com/aws-samples/sample-speclens-subagent.git
cd sample-speclens-subagent

# Activate the environment the CLI should land in (e.g. your target project's venv),
# then run the installer against your target project:
./install.sh /path/to/your/target/project
```

> On macOS and many Linux distributions the system Python is "externally managed"
> (PEP 668) and `pip install` into it is refused. Use `pipx` (Option 1) or a
> virtual environment (Option 2) rather than `--break-system-packages`.

### Option 4: Development install

To work on the extractor itself, install it in editable mode with the test
dependencies and run the suite:

```bash
git clone https://github.com/aws-samples/sample-speclens-subagent.git
cd sample-speclens-subagent

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
pytest
```

### Verifying the installation

Run this **from your target project directory** (with that project's environment
active, if it uses one) — that is the context the agent runs in:

```bash
cd /path/to/your/target/project
extract-api-surface --help
```

If the command is found here, the agent will be able to invoke it. If it is not
on your `PATH` (for example after a `--user` install), it can always be invoked as
a module:

```bash
python3 -m speclens.cli --help
```

If the command works in the SpecLens clone but *not* in your target project, the
CLI is installed in the wrong environment — see the ⚠️ note above and use Option 1
or Option 2.

### After Installation

The subagent integrates with Kiro through:
- **Agent definition** — `.kiro/agents/spec-validator.json`
- **Hooks** — automatic triggers on file edits and task completion
- **Skills** — `/spec-validate` command for on-demand validation
- **Steering docs** — detailed guidance for requirements parsing, test generation, and violation classification

## How It Works

The subagent enforces a strict **information hiding** principle: it reads only specifications and design documents, never implementation code. This ensures tests represent the specification's intent rather than encoding implementation assumptions.

The subagent **always** generates the technical design by running a bundled tree-sitter extractor over the codebase to produce `generated-tech.md` — this happens in every run, whether or not a hand-written design document is present. It then operates in one of two modes:

- **Greenfield / hybrid** — A hand-written tech doc (DESIGN.md / tech.md) exists. It supplies business/semantic intent, while the tree-sitter–extracted `generated-tech.md` supplies the authoritative, exhaustive signature reference (routes, request/response types, parameters, service interfaces). Where the two disagree on the API surface, the extraction is ground truth.
- **Brownfield** — No hand-written tech doc exists. The tree-sitter `generated-tech.md` is the sole tech document, and a reconciliation report maps each requirement to an endpoint.

```
┌───────────────────────┐     ┌──────────────────────────┐
│  Requirements Files   │     │  Tree-sitter extraction  │
│  (REQ-F-001, etc.)   │     │  (ALWAYS runs)           │
└──────────┬────────────┘     │  → generated-tech.md     │
           │                  │  (+ hand-written tech    │
           │                  │   doc if one exists)     │
           │                  └────────────┬─────────────┘
           └───────────┐   ┌───────────────┘
                       ▼   ▼
            ┌──────────────────────────┐
            │  Spec-Validator Agent    │
            │  (never reads src code)  │
            └──────────────┬───────────┘
                           │
              ┌────────────┼─────────────────┐
              ▼            ▼                  ▼
   ┌────────────────┐  ┌──────────────┐  ┌────────────────┐
   │ Requirement    │  │ State Token  │  │ Ubiquitous Req │
   │ → Endpoint Map │  │ Extraction   │  │ Detection      │
   └───────┬────────┘  └──────┬───────┘  └───────┬────────┘
           │                  ▼                   │
           │         ┌────────────────┐           │
           │         │ Dependency     │           │
           │         │ Graph → Paths  │           │
           │         └───────┬────────┘           │
           ▼                 ▼                    ▼
    ┌──────────────┐ ┌──────────┐ ┌────────────────────┐
    │ Integration  │ │  E2E     │ │ Property Tests     │
    │ Tests        │ │  Tests   │ │ (randomized input) │
    └──────┬───────┘ └────┬─────┘ └──────────┬─────────┘
           │              │                   │
           └──────┬───────┴───────────────────┘
                  │
                  ▼
       ┌──────────────────────┐     ┌────────────────────┐
       │  Spec Mutation       │     │ TestsToSpec        │
       │  (quality gate)      │────▶│ Coverage.md        │
       └──────────┬───────────┘     └────────────────────┘
                  │
                  ▼
       ┌────────────────────┐
       │  Execute Against   │
       │  Implementation    │
       └─────────┬──────────┘
                 │
         ┌───────┴───────┐
         │               │
    All Pass         Failures
         │               │
         ▼               ▼
   ┌──────────┐  ┌──────────────────┐
   │  Spec    │  │ Violation Report │
   │  Compliant│  │ + Auto-Repair   │
   └──────────┘  │ Loop (max 3x)   │
                 └──────────────────┘
```

## Workflow Phases

### Phase 0: Technical Design Generation (always runs)

The agent **always** runs tree-sitter API surface extraction over the codebase to produce `generated-tech.md`, regardless of whether a hand-written design document exists. The extractor uses deterministic AST parsing (no LLM) to discover routes, DTOs, service interfaces, and entities — extracting all signatures needed for test generation, which a hand-written doc may omit or describe out-of-date.

- **Hand-written tech doc exists** → greenfield/hybrid mode: the document supplies business intent, and `generated-tech.md` supplies the authoritative signature reference.
- **No hand-written tech doc** → brownfield mode: `generated-tech.md` is the sole tech document, and a **reconciliation report** maps each requirement to its matched endpoint — if >30% of testable requirements are unmapped, the agent halts and reports the gap.

### Phase 1: Requirements Parsing

The agent scans requirement files and extracts structured behavioral assertions. It supports:

- **EARS format** — "When [trigger], the system shall [response]"
- **User stories** — "As a [role], I want [capability] so that [benefit]"
- **Structured REQ-IDs** — `REQ-F-001`, `REQ-NF-002`, etc.

Each requirement is classified as TESTABLE, UI-ONLY, INFRASTRUCTURE, or AMBIGUOUS.

### Phase 2: Technical Design Document Analysis

The agent reads the technical design document to extract:

- API contracts (endpoints, HTTP methods, request/response schemas)
- Entity schemas (field names, types, constraints)
- Authentication/authorization model
- Seed data for test fixtures
- Error response formats and exact error messages

### Phase 3: E2E Workflow Discovery

Rather than manually composing end-to-end tests, the agent automatically discovers workflow paths by building a **requirement dependency graph**:

1. **Extract state tokens** — For each requirement, identify postconditions (states it produces) and preconditions (states it requires). State tokens are normalized to `STATE:{entity}_{condition}` form.

2. **Build a directed graph** — An edge from REQ-A → REQ-B exists when REQ-A's postcondition satisfies REQ-B's precondition. Additional edges come from explicit sequencing references, shared-resource create→use patterns, and auth dependencies.

3. **Extract maximal paths** — DFS from source nodes (no incoming edges) to sink nodes (no outgoing edges). Paths are filtered to 3–8 requirements and ranked by coverage value with bonuses for cross-domain span and P1-severity requirements.

4. **Merge overlapping prefixes** — Paths sharing a common prefix of ≥2 requirements share a test fixture and branch into separate assertions.

5. **Handle cycles** — Detected via back-edge detection and converted into dedicated state-machine tests.

### Phase 4: Test Generation

The agent **always generates new tests**, even when the repository already contains a test suite — the presence of existing tests is never a reason to skip generation, since those tests may encode implementation assumptions or fail to trace to requirements. Generation prioritizes **end-to-end and integration tests**, and generated tests are written to a namespaced subfolder of the output directory so they never overwrite pre-existing tests.

Three categories of tests are generated:

| Type | Purpose | Naming Convention |
|------|---------|-------------------|
| Integration Tests | Per-endpoint coverage (happy path, validation errors, auth failures, boundaries) | `{Resource}ControllerIntegrationTest` |
| End-to-End Tests | Cross-domain workflows from discovered dependency paths | `EndToEnd{Workflow}FlowTest` |
| Property Tests | Invariant verification via randomized inputs (ubiquitous requirements only) | `{Resource}PropertyTest` |

Every test method is instrumented with:
1. The requirement ID(s) it covers
2. A description of what behavior it exercises

#### Property-Based Tests

For requirements using the **Ubiquitous EARS pattern** ("The system shall [X]") that declare invariants over a quantifiable property, property-based tests are generated in addition to example-based tests. These exercise the invariant across randomized, bounded inputs to prove universality.

Six property categories are supported:

| Category | Requirement Pattern | Example |
|----------|-------------------|---------|
| Format Invariants | "shall [format/constrain] [field] to [constraint]" | Timestamps ≤ 26 chars |
| Boundary Invariants | "shall [reject/accept] [outside/within] [boundary]" | Amount > 0 |
| Idempotency | "shall [produce same result] on repeated calls" | GET returns identical results |
| Data Integrity | "shall [preserve/maintain] [data relationship]" | Balance constant across transfers |
| Ordering | "shall [order/sort] [resource] by [criteria]" | Transactions in reverse chronological order |
| Security | "shall [never/always] [security constraint]" | Never expose password hashes |

Generators are derived from the tech.md schema, and failing inputs are shrunk to minimal reproducing cases. Default trial count is 100 per property (configurable up to 1000+ for known flaky areas).

### Phase 5: Spec Mutation (Quality Gate)

Spec mutation validates whether generated tests are genuinely tied to the requirements they claim to cover. For E2E tests claiming 3+ REQ-IDs and any test with status-code-only assertions:

1. Mutate one requirement at a time (outcome inversion, boundary shift, status code substitution, side-effect removal, role change)
2. Regenerate the test from the mutated spec
3. Diff original vs. regenerated — score as KILLED (real coverage) or SURVIVED (vacuous)
4. Tests scoring SURVIVED get remediation hints and are re-generated with missing assertions

### Phase 6: Coverage Report

A `TestsToSpecCoverage.md` report maps every requirement to its covering tests, showing:
- Integration test coverage percentage
- End-to-end test coverage percentage
- Property test coverage (invariant type, trial count, pass/fail, shrunk counterexamples)
- Combined coverage matrix
- Spec mutation analysis (KILLED vs SURVIVED per requirement)
- Workflow discovery summary (dependency graph stats, discovered paths, cross-domain workflows)
- Uncovered requirements with explanations

### Phase 7: Execution and Violation Reporting

Tests run against the implementation. Failures are classified by severity:

| Severity | Label | Definition |
|----------|-------|------------|
| P1 | Critical | Data loss, corruption, or security vulnerability |
| P2 | High | Incorrect functional behavior visible to users |
| P3 | Medium | Degraded experience, cosmetic logic errors |
| P4 | Low | Non-functional deviation |

Violation categories include: Data Integrity, Behavioral, Security, Boundary, State Management, Vacuous Coverage, and Infrastructure/Configuration.

### Phase 8: Auto-Repair Loop

If violations are found, the structured violation report is fed back to the coding agent. The coding agent fixes the violating code, tests re-run, and the cycle repeats up to 3 times.

## Package Structure

```
sample-speclens-subagent/
├── pyproject.toml                          # Package config, deps, console script, tooling
├── .flake8                                 # flake8 config (it cannot read pyproject.toml)
├── install.sh                              # One-step installer for target projects
├── .kiro/                                  # Subagent configuration copied into your project
│   ├── agents/
│   │   └── spec-validator.json             # Agent profile (prompt, tools, resources, permissions)
│   ├── hooks/
│   │   ├── spec-code-validation.kiro.hook  # Auto-triggers on src/main/**/*.java edits
│   │   ├── post-task-validation.kiro.hook  # Fires after coding tasks complete
│   │   ├── on-demand-validation.kiro.hook  # User-triggered validation
│   │   ├── post-task-validation.md         # Post-task hook documentation
│   │   └── on-demand-validation.md         # On-demand hook documentation
│   ├── skills/
│   │   └── spec-validation-skill.md        # Skill activation patterns and workflow
│   └── steering/
│       └── spec-validation/
│           ├── requirements-parsing.md     # How to parse requirements into assertions
│           ├── test-generation-patterns.md # Test architecture and quality standards
│           ├── traceability-standards.md   # Annotation format, coverage report structure
│           ├── violation-classification.md # Severity taxonomy and auto-repair hints
│           ├── spec-mutation.md            # Mutation testing for coverage verification
│           ├── brownfield-discovery.md     # Tree-sitter extraction workflow
│           ├── property-test-generation.md # PBT for ubiquitous EARS invariants
│           └── e2e-workflow-discovery.md   # Automated E2E path discovery algorithm
├── src/
│   └── speclens/                           # Tree-sitter API surface extractor package
│       ├── __init__.py                     # Public API: Scanner, format_tech_md, format_yaml
│       ├── cli.py                          # CLI: extract-api-surface <path> --output <file>
│       ├── core.py                         # Data models (Endpoint, TypeDefinition, etc.)
│       ├── scanner.py                      # File discovery and orchestration
│       ├── formatter.py                    # Markdown and YAML output formatters
│       ├── java_extractor.py               # Spring Boot: @GetMapping, @RequestBody, etc.
│       ├── python_extractor.py             # FastAPI/Flask/Django: decorators, Pydantic models
│       ├── typescript_extractor.py         # Express/NestJS: router calls, @Controller
│       ├── go_extractor.py                 # Gin/Chi/Echo: router.GET, struct tags
│       └── py.typed                        # PEP 561 typing marker
├── tests/                                  # Pytest suite for the extractor
│   ├── conftest.py                         # Shared extractor fixtures and helpers
│   ├── test_java_extractor.py
│   ├── test_python_extractor.py
│   ├── test_typescript_extractor.py
│   ├── test_go_extractor.py
│   ├── test_scanner.py                     # Discovery, filtering, error isolation
│   ├── test_formatter.py                   # tech.md and YAML rendering
│   ├── test_cli.py                         # extract-api-surface entry point
│   └── test_package_assets.py              # .kiro config validity and shell allowlist
├── examples/
│   ├── DESIGN.md                           # Example technical design document (CardDemo)
│   └── prompt.md                           # Example invocation prompt
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE
└── README.md                               # This file
```

The Python package lives under `src/speclens/` and installs as `speclens`,
exposing the `extract-api-surface` console script declared in `pyproject.toml`.

## Running the Tests

```bash
pip install -e ".[dev]"
pytest
```

With a coverage report:

```bash
pytest --cov=speclens --cov-report=term-missing
```

The `dev` extra also installs the linters and formatters used by this project:

```bash
black src tests            # formatting (line length 100)
isort src tests            # import ordering
flake8 src tests           # style and unused-name checks
mypy src                   # type checking
```

`black`, `isort`, and `mypy` read their settings from `pyproject.toml`; `flake8`
cannot read `pyproject.toml`, so its configuration lives in `.flake8`.

## Trigger Mechanisms

### 1. Automatic (File Edit Hook)

The `.kiro.hook` triggers automatically when any Java source file in `src/main/java/` is edited. The agent runs the spec validation tests and reports violations inline.

### 2. Automatic (Post-Task)

After a coding agent completes a task that modified source code, the hook checks whether requirements and a tech doc exist, then invokes the subagent automatically. If no tech doc exists, it runs brownfield extraction first.

### 3. On-Demand

Users explicitly invoke validation with options:

```
/spec-validate
/spec-validate --specs ./path/to/requirements --tech ./DESIGN.md
/spec-validate --framework junit5 --output ./src/test/
/spec-validate --no-exec          # Generate tests only, skip execution
/spec-validate --no-repair        # Skip the auto-repair loop
```

## Shell Command Restrictions

The agent needs `execute_bash` to install the extractor, run the API surface
extractor, and execute generated test suites. Shell access is controlled by the
`permissions` block in `.kiro/agents/spec-validator.json`:

- `policies: ["read-only-shell"]` lets read-only commands run without asking.
- A `shell` rule with `"effect": "allow"` lists the only commands that run
  without approval: the extractor install/run (`pip install` of this repository or
  `speclens`, `extract-api-surface ...`), test runners (`pytest`, `mvn`/`mvnw`,
  `gradle`/`gradlew`, `npm`/`npx`/`jest`/`yarn`/`pnpm`, `go test`, `dotnet test`)
  and inspection commands (`ls`, `cat`, `grep`, `find`, `test`, `echo`, `which`).
- Kiro asks for your approval before any other command runs. Destructive and
  network commands such as `rm`, `sudo`, `curl`, `wget`, `ssh`, `chmod` and
  `git push` are not on the allowlist.

Patterns are globs (`*` matches any text), not regular expressions. To support
another build tool or test runner, add a pattern to the `shell` rule's `match`
list. Don't replace the list with `*`. `tests/test_package_assets.py` fails if
the allowlist is removed or includes a destructive command.

> Current Kiro rejects the older `toolsSettings` / `allowedTools` fields in this
> profile, and then won't register the agent. Use `permissions` only.

## API Surface Extractor (Brownfield Tool)

The bundled tree-sitter extractor — the `speclens` package under `src/speclens/` — provides deterministic, exhaustive API surface discovery without requiring an LLM.

### Installation

The extractor ships with the same `speclens` package installed in the
[Installation](#installation) section above — if you followed those steps, the
`extract-api-surface` CLI is already available. To install *only* the extractor
(without the `.kiro/` agent configuration), install the package into an
environment on your `PATH`:

```bash
# From the repository root — prefer pipx for a global CLI, or a venv
pipx install .        # or: pip install .  (into the active venv)
```

### Usage

```bash
# Standard extraction (surface-pattern files only)
extract-api-surface /path/to/codebase --output /path/to/codebase/generated-tech.md

# Full scan (unconventional file names)
extract-api-surface /path/to/codebase --scan-all --output generated-tech.md

# YAML output for programmatic consumption
extract-api-surface /path/to/codebase --format yaml --output surface.yaml
```

### Supported Frameworks

| Language | Frameworks | Detection Signals |
|----------|-----------|-------------------|
| Java | Spring Boot | `@GetMapping`, `@PostMapping`, `@RequestBody`, `@Entity` |
| Python | FastAPI, Flask, Django REST | `@app.get()`, `@router.post()`, `BaseModel`, `Serializer` |
| TypeScript | Express, NestJS, Hono | `app.get()`, `@Controller`, `@Get()`, interfaces |
| Go | Gin, Chi, Echo, net/http | `r.GET()`, `r.Get()`, `http.HandleFunc`, struct tags |

### What It Extracts

- **Endpoints** — HTTP method, path, handler name, file location, parameters, request/response types, auth requirements
- **Type definitions** — DTOs, entities, request/response classes with field names, types, and constraints
- **Service interfaces** — Method signatures with parameters and return types

### Surface Pattern Filtering

By default, only files matching API-surface naming conventions are scanned (e.g., `*Controller.java`, `*routes.py`, `*.controller.ts`, `*handler*.go`). Use `--scan-all` to scan every source file.

## Example Invocation

Worked examples live in `examples/`: `examples/DESIGN.md` is a sample technical
design document (CardDemo) and `examples/prompt.md` is a sample invocation prompt.
The paths below refer to files in *your* project, not in this repository.

### How the design document is found

The design document is optional. For each requirements file, the agent uses the
first match below. If nothing matches, that spec runs in brownfield mode from
`generated-tech.md` alone.

1. `techDocPath`, if you pass it and the file exists. If it doesn't exist, the
   agent logs a warning and moves on to rule 2.
2. `design.md`, then `tech.md`, in the same folder as the requirements file. This
   is the standard Kiro layout:
   ```
   .kiro/specs/<spec-name>/requirements.md
   .kiro/specs/<spec-name>/design.md
   ```
   Case doesn't matter (`design.md`, `DESIGN.md`).
3. `DESIGN.md` or `tech.md` in the project root, then in `docs/`.

A spec's own `design.md` always beats a project-level one. When one run covers
several specs, each spec is paired with its own design document. The chosen
document for each spec is listed in `TestsToSpecCoverage.md`.

### Agent inputs

The agent reads its inputs from your chat message. Write them as `name: value` lines.

| Input | Required | Default | Meaning |
|---|---|---|---|
| `requirementsPath` | yes | discovers `**/requirements.md` | Requirements directory, file, or glob |
| `codebasePath` | yes | `.` | Root of the codebase to validate (tree-sitter extraction runs here) |
| `techDocPath` | no | auto-resolved per spec | Optional hand-written design doc. Overrides discovery when the file exists |
| `testFramework` | no | `auto-detect` | `auto-detect`, `junit5`, `pytest`, `jest`, `go-test`, or `xunit` |
| `outputDir` | no | `src/test/` | Where generated tests and reports are written |
| `executeTests` | no | `true` | Run the generated tests after generating them |
| `maxRepairIterations` | no | `3` | Maximum auto-repair cycles |

### Example prompts

To trigger the spec-validator subagent in Kiro:

```
Run the spec-validator agent against my requirements in requirements/ and design doc at DESIGN.md
```

For a detailed invocation with explicit parameters:

```
Run the spec-validator agent with these inputs:
- requirementsPath: ./requirements/
- codebasePath: ./src/
- techDocPath: ./DESIGN.md
- testFramework: junit5
- outputDir: ./src/test/java/
- executeTests: true
- maxRepairIterations: 3

Generate integration and end-to-end tests from the specifications only (do not read source code),
execute them against the implementation, classify any failures by severity, and produce:
1. The generated test files
2. A TestsToSpecCoverage.md report showing requirement-to-test traceability
3. A spec-validation-violations.md report if any tests fail
```

For brownfield codebases (no tech doc):

```
Run the spec-validator agent with these inputs:
- requirementsPath: ./requirements/
- codebasePath: ./my-legacy-app/
- testFramework: auto-detect
- executeTests: true

The codebase has no tech.md — use brownfield mode to extract the API surface first.
```

## Key Design Principles

1. **Spec is ground truth** — If a test fails, the implementation is wrong. Tests are never weakened to match observed behavior.

2. **Information hiding** — The validation agent never reads source code. It operates exclusively from requirements and the technical design document.

3. **Determinism for discovery, LLM for synthesis** — API surface extraction uses tree-sitter (exhaustive, deterministic). LLMs are only used to format and enrich the extracted data, never to discover endpoints.

4. **Observable behavior only** — Tests exercise externally observable behavior through documented interfaces (APIs, CLI, events). Internal implementation details are never tested.

5. **Test independence** — Every test is independently runnable with no ordering dependencies.

6. **Meaningful assertions** — Tests verify semantic correctness (field values, relationships, side effects), not just HTTP status codes. Spec mutation validates this.

7. **Algorithmic workflow composition** — E2E tests are discovered via graph algorithms over requirement dependencies, not hand-composed. This ensures complete coverage of cross-domain paths that a human might miss.

8. **Universality for invariants** — Ubiquitous requirements are tested with property-based testing (randomized bounded inputs), not just fixed examples. A passing property test provides stronger evidence than any finite set of examples.

## Supported Test Frameworks

The agent auto-detects the framework from project files, or accepts explicit specification:

| Framework | Detection Signal | Property Testing Library |
|-----------|-----------------|--------------------------|
| JUnit 5 | `pom.xml` present | jqwik |
| pytest | `requirements.txt` or `pyproject.toml` present | Hypothesis |
| Jest | `package.json` present | fast-check |
| Go test | `go.mod` present | rapid |
| xUnit | `.csproj` present | FsCheck |

## Output Files

| File | Description |
|------|-------------|
| `TestsToSpecCoverage.md` | Full traceability matrix: requirements → tests (E2E + integration), spec mutation verdicts |
| `spec-validation-violations.md` | Classified failures with severity, root cause, and repair hints |
| `generated-tech.md` | Extracted API surface (brownfield only) |
| `reconciliation-report.md` | REQ-ID → endpoint mapping status (brownfield only) |
| Generated test files | Executable tests in `src/test/` (or configured output directory) |

## Coverage Status Taxonomy

| Status | Meaning |
|--------|---------|
| COVERED | Test validates this requirement (confirmed by mutation kill) |
| VACUOUS | Test claims coverage but spec mutation survived — assertions don't exercise the requirement |
| UNCOVERED | Testable requirement but no test generated |
| UI-ONLY | Requirement is UI-specific; cannot test via API |
| INFRA | Infrastructure/deployment requirement; out of scope |
| AMBIGUOUS | Requirement unclear; test generated with restrictive interpretation |
| DEFERRED | Depends on external system not available in test env |


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

