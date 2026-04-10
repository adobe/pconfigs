# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations


def _extract_param_id(nodeid: str) -> str:
    if nodeid.endswith("]") and "[" in nodeid:
        start = nodeid.rfind("[")
        return nodeid[start + 1 : -1]
    return nodeid


def _is_our_item(item) -> bool:
    try:
        modname = item.module.__name__
    except Exception:
        return False
    return modname == "pconfigs.test"


def pytest_collection_modifyitems(items):
    for item in items:
        if not _is_our_item(item):
            continue
        cs = getattr(item, "callspec", None)
        if cs is None or not cs.id:
            continue
        new_id = cs.id
        item.name = new_id
        try:
            item._nodeid = new_id
        except Exception:
            pass


def pytest_itemcollected(item):
    if not _is_our_item(item):
        return
    cs = getattr(item, "callspec", None)
    if cs is None or not cs.id:
        return
    item.name = cs.id
    try:
        item._nodeid = cs.id
    except Exception:
        pass


def pytest_configure(config):
    tr = config.pluginmanager.getplugin("terminalreporter")
    if tr is None:
        return

    original = getattr(tr, "_getfailureheadline", None)
    if original is None:
        return

    def _custom_failure_headline(rep):
        nid = rep.nodeid
        if nid.startswith("pconfigs/test.py::"):
            return f"FAILED {_extract_param_id(nid)}"
        return original(rep)

    tr._getfailureheadline = _custom_failure_headline


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    failed = terminalreporter.stats.get("failed") or []
    for rep in failed:
        nid = rep.nodeid
        if nid.startswith("pconfigs/test.py::"):
            new = _extract_param_id(nid)
            rep.nodeid = new
            try:
                rep.head_line = new
            except Exception:
                pass
