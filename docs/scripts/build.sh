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

# Build Sphinx docs locally and print the path/URL to index.html
#
# Usage:
#   bash docs/scripts/build.sh
#
# Optional env vars:
#   PCONFIG_BUILD_ENV  Conda env name to run the build in. If unset, uses the
#                      current Python on PATH (the active venv or conda env).

main_repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [[ -z "${main_repo_root}" ]]; then
  echo "Error: Not inside a git repository." >&2
  exit 1
fi

DOCS_SRC_DIR="${main_repo_root}/docs"
DOCS_BUILD_DIR="${DOCS_SRC_DIR}/_build/html"

if [[ ! -f "${DOCS_SRC_DIR}/conf.py" ]]; then
  echo "Error: ${DOCS_SRC_DIR}/conf.py not found. Are you in the right repo?" >&2
  exit 1
fi

# Select Python: use PCONFIG_BUILD_ENV conda env if set, otherwise current Python on PATH
if [[ -n "${PCONFIG_BUILD_ENV:-}" ]]; then
  python_cmd=(conda run -n "${PCONFIG_BUILD_ENV}" python)
  echo "Using conda env: ${PCONFIG_BUILD_ENV}"
else
  python_cmd=(python)
fi

echo "Cleaning previous build output..."
rm -rf "${DOCS_BUILD_DIR}"
echo "Building Sphinx HTML (full rebuild)..."
"${python_cmd[@]}" -m sphinx -E -b html "${DOCS_SRC_DIR}" "${DOCS_BUILD_DIR}"

index_path="${DOCS_BUILD_DIR}/index.html"
if [[ -f "${index_path}" ]]; then
  abs_path="$(cd "${DOCS_BUILD_DIR}" && pwd)/index.html"
  echo -e "\nBuilt docs: ${abs_path}"
  echo -e "Built URL : file://${abs_path}\n"
else
  echo "Build finished, but index.html not found at ${index_path}" >&2
  exit 2
fi


