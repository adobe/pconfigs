# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

import contextlib
import hashlib
import importlib
import io
import os
import sys
from enum import Enum
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from typing import Iterator, Optional, Tuple, Type

import pconfigs as _pconfigs


def make_dotpath_from_module_path(py_path: Path) -> str | None:
    """Compute a dotted module name for __pconfigs__.py if importable on sys.path.

    We walk up package directories (those having __init__.py) to find the package
    root and verify it’s on sys.path. If not importable, return None.
    """
    py_path = py_path.resolve()
    if py_path.name != "__pconfigs__.py":
        return None

    parts: list[str] = ["__pconfigs__"]
    cur = py_path.parent
    while (cur / "__init__.py").is_file():
        parts.append(cur.name)
        parent = cur.parent
        if parent == cur:
            break

        cur = parent

    pkg_root = cur.resolve()
    sys_paths = {Path(p).resolve() for p in sys.path if isinstance(p, str)}
    if pkg_root not in sys_paths:
        return None

    return ".".join(reversed(parts))


def type_matches(a: Optional[Type], b: Type) -> bool:
    if a is None:
        return False

    return a.__module__ == b.__module__ and a.__name__ == b.__name__


def iter_package_py(root: Path) -> Iterator[Path]:
    """Yield .py files under root, recursing into Python packages and
    implicit namespace packages (PEP 420).

    We include any subdirectory (namespace packages do not require
    an "__init__.py"). Excludes "__init__.py" and "__pconfigs__.py" files.
    """
    try:
        entries = sorted(root.iterdir())
    except Exception:
        return

    for e in entries:
        if e.is_dir():
            # Descend into all directories; implicit namespaces are valid
            yield from iter_package_py(e)
        elif e.suffix == ".py" and e.name not in ("__init__.py", "__pconfigs__.py"):
            yield e


def import_path_quiet(py_path: Path):
    if not (py_path.is_file() and py_path.suffix == ".py"):
        raise ImportError(f"Not a Python file: {py_path}")

    safe = hashlib.sha1(str(py_path.resolve()).encode("utf-8")).hexdigest()
    name = f"pconfigs_autoload_{safe}"

    loader = SourceFileLoader(name, str(py_path))
    spec = spec_from_loader(name, loader, origin=str(py_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create loader for {py_path}")

    module = module_from_spec(spec)
    if module is None:
        raise ImportError(f"Failed to create module for {py_path}")

    sys.modules[name] = module
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    try:
        # Ensure __file__ is available for modules imported when users launch with the ptest command.
        try:
            module.__file__ = str(py_path)
        except Exception:
            pass
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            loader.exec_module(module)

        return module
    finally:
        sys.modules.pop(name)


class TestTarget(Enum):
    Dotpath = "dotpath"
    Path = "path"
    Failure = "failure"


Dotpath = str
ImportableAndSource = Tuple[Dotpath | Path, Path]
ExceptionAndSource = Tuple[Exception, Path]


def list_configs() -> Iterator[Tuple[TestTarget, ImportableAndSource | ExceptionAndSource]]:
    start_dir = Path(os.getcwd())

    for pconfigs_file in start_dir.rglob("__pconfigs__.py"):
        curr_dir = pconfigs_file.parent
        pconfigs_dotpath = make_dotpath_from_module_path(pconfigs_file)

        if pconfigs_dotpath:
            # If the __pconfigs__.py file is importable as a dotted path, try importing it.
            try:
                module = import_dotpath_quiet(pconfigs_dotpath)
            except Exception as e:
                yield (TestTarget.Failure, (e, pconfigs_file))
                continue

            test_configs_attr = getattr(module, _pconfigs.TestConfigs.__name__, None)
            test_subdirs_attr = getattr(module, _pconfigs.TestSubdirs.__name__, None)

            base = pconfigs_dotpath.rsplit(".", 1)[0]
            if test_configs_attr is None:
                for currdir_py_file in sorted(curr_dir.glob("*.py")):
                    if currdir_py_file.name in ("__init__.py", "__pconfigs__.py"):
                        continue

                    yield (TestTarget.Dotpath, (f"{base}.{currdir_py_file.stem}", currdir_py_file))

            elif test_configs_attr is not _pconfigs.TestConfigs:
                raise ValueError(f"TestConfigs attribute is not the TestConfigs class: {test_configs_attr}")

            if test_configs_attr is not None:
                for py_file in test_configs_attr.py_files:
                    yield (TestTarget.Dotpath, (f"{base}.{py_file.stem}", py_file))

                test_configs_attr.__clear__()

            if test_subdirs_attr is _pconfigs.TestSubdirs:
                for sub_module in iter_package_py(curr_dir):
                    if sub_module.parent == curr_dir:
                        continue
                    rel = sub_module.relative_to(curr_dir).with_suffix("")
                    dotted = ".".join([base] + list(rel.parts))

                    yield (TestTarget.Dotpath, (dotted, sub_module))
        else:
            # If the __pconfigs__.py file is not importable as a dotted path, try importing it as a file path.
            try:
                module = import_path_quiet(pconfigs_file)
            except Exception as e:
                yield (TestTarget.Failure, (e, pconfigs_file))
                continue

            test_configs_attr = getattr(module, _pconfigs.TestConfigs.__name__, None)
            test_subdirs_attr = getattr(module, _pconfigs.TestSubdirs.__name__, None)
            if test_configs_attr is None:
                for currdir_py_file in sorted(curr_dir.glob("*.py")):
                    if currdir_py_file.name in ("__init__.py", "__pconfigs__.py"):
                        continue

                    yield (TestTarget.Path, (currdir_py_file, currdir_py_file))

            elif test_configs_attr is not _pconfigs.TestConfigs:
                raise ValueError(f"TestConfigs attribute is not TestConfigs class: {test_configs_attr}")

            if test_configs_attr is not None:
                for py_file in test_configs_attr.py_files:
                    yield (TestTarget.Path, (py_file, py_file))

                test_configs_attr.__clear__()

            if test_subdirs_attr is _pconfigs.TestSubdirs:
                for sub_module in iter_package_py(curr_dir):
                    if sub_module.parent == curr_dir:
                        continue

                    yield (TestTarget.Path, (sub_module, sub_module))


def import_dotpath_quiet(dotted: str):
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        return importlib.import_module(dotted)


try:
    import pytest
except Exception:
    pytest = None

if pytest is not None and __name__ != "__main__":
    pytest_plugins = ["pconfigs.tests.pytest"]

    def _short_rel(path: Path) -> str:
        try:
            return str(path.resolve().relative_to(Path.cwd().resolve()))
        except Exception:
            return path.name

    def _param_cases():
        cases = []
        for kind, (obj, source) in list_configs():
            if kind is TestTarget.Failure:
                continue
            if kind is TestTarget.Dotpath:
                cases.append(pytest.param(kind, obj, id=f"{obj}"))
            elif kind is TestTarget.Path:
                cases.append(pytest.param(kind, obj, id=f"{_short_rel(source)}"))

        return cases

    @pytest.mark.parametrize(("kind", "target"), _param_cases())
    def test_pconfigs_imports(kind, target):
        if kind is TestTarget.Dotpath:
            import_dotpath_quiet(target)
        else:
            import_path_quiet(target)


def main():
    total = 0
    errors = 0
    successes = 0
    for kind, (thing, source) in list_configs():
        try:
            if kind is TestTarget.Dotpath:
                dotpath = thing
                import_dotpath_quiet(dotpath)
                successes += 1
            elif kind is TestTarget.Path:
                path = thing
                import_path_quiet(path)
                successes += 1
            elif kind is TestTarget.Failure:
                errors += 1
                error = thing
                print(f"Import failed for {source}: {type(error).__name__}: '{error}'")
            else:
                raise ValueError(f"Unknown test target: {kind}")

            total += 1
        except Exception as error:
            print(f"Import failed for {source}: {type(error).__name__}: '{error}'")
            errors += 1

    print(f"Tested {total} configs. Errors: {errors}")


if __name__ == "__main__":
    main()
