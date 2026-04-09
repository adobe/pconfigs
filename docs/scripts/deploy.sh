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

# Build and publish Sphinx docs to the gh-pages branch via a git worktree.
#
# Usage:
#   bash docs/scripts/deploy.sh
#
# Optional env vars:
#   SITE_DIR           Path to the gh-pages worktree (default: sibling '<repo>-gh-pages')
#   CNAME              Custom domain to restore into CNAME if it's missing
#   PCONFIG_BUILD_ENV  Conda env name to run the build in (default: pconfig-docs)

main_repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [[ -z "${main_repo_root}" ]]; then
  echo "Error: Not inside a git repository." >&2
  exit 1
fi
# Load default Conda env name (sets PCONFIG_BUILD_ENV if unset)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/conda_env.sh"


repo_name="$(basename "${main_repo_root}")"
parent_dir="$(dirname "${main_repo_root}")"
site_dir_default="${parent_dir}/${repo_name}-gh-pages"
SITE_DIR="${SITE_DIR:-${site_dir_default}}"

DOCS_SRC_DIR="${main_repo_root}/docs"
DOCS_BUILD_DIR="${DOCS_SRC_DIR}/_build/html"

echo -e "\nMain repo: ${main_repo_root}"
echo -e "Site dir : ${SITE_DIR} (branch: gh-pages)\n"

# Ensure worktree is up-to-date with remote (reset to remote if it exists)
echo "Synchronizing gh-pages with remote (if configured)..."
git -C "${SITE_DIR}" fetch origin gh-pages || true
if git -C "${SITE_DIR}" rev-parse --verify --quiet remotes/origin/gh-pages >/dev/null 2>&1; then
  # Hard reset to avoid divergence on a generated branch
  git -C "${SITE_DIR}" reset --hard origin/gh-pages || true
fi

# Ensure worktree exists
if ! git worktree list --porcelain | grep -q "^worktree ${SITE_DIR}$"; then
  echo "Worktree not found at ${SITE_DIR}. Run docs/scripts/setup/github.sh first or set SITE_DIR."
  exit 1
fi

# Build docs
if [[ ! -f "${DOCS_SRC_DIR}/conf.py" ]]; then
  echo "Error: ${DOCS_SRC_DIR}/conf.py not found. Are you in the right repo?" >&2
  exit 1
fi

echo "Cleaning previous autosummary stubs..."
rm -rf "${DOCS_SRC_DIR}/api/generated" || true

echo "Running build script..."
bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/build.sh"

# Sync build into site worktree (preserve its .git)
echo "Syncing build into site worktree..."
rsync -av --delete --exclude '.git' --exclude '.doctrees' --exclude 'CNAME' \
  "${DOCS_BUILD_DIR}/" "${SITE_DIR}/"

# If a custom domain file is missing, optionally restore it from $CNAME
if [[ ! -f "${SITE_DIR}/CNAME" && -n "${CNAME:-}" ]]; then
  echo "Restoring CNAME from env: ${CNAME}"
  echo "${CNAME}" > "${SITE_DIR}/CNAME"
fi

touch "${SITE_DIR}/.nojekyll"

# Commit and push
echo "Committing and pushing..."
git -C "${SITE_DIR}" add -A
if ! git -C "${SITE_DIR}" diff --cached --quiet; then
  git -C "${SITE_DIR}" commit -m "Docs: update $(date +%F)"
  set +e
  git -C "${SITE_DIR}" push -u origin gh-pages
  rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "Push failed (non-fast-forward). Resetting to remote and retrying..." >&2
    git -C "${SITE_DIR}" fetch origin gh-pages || true
    git -C "${SITE_DIR}" reset --hard origin/gh-pages || exit $rc
    # re-sync build output after reset
    rsync -av --delete --exclude '.git' --exclude '.doctrees' --exclude 'CNAME' \
      "${DOCS_BUILD_DIR}/" "${SITE_DIR}/"
    
    # If a custom domain file is missing after reset, optionally restore it from $CNAME
    if [[ ! -f "${SITE_DIR}/CNAME" && -n "${CNAME:-}" ]]; then
      echo "Restoring CNAME from env: ${CNAME}"
      echo "${CNAME}" > "${SITE_DIR}/CNAME"
    fi
    touch "${SITE_DIR}/.nojekyll"
    git -C "${SITE_DIR}" add -A
    git -C "${SITE_DIR}" commit -m "Docs: update $(date +%F)"
    git -C "${SITE_DIR}" push -u origin gh-pages || exit $rc
  fi
  set -e
else
  echo "No changes to publish."
fi

echo "Done."


