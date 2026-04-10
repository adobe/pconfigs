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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  echo "Usage: bash docs/comparisons/testbed/clean.sh [-y] [--dry-run]" >&2
  echo "" >&2
  echo "Deletes generated comparison artifacts (Hydra outputs, caches, venv)." >&2
}

confirm="true"
dry_run="false"
while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes)
      confirm="false"
      shift
      ;;
    --dry-run)
      dry_run="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

paths=(
  "${SCRIPT_DIR}/.venv"
  "${SCRIPT_DIR}/hydra/outputs"
  "${SCRIPT_DIR}/hydra/multirun"
  "${SCRIPT_DIR}/hydra/.hydra"
  "${SCRIPT_DIR}/hydra/logs"
  "${SCRIPT_DIR}/gin/__pycache__"
  "${SCRIPT_DIR}/hydra/__pycache__"
  "${SCRIPT_DIR}/__pycache__"
  "${SCRIPT_DIR}/.pytest_cache"
)

existing_paths=()
for path in "${paths[@]}"; do
  if [[ -e "${path}" ]]; then
    existing_paths+=("${path}")
  fi
done

if [[ ${#existing_paths[@]} -eq 0 ]]; then
  echo "Nothing to clean."
  exit 0
fi

echo "Will delete:"
for path in "${existing_paths[@]}"; do
  echo "  ${path}"
done

if [[ "${dry_run}" == "true" ]]; then
  exit 0
fi

if [[ "${confirm}" == "true" ]]; then
  read -r -p "Proceed? [y/N] " response
  if [[ ! "${response}" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi
fi

rm -rf "${existing_paths[@]}"
echo "Cleaned."
