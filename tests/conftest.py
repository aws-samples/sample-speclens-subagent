"""Shared fixtures for the SpecLens extractor test suite."""

from pathlib import Path

import pytest

from speclens.go_extractor import GoExtractor
from speclens.java_extractor import JavaExtractor
from speclens.python_extractor import PythonExtractor
from speclens.typescript_extractor import TypeScriptExtractor


@pytest.fixture(scope="session")
def java_extractor() -> JavaExtractor:
    return JavaExtractor()


@pytest.fixture(scope="session")
def python_extractor() -> PythonExtractor:
    return PythonExtractor()


@pytest.fixture(scope="session")
def typescript_extractor() -> TypeScriptExtractor:
    return TypeScriptExtractor()


@pytest.fixture(scope="session")
def go_extractor() -> GoExtractor:
    return GoExtractor()


def extract_all(extractor, source: str, file_path: str):
    """Parse `source` and return (endpoints, types, service_methods)."""
    raw = source.encode("utf-8")
    tree = extractor.parse(raw)
    return (
        extractor.extract_endpoints(tree, raw, file_path),
        extractor.extract_types(tree, raw, file_path),
        extractor.extract_service_methods(tree, raw, file_path),
    )


@pytest.fixture
def write_source(tmp_path: Path):
    """Write a source file into a temp codebase tree and return the root."""

    def _write(relative_path: str, content: str) -> Path:
        target = tmp_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return tmp_path

    return _write
