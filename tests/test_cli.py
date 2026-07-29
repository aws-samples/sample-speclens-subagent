"""Tests for the `extract-api-surface` command line entry point."""

from pathlib import Path

import pytest
import yaml

from speclens.cli import main

CONTROLLER = """
package com.example;

@RestController
@RequestMapping("/api/orders")
public class OrderController {
    @GetMapping("/{id}")
    public OrderResponse getOrder(@PathVariable String id) { return null; }
}
"""


@pytest.fixture
def codebase(tmp_path: Path) -> Path:
    root = tmp_path / "app"
    root.mkdir()
    (root / "OrderController.java").write_text(CONTROLLER)
    return root


def run_cli(monkeypatch, argv: list[str]) -> None:
    monkeypatch.setattr("sys.argv", ["extract-api-surface", *argv])
    main()


def test_writes_markdown_to_requested_output_path(monkeypatch, codebase, tmp_path):
    out = tmp_path / "generated-tech.md"

    run_cli(monkeypatch, [str(codebase), "--output", str(out)])

    assert out.is_file()
    assert "#### GET `/api/orders/{id}`" in out.read_text()


def test_project_name_defaults_to_directory_name(monkeypatch, codebase, tmp_path):
    out = tmp_path / "tech.md"

    run_cli(monkeypatch, [str(codebase), "--output", str(out)])

    assert out.read_text().startswith("# app — Extracted API Surface")


def test_project_name_override_is_used_in_header(monkeypatch, codebase, tmp_path):
    out = tmp_path / "tech.md"

    run_cli(monkeypatch, [str(codebase), "--output", str(out), "--project-name", "CardDemo"])

    assert out.read_text().startswith("# CardDemo — Extracted API Surface")


def test_yaml_format_emits_parseable_yaml(monkeypatch, codebase, tmp_path):
    out = tmp_path / "surface.yaml"

    run_cli(monkeypatch, [str(codebase), "--output", str(out), "--format", "yaml"])

    data = yaml.safe_load(out.read_text())
    assert data["endpoints"][0]["path"] == "/api/orders/{id}"


def test_scan_all_picks_up_non_surface_filenames(monkeypatch, tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    (root / "Helpers.java").write_text(CONTROLLER)
    out = tmp_path / "tech.md"

    run_cli(monkeypatch, [str(root), "--output", str(out), "--scan-all"])

    assert "/api/orders/{id}" in out.read_text()


def test_summary_is_written_to_stderr_not_stdout(monkeypatch, codebase, tmp_path, capsys):
    """The report goes to a file; progress goes to stderr so stdout stays clean."""
    out = tmp_path / "tech.md"

    run_cli(monkeypatch, [str(codebase), "--output", str(out)])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Endpoints: 1" in captured.err


def test_missing_directory_exits_nonzero(monkeypatch, tmp_path):
    with pytest.raises(SystemExit) as exc:
        run_cli(monkeypatch, [str(tmp_path / "does-not-exist")])

    assert exc.value.code == 1


def test_file_path_instead_of_directory_exits_nonzero(monkeypatch, tmp_path):
    target = tmp_path / "file.java"
    target.write_text(CONTROLLER)

    with pytest.raises(SystemExit) as exc:
        run_cli(monkeypatch, [str(target)])

    assert exc.value.code == 1


def test_codebase_without_api_surface_still_writes_output(monkeypatch, tmp_path):
    root = tmp_path / "empty"
    root.mkdir()
    out = tmp_path / "tech.md"

    run_cli(monkeypatch, [str(root), "--output", str(out)])

    assert out.is_file()
    assert "Extracted API Surface" in out.read_text()
