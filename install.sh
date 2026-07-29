#!/bin/bash
#
# Install the SpecLens spec-to-code validation subagent into a target project.
#
# Usage:
#   ./install.sh /path/to/target/project
#
# This script:
#   1. Copies .kiro/ configuration (agents, hooks, skills, steering) into the target
#   2. Installs the speclens package, which provides the extract-api-surface CLI
#
# The extractor is installed as a Python package rather than copied into the
# target project, so the target repository stays free of vendored tool source.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:?Usage: $0 /path/to/target/project}"

if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Target directory does not exist: $TARGET_DIR" >&2
    exit 1
fi

# Prefer python3 -m pip so the install lands in the active interpreter/venv.
PIP=(python3 -m pip)
if ! python3 -c "import pip" >/dev/null 2>&1; then
    if command -v pip3 >/dev/null 2>&1; then
        PIP=(pip3)
    elif command -v pip >/dev/null 2>&1; then
        PIP=(pip)
    else
        echo "Error: no pip found. Install pip for python3 and re-run." >&2
        exit 1
    fi
fi

echo "Installing SpecLens into: $TARGET_DIR"

# Copy .kiro configuration
echo "  Copying .kiro/ configuration..."
mkdir -p "$TARGET_DIR/.kiro"
cp -r "$SCRIPT_DIR/.kiro/agents" "$TARGET_DIR/.kiro/"
cp -r "$SCRIPT_DIR/.kiro/hooks" "$TARGET_DIR/.kiro/"
cp -r "$SCRIPT_DIR/.kiro/skills" "$TARGET_DIR/.kiro/"
cp -r "$SCRIPT_DIR/.kiro/steering" "$TARGET_DIR/.kiro/"

# Install the extractor package (idempotent — safe to re-run)
echo "  Installing the speclens package (provides extract-api-surface)..."
if ! "${PIP[@]}" install "$SCRIPT_DIR"; then
    cat >&2 <<EOF

Error: installing the speclens package failed.

If the failure above mentions an "externally-managed-environment" (PEP 668),
your Python is managed by the OS or a package manager. Install into a virtual
environment instead:

    python3 -m venv .venv
    source .venv/bin/activate
    $0 $TARGET_DIR

The .kiro/ configuration was already copied into $TARGET_DIR successfully.
EOF
    exit 1
fi

echo ""
echo "Installation complete."
echo ""
if command -v extract-api-surface >/dev/null 2>&1; then
    echo "Verified: extract-api-surface is on PATH."
else
    echo "Note: extract-api-surface is not on PATH. It may be installed in a"
    echo "      user or virtualenv bin directory; run it via:"
    echo "      python3 -m speclens.cli --help"
fi
echo ""
echo "The spec-validator subagent is now available in your project."
echo "Trigger it with: /spec-validate"
echo "Or invoke the agent directly via Kiro."
