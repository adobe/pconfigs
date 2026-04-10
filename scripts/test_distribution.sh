#!/usr/bin/env bash

# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

set -euo pipefail

# Test the pconfigs wheel distribution end-to-end.
#
# Builds a wheel, installs it into a fresh conda env, runs both
# `pconfigs.cursor install` and `pconfigs.claude install` into temp
# directories, then verifies that all expected files landed correctly.
# Everything is cleaned up on exit.
#
# Usage:
#   ./scripts/test_distribution.sh
#
# Prerequisites:
#   - conda available on PATH
#   - A conda env named "pconfig" with the `build` package installed

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_NAME="pconfig-dist-test"
CONDA_BASE="$(conda info --base)"
BUILD_PYTHON="$CONDA_BASE/envs/pconfigs/bin/python"
CURSOR_TARGET_DIR="$(mktemp -d)"
CLAUDE_TARGET_DIR="$(mktemp -d)"

GREEN='\033[1;32m'
RED='\033[1;31m'
RESET='\033[0m'
PASSED=false

cleanup() {
    local exit_code=$?
    echo ""
    echo "=== Cleaning up ==="
    conda remove -n "$ENV_NAME" --all -y 2>/dev/null || true
    rm -rf "$REPO_DIR/dist/" "$CURSOR_TARGET_DIR" "$CLAUDE_TARGET_DIR"

    echo ""
    if [ "$PASSED" = true ]; then
        echo -e "${GREEN}╔════════════════════════════╗${RESET}"
        echo -e "${GREEN}║   ALL TESTS PASSED         ║${RESET}"
        echo -e "${GREEN}╚════════════════════════════╝${RESET}"
    else
        echo -e "${RED}╔════════════════════════════╗${RESET}"
        echo -e "${RED}║   TESTS FAILED             ║${RESET}"
        echo -e "${RED}╚════════════════════════════╝${RESET}"
    fi

    exit "$exit_code"
}
trap cleanup EXIT

run_in_env() {
    env -u PYTHONPATH conda run --no-capture-output -n "$ENV_NAME" "$@"
}

echo "=== Building wheel ==="
rm -rf "$REPO_DIR/dist/"
cd "$REPO_DIR"
"$BUILD_PYTHON" -m build --wheel
WHEEL="$(ls "$REPO_DIR"/dist/pconfigs-*.whl)"
echo "Built: $WHEEL"

echo ""
echo "=== Creating fresh conda env: $ENV_NAME ==="
conda remove -n "$ENV_NAME" --all -y 2>/dev/null || true
conda create -n "$ENV_NAME" python=3.10 -y

echo ""
echo "=== Installing wheel (non-editable) ==="
run_in_env python -m pip install "$WHEEL"

echo ""
echo "=== Running install commands ==="
run_in_env python -m pconfigs.cursor install "$CURSOR_TARGET_DIR" -y
run_in_env python -m pconfigs.claude install "$CLAUDE_TARGET_DIR" -y

echo ""
echo "=== Verifying ==="
run_in_env python - "$CURSOR_TARGET_DIR" "$CLAUDE_TARGET_DIR" <<'PY'
import os
import sys

import pconfigs


def check_dirs(base, label, checks):
    errors = []
    for rel_dir, suffix in checks:
        full = os.path.join(base, rel_dir)
        if not os.path.isdir(full):
            errors.append(f"MISSING: {rel_dir}/")
            continue

        files = [
            os.path.join(root, f)
            for root, _, filenames in os.walk(full)
            for f in filenames
            if suffix is None or f.endswith(suffix)
        ]

        if not files:
            errors.append(f"EMPTY:   {rel_dir}/ (expected *{suffix})")
        else:
            print(f"  {rel_dir}/ -> {len(files)} files")

    return errors


def check_file(base, rel_path):
    full = os.path.join(base, rel_path)
    if not os.path.isfile(full):
        return [f"MISSING: {rel_path}"]

    print(f"  {rel_path} exists")

    return []


cursor_target, claude_target = sys.argv[1], sys.argv[2]
pkg_dir = os.path.dirname(pconfigs.__file__)
all_errors = []

print(f"Package version: {pconfigs.__version__}")
print(f"Package dir:     {pkg_dir}")

asset_checks = [("rules", ".md"), ("skills", "SKILL.md"), ("installation_test", None)]

print("\n--- Package assets ---")
for asset_dir in ["cursor_assets", "claude_assets"]:
    all_errors += check_dirs(pkg_dir, asset_dir, [
        (f"{asset_dir}/{sub}", suffix) for sub, suffix in asset_checks
    ])

print("\n--- Cursor install ---")
all_errors += check_dirs(cursor_target, "cursor", [
    (".cursor/rules/pconfigs", ".mdc"),
    (".cursor/skills", "SKILL.md"),
    (".cursor/installation_test", None),
])

print("\n--- Claude install ---")
all_errors += check_dirs(claude_target, "claude", [
    (".claude/pconfigs", ".md"),
    (".claude/skills", "SKILL.md"),
    (".claude/installation_test", None),
])
all_errors += check_file(claude_target, "CLAUDE.md")

if all_errors:
    print("\nERRORS:")
    for e in all_errors:
        print(f"  {e}")
    sys.exit(1)

print("\nAll checks passed.")
PY

PASSED=true
