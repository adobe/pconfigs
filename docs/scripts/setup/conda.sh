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

# Create and populate a Conda environment for building the docs.
#
# Usage:
#   bash docs/scripts/setup/conda.sh [-n ENV_NAME] [-p PYTHON_VERSION]
#
# Defaults:
#   ENV_NAME: pconfig-docs
#   PYTHON_VERSION: 3.10
#   REQUIREMENTS_FILE: docs/requirements.txt

usage() {
  echo "Usage: bash docs/scripts/setup/conda.sh [-n ENV_NAME] [-p PYTHON_VERSION]" >&2
}

# Resolve script directory and load default Conda env name
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root_scripts_dir="$(cd "${script_dir}/.." && pwd)"
source "${root_scripts_dir}/conda_env.sh"

# Determine repo name for default env name
main_repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
repo_name="${main_repo_root:+$(basename "${main_repo_root}")}"

# Defaults (can be overridden by flags)
ENV_NAME="${ENV_NAME:-${PCONFIG_BUILD_ENV}}"
PYTHON_VERSION="${PYTHON_VERSION:-3.10}"
REQUIREMENTS_FILE="${root_scripts_dir}/../requirements.txt"

while getopts ":n:p:h" opt; do
  case "${opt}" in
    n) ENV_NAME="${OPTARG}" ;;
    p) PYTHON_VERSION="${OPTARG}" ;;
    h) usage; exit 0 ;;
    :) echo "Option -${OPTARG} requires an argument." >&2; usage; exit 1 ;;
    \?) echo "Invalid option: -${OPTARG}" >&2; usage; exit 1 ;;
  esac
done

if [[ ! -f "${REQUIREMENTS_FILE}" ]]; then
  echo "Error: requirements file not found at ${REQUIREMENTS_FILE}" >&2
  exit 1
fi

# Ensure conda is available
if ! command -v conda >/dev/null 2>&1; then
  echo "Error: conda not found in PATH. Install Miniconda/Anaconda and retry." >&2
  exit 1
fi

# Prefer mamba for faster solves if available for creation, but still use conda for activation
CONDA_CREATE_CMD="conda"
if command -v mamba >/dev/null 2>&1; then
  CONDA_CREATE_CMD="mamba"
fi

# Enable conda in this shell
# shellcheck source=/dev/null
source "$(conda info --base)/etc/profile.d/conda.sh"

# Create env if it does not exist
if conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  echo "Conda env '${ENV_NAME}' already exists. Skipping creation."
else
  echo "Creating conda env '${ENV_NAME}' (python=${PYTHON_VERSION})..."
  "${CONDA_CREATE_CMD}" create -y -n "${ENV_NAME}" "python=${PYTHON_VERSION}"
fi

python_cmd=(conda run -n "${ENV_NAME}" python)
echo "Upgrading pip in '${ENV_NAME}'..."
"${python_cmd[@]}" -m pip install --upgrade pip
echo "Installing Python requirements into '${ENV_NAME}' from ${REQUIREMENTS_FILE}..."
"${python_cmd[@]}" -m pip install -r "${REQUIREMENTS_FILE}"

echo -e "\nDone. Docs build environment created."
