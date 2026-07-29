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


def test_agent_definition_exists_and_is_valid_json():
    agent = json.loads((KIRO / "agents" / "spec-validator.json").read_text())

    assert agent["name"] == "spec-validator"
    assert agent["systemPrompt"]


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


def test_execute_bash_is_deny_by_default():
    """The agent must never ship with an unrestricted shell."""
    agent = json.loads((KIRO / "agents" / "spec-validator.json").read_text())
    settings = agent["toolsSettings"]["execute_bash"]

    assert settings["denyByDefault"] is True
    assert settings["allowedCommands"]
    assert settings["deniedCommands"]


def test_destructive_commands_are_denied():
    agent = json.loads((KIRO / "agents" / "spec-validator.json").read_text())
    denied = " ".join(agent["toolsSettings"]["execute_bash"]["deniedCommands"])

    for command in ("rm", "sudo", "curl", "git push"):
        assert command in denied


def test_extractor_commands_are_allowed():
    """The workflow's own extractor commands must remain runnable."""
    agent = json.loads((KIRO / "agents" / "spec-validator.json").read_text())
    allowed = " ".join(agent["toolsSettings"]["execute_bash"]["allowedCommands"])

    assert "extract-api-surface" in allowed
    assert "pip install" in allowed


def test_installer_is_executable():
    install = REPO_ROOT / "install.sh"

    assert install.is_file()
    assert install.stat().st_mode & 0o111, "install.sh must be executable"
