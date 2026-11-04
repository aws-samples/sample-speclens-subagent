"""Tests that the shipped .kiro subagent assets are present and well-formed."""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
KIRO = REPO_ROOT / ".kiro"

STEERING_DOCS = [
    "brownfield-discovery.md",
    "e2e-workflow-discovery.md",
    "property-test-generation.md",
    "requirements-parsing.md",
    "spec-mutation.md",
    "test-generation-patterns.md",
    "traceability-standards.md",
    "violation-classification.md",
]

HOOKS = [
    "on-demand-validation.kiro.hook",
    "post-task-validation.kiro.hook",
    "spec-code-validation.kiro.hook",
]


def _agent():
    return json.loads((KIRO / "agents" / "spec-validator.json").read_text())


def _shell_allow_patterns():
    rules = _agent()["permissions"]["rules"]
    return [
        pattern
        for rule in rules
        if rule["capability"] == "shell" and rule["effect"] == "allow"
        for pattern in rule.get("match", [])
    ]


def test_agent_definition_exists_and_is_valid_json():
    agent = _agent()

    assert agent["name"] == "spec-validator"
    assert agent["prompt"]


def test_agent_uses_only_fields_supported_by_the_kiro_agent_engine():
    """Kiro refuses to register profiles that carry legacy fields without `permissions`."""
    agent = _agent()

    for legacy in (
        "systemPrompt",
        "toolsSettings",
        "allowedTools",
        "steeringDocs",
        "inputs",
        "outputs",
        "version",
    ):
        assert legacy not in agent, f"legacy field {legacy!r} prevents the agent from loading"
    assert "permissions" in agent


def test_resources_use_relative_file_uris_that_exist():
    """Absolute file:// URIs are rejected; every resource must resolve inside the project."""
    for uri in _agent()["resources"]:
        assert uri.startswith("file://")
        path = uri[len("file://") :]
        assert not path.startswith("/"), f"absolute resource URI: {uri}"
        assert list(REPO_ROOT.glob(path)), f"resource matches no files: {uri}"


@pytest.mark.parametrize("hook_name", HOOKS)
def test_hooks_are_valid_json(hook_name):
    hook = json.loads((KIRO / "hooks" / hook_name).read_text())

    assert "prompt" in hook or "then" in hook


@pytest.mark.parametrize("doc_name", STEERING_DOCS)
def test_steering_docs_are_present_and_non_empty(doc_name):
    doc = KIRO / "steering" / "spec-validation" / doc_name

    assert doc.is_file()
    assert doc.stat().st_size > 0


def test_skill_definition_is_present():
    skill = KIRO / "skills" / "spec-validation-skill.md"

    assert skill.is_file()
    assert skill.stat().st_size > 0


def test_shell_is_restricted_to_an_allowlist():
    """The agent must never ship with an unrestricted shell."""
    patterns = _shell_allow_patterns()

    assert patterns
    assert "*" not in patterns


def test_destructive_commands_are_not_allowed():
    patterns = _shell_allow_patterns()

    for command in ("rm", "sudo", "curl", "wget", "git push", "chmod"):
        assert not any(p == command or p.startswith(command + " ") for p in patterns)


def test_extractor_commands_are_allowed():
    """The workflow's own extractor commands must remain runnable."""
    allowed = " ".join(_shell_allow_patterns())

    assert "extract-api-surface" in allowed
    assert "pip install" in allowed


def test_installer_is_executable():
    install = REPO_ROOT / "install.sh"

    assert install.is_file()
    assert install.stat().st_mode & 0o111, "install.sh must be executable"


def test_agent_resolves_design_doc_next_to_each_requirements_file():
    """Kiro specs keep design.md beside requirements.md; a missing doc must not halt."""
    prompt = _agent()["prompt"]

    assert "Step 0.0: Resolve the Design Document" in prompt
    assert ".kiro/specs/<spec-name>/design.md" in prompt
    assert "case-insensitively" in prompt
    assert "falling back to discovery" in prompt
    assert "| `techDocPath` | no | `DESIGN.md` |" not in prompt


def test_agent_keeps_shell_commands_parseable_by_kiro():
    """Heredocs, pipes and $(...) make Kiro's command parser fail, so rules never match."""
    prompt = _agent()["prompt"]

    assert "## SHELL COMMAND RULES" in prompt
    assert "No heredocs" in prompt
    assert "&& echo 'Extraction complete' ||" not in prompt
