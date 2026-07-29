"""
SpecLens — tree-sitter based API surface extractor for spec-to-code validation.

Deterministically extracts the public API surface (endpoints, DTOs/entities, and
service interfaces) from a codebase so the spec-validation subagent can generate
tests from specifications without reading implementation source code.

Public entry points:
    Scanner          — walks a codebase and produces an ExtractionResult
    format_tech_md   — renders an ExtractionResult as a tech.md document
    format_yaml      — renders an ExtractionResult as structured YAML
"""

from .core import (
    Endpoint,
    ExtractionResult,
    Language,
    Parameter,
    ServiceMethod,
    TypeDefinition,
    detect_language,
)
from .formatter import format_tech_md, format_yaml
from .scanner import Scanner

__version__ = "1.0.0"

__all__ = [
    "Endpoint",
    "ExtractionResult",
    "Language",
    "Parameter",
    "ServiceMethod",
    "TypeDefinition",
    "detect_language",
    "format_tech_md",
    "format_yaml",
    "Scanner",
    "__version__",
]
