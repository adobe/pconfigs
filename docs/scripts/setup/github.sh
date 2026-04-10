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

# Create a github "worktree" for the gh-pages branch. This lets you to publish the docs via the docs/scripts/deploy.sh script.
#
# USAGE: bash docs/scripts/setup/github.sh
#
# Configure a worktree for the gh-pages branch. This is a directory that lives alongside the pconfig repo.
# It is placed as a sibling directory next to the main repository directory, named
#   "pconfig-gh-pages".

main_repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [[ -z "${main_repo_root}" ]]; then
  echo "Error: Not inside a git repository." >&2
  exit 1
fi

repo_name="$(basename "${main_repo_root}")"
parent_dir="$(dirname "${main_repo_root}")"
site_dir_default="${parent_dir}/${repo_name}-gh-pages"

SITE_DIR="${SITE_DIR:-${site_dir_default}}"

echo "Main repo: ${main_repo_root}"
echo "Site worktree: ${SITE_DIR} (branch: gh-pages)"

# Clean up any stale directory that isn't a git repo/worktree
if [[ -d "${SITE_DIR}" ]] && \
   ! git -C "${SITE_DIR}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then

  echo "Found non-git directory at ${SITE_DIR}. You must remove that to continue. Aborting."
  exit 1
fi

# Ensure the gh-pages branch worktree exists
if git worktree list --porcelain | grep -q "^worktree ${SITE_DIR}$"; then
  echo "Worktree already exists at ${SITE_DIR}."
else
  # Try to attach existing branch; if it doesn't exist, create it
  if git show-ref --verify --quiet refs/heads/gh-pages; then
    echo "Adding worktree for existing branch gh-pages..."
    git worktree add "${SITE_DIR}" gh-pages
  else
    echo "Creating gh-pages branch and worktree..."
    git worktree add -b gh-pages "${SITE_DIR}"
  fi
fi

# Initialize the branch contents to an empty site commit (idempotent)
if [[ -d "${SITE_DIR}/.git" ]]; then
  echo "Initializing gh-pages contents (idempotent)..."
  git -C "${SITE_DIR}" rm -rf . >/dev/null 2>&1 || true
  git -C "${SITE_DIR}" clean -fdx >/dev/null 2>&1 || true
  touch "${SITE_DIR}/.nojekyll"
  if [[ -n "${CNAME:-}" ]]; then
    echo "${CNAME}" > "${SITE_DIR}/CNAME"
  fi
  if ! git -C "${SITE_DIR}" diff --quiet || ! git -C "${SITE_DIR}" diff --cached --quiet; then
    git -C "${SITE_DIR}" add -A
    git -C "${SITE_DIR}" commit -m "Initialize gh-pages worktree"
  fi
fi

echo "Done. Worktree ready at: ${SITE_DIR}"


