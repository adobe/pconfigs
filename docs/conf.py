# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

import os
import sys

# Ensure the package can be imported when building locally or in CI
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = '🌲 <span class="brand-name">pconfigs</span>'
author = "Eric Kee and Adam Pikielny"

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx.ext.autosectionlabel",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

autosummary_generate = False
autosectionlabel_prefix_document = True
autodoc_typehints = "none"
autodoc_preserve_defaults = False
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# Only document the public interface exported via __all__ when using autosummary
autodoc_default_options = {
    "members": False,
    "undoc-members": False,
    "inherited-members": False,
    "show-inheritance": False,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css", "typehints.css"]
html_js_files = ["typehints.js"]

# Code highlighting: use VS Code Dark+ for dark mode
pygments_dark_style = "docs._vscode_dark_plus.VSCodeDarkPlusStyle"

# MyST configuration
myst_enable_extensions = [
    "colon_fence",  # enable ::: directive fences (used for subtitle rubric)
]


def _skip_sentinel_members(app, what, name, obj, would_skip, options):
    if name in {"Pinned", "Required"}:
        return True
    return would_skip


def setup(app):
    app.connect("autodoc-skip-member", _skip_sentinel_members)
