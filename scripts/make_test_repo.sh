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
PCONFIG_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_NAME="my_pconfigs"
TARGET_DIR="${1:-$(cd "$PCONFIG_REPO/.." && pwd)/$ENV_NAME}"

run_in_env() {
    env -u PYTHONPATH conda run --no-capture-output -n "$ENV_NAME" "$@"
}

RED='\033[1;31m'
GREEN='\033[1;32m'
RESET='\033[0m'

echo "=== Fresh pconfigs install ==="
echo ""
echo "This will modify:"
echo -e "  ${RED}DELETE${RESET} conda env:  $ENV_NAME"
echo -e "  ${RED}DELETE${RESET} directory:  $TARGET_DIR"
echo -e "  ${GREEN}CREATE${RESET} conda env:  $ENV_NAME (python 3.10)"
echo -e "  ${GREEN}CREATE${RESET} directory:  $TARGET_DIR"
echo ""
read -r -p "Proceed? [y/N] " response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi
echo ""

if ! command -v conda &> /dev/null; then
    echo "Error: conda is not installed or not in PATH"
    exit 1
fi
eval "$(conda shell.bash hook)"

echo "=== Removing conda env '$ENV_NAME' (if exists) ==="
conda remove -n "$ENV_NAME" --all -y 2>/dev/null || true

echo "=== Cleaning target directory ==="
if [ -d "$TARGET_DIR" ]; then
    rm -rf "$TARGET_DIR"
fi
mkdir -p "$TARGET_DIR"

echo "=== Creating conda env '$ENV_NAME' ==="
conda create -n "$ENV_NAME" python=3.10 -y

echo "=== Installing pconfigs ==="
run_in_env python -m pip install -e "$PCONFIG_REPO"

echo "=== Installing Cursor rules ==="
run_in_env python -m pconfigs.cursor install "$TARGET_DIR" -y

echo "=== Installing Claude rules ==="
run_in_env python -m pconfigs.claude install "$TARGET_DIR" -y

cat > "$TARGET_DIR/install.sh" << 'INSTALL_EOF'
#!/bin/bash
set -e

ENV_NAME="my_pconfigs"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PCONFIG_REPO="__PCONFIG_REPO__"

echo "=== Setting up $ENV_NAME environment ==="

if ! command -v conda &> /dev/null; then
    echo "Error: conda is not installed or not in PATH"
    exit 1
fi
eval "$(conda shell.bash hook)"

if conda env list | grep -Eq "^\s*${ENV_NAME}\s"; then
    echo "Conda environment '$ENV_NAME' already exists"
else
    echo "Creating conda environment '$ENV_NAME' with Python 3.10..."
    conda create -n "$ENV_NAME" python=3.10 -y
fi

echo "Installing pconfigs..."
conda run -n "$ENV_NAME" python -m pip install -e "$PCONFIG_REPO"

echo "Installing Cursor rules..."
conda run -n "$ENV_NAME" python -m pconfigs.cursor install "$SCRIPT_DIR" -y

echo "Installing Claude rules..."
conda run -n "$ENV_NAME" python -m pconfigs.claude install "$SCRIPT_DIR" -y
INSTALL_EOF
sed -i '' "s|__PCONFIG_REPO__|$PCONFIG_REPO|" "$TARGET_DIR/install.sh"
chmod +x "$TARGET_DIR/install.sh"

cat > "$TARGET_DIR/README.md" << 'README_EOF'
# my_pconfigs

A starter project using the pconfigs library.

## Setup

Run the installer script:

```bash
./install.sh
```

This will:
1. Create a `my_pconfigs` conda environment with Python 3.10
2. Install pconfigs
3. Install Cursor and Claude rules configured for this environment

## Usage

Activate the environment:

```bash
conda activate my_pconfigs
```

Run a pconfig file:

```bash
python -m pconfigs.run my_pconfigs.pconfig.example.config
```

Print a config's resolved values:

```bash
python -m pconfigs.print my_pconfigs.pconfig.example.config
```

Test all pconfigs:

```bash
ptest
```
README_EOF

echo "=== Initializing git repo ==="
cd "$TARGET_DIR"
git init

echo ""
echo "=== Done ==="
echo "  Activate: conda activate $ENV_NAME"
echo "  Location: $TARGET_DIR"
