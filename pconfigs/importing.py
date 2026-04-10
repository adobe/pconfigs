# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

import importlib
import traceback
from typing import Any, Tuple


def split_last_attr(full_path: str) -> Tuple[str, str]:
    parts = full_path.split(".")
    attribute_name = parts[-1]
    module_name = ".".join(parts[:-1])

    return module_name, attribute_name


def split_attrs(full_path: str) -> Tuple[str, str]:
    """Splits a full . separated path to a module and an attribute within that module into multiple parsings. Yields
    each parsing. The first parsing is to treat the entire path as a module with no attribute. The last parsing treats
    the first term (before the first .) as the module, and the remaining entries as attributes within attributes in that
    module.
    """
    parts = full_path.split(".")
    for k in range(len(parts)):
        if k == 0:
            attribute_name = ""
            module_name = ".".join(parts)
        else:
            attribute_name = ".".join(parts[-k:])
            module_name = ".".join(parts[:-k])

        yield module_name, attribute_name


def import_from(module_name: str, attribute_name: str) -> Any:
    module = importlib.import_module(module_name)
    return getattr(module, attribute_name)


def getmoduleattr(attribute_path: str) -> Any:
    """Given a full . separated path to a module and an attribute within the module, this will import the module
    and return the attribute.
    """
    errors = []
    for module_name, attr_name in split_attrs(attribute_path):
        try:
            module = importlib.import_module(module_name)
            attr = module
            for subattr in attr_name.split("."):
                attr = getattr(attr, subattr)

            return attr

        except (ModuleNotFoundError, AttributeError) as err:
            backtrace = traceback.format_exc()
            errors.append((module_name, attr_name, err, backtrace))

    for k, (module_name, attr_name, err, backtrace) in enumerate(errors[::-1]):
        if not attr_name:
            msg = "Import path split {:02d}.\n  Import      {}\n  Fails       {}\n  Backtrace   {}\n".format(
                k, module_name, err, backtrace
            )
        else:
            msg = "Import path split {:02d}.\n  Import      {}\n  From        {}\n  Fails       {}\n  Backtrace   {}\n".format(
                k, attr_name, module_name, err, backtrace
            )

        print(msg)

    print("No import path splits succeed for: {}".format(attribute_path))

    raise ModuleNotFoundError("Module and/or attribute not found: {}".format(attribute_path))


def get_attribute_module(attribute_path: str) -> str:
    for module_name, attr_name in split_attrs(attribute_path):
        try:
            module = importlib.util.find_spec(module_name)
            if module is None:
                # This happens when the penultimate key is a directory of modules, and the final key is not a valid
                # module name within that directory. In this case, we can only hope that the __init__.py has included
                # the thing that the user is looking for. So, we will try to import it from there.
                name_parts = module_name.split(".")
                module_name = ".".join(name_parts[:-1])
                attr_name = ".".join(name_parts[-1:])
                module = importlib.import_module(module_name)
                attr = module
                for subattr in attr_name.split("."):
                    attr = getattr(attr, subattr)

            return module_name
        except ModuleNotFoundError:
            pass

    raise ModuleNotFoundError("No base module found for attribute path: {}".format(attribute_path))


def get_module_path(module_import_str: str) -> str:
    module = importlib.import_module(module_import_str)
    return module.__file__
