"""Tests for codebase discovery and scan orchestration."""

from pathlib import Path

import pytest

from speclens import Scanner
from speclens.core import Language, detect_language

CONTROLLER = """
package com.example;

@RestController
@RequestMapping("/api/orders")
public class OrderController {
    @GetMapping("/{id}")
    public OrderResponse getOrder(@PathVariable String id) { return null; }
}
"""


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("Foo.java", Language.JAVA),
        ("foo.py", Language.PYTHON),
        ("foo.ts", Language.TYPESCRIPT),
        ("foo.tsx", Language.TYPESCRIPT),
        ("foo.go", Language.GO),
        ("foo.cs", Language.CSHARP),
        ("README.md", None),
        ("Makefile", None),
    ],
)
def test_detect_language_by_suffix(filename, expected):
    assert detect_language(Path(filename)) is expected


def test_scanner_extracts_from_surface_pattern_file(tmp_path: Path):
    (tmp_path / "OrderController.java").write_text(CONTROLLER)

    result = Scanner(tmp_path).scan()

    assert len(result.endpoints) == 1
    assert result.endpoints[0].path == "/api/orders/{id}"
    assert result.errors == []


def test_non_surface_filenames_are_skipped_by_default(tmp_path: Path):
    """`Helpers.java` does not match a surface pattern, so it is not scanned."""
    (tmp_path / "Helpers.java").write_text(CONTROLLER)

    result = Scanner(tmp_path).scan()

    assert result.endpoints == []


def test_scan_all_includes_non_surface_filenames(tmp_path: Path):
    (tmp_path / "Helpers.java").write_text(CONTROLLER)

    result = Scanner(tmp_path, scan_all=True).scan()

    assert len(result.endpoints) == 1


def test_skip_dirs_are_not_scanned(tmp_path: Path):
    vendored = tmp_path / "node_modules" / "pkg"
    vendored.mkdir(parents=True)
    (vendored / "OrderController.java").write_text(CONTROLLER)

    result = Scanner(tmp_path, scan_all=True).scan()

    assert result.endpoints == []


def test_file_paths_are_recorded_relative_to_root(tmp_path: Path):
    nested = tmp_path / "src" / "main" / "java"
    nested.mkdir(parents=True)
    (nested / "OrderController.java").write_text(CONTROLLER)

    result = Scanner(tmp_path).scan()

    assert result.endpoints[0].file_path == "src/main/java/OrderController.java"


def test_extractor_failure_is_reported_without_aborting_scan(tmp_path: Path):
    """One failing file must not prevent the rest of the codebase from scanning."""
    (tmp_path / "OrderController.java").write_text(CONTROLLER)
    (tmp_path / "routes.py").write_text(
        '@router.get("/api/items")\ndef list_items():\n    return None\n'
    )

    scanner = Scanner(tmp_path)

    class ExplodingExtractor:
        def parse(self, source):
            raise RuntimeError("grammar unavailable")

    scanner._extractors[Language.JAVA] = ExplodingExtractor()
    result = scanner.scan()

    # The Python file still produced its endpoint.
    assert [e.path for e in result.endpoints] == ["/api/items"]
    assert len(result.errors) == 1
    assert "OrderController.java" in result.errors[0]
    assert "grammar unavailable" in result.errors[0]


def test_binary_content_does_not_crash_the_scan(tmp_path: Path):
    (tmp_path / "OrderController.java").write_text(CONTROLLER)
    (tmp_path / "BrokenController.java").write_bytes(b"\xff\xfe\x00package broken;")

    result = Scanner(tmp_path).scan()

    assert len(result.endpoints) == 1


def test_empty_directory_yields_empty_result(tmp_path: Path):
    result = Scanner(tmp_path).scan()

    assert result.endpoints == []
    assert result.types == []
    assert result.service_methods == []
    assert result.errors == []


def test_multi_language_codebase_is_aggregated(tmp_path: Path):
    (tmp_path / "OrderController.java").write_text(CONTROLLER)
    (tmp_path / "routes.py").write_text(
        '@router.get("/api/items")\ndef list_items():\n    return None\n'
    )
    (tmp_path / "handler.go").write_text(
        'package main\n\nfunc reg(r *gin.Engine) {\n\tr.GET("/api/ping", ping)\n}\n'
    )

    result = Scanner(tmp_path).scan()

    paths = {e.path for e in result.endpoints}
    assert paths == {"/api/orders/{id}", "/api/items", "/api/ping"}
