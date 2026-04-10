# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from pygments.style import Style
from pygments.token import (
    Comment,
    Generic,
    Keyword,
    Literal,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
    Whitespace,
)


class VSCodeDarkPlusStyle(Style):
    background_color = "#1e1e1e"
    default_style = ""
    styles = {
        Text: "#d4d4d4",
        Whitespace: "",
        Comment: "italic #6a9955",
        # VS Code Dark+ uses blue for Python keywords (class/def/etc.)
        Keyword: "#569cd6",
        Keyword.Type: "#4ec9b0",
        Name: "#9cdcfe",
        Name.Function: "#dcdcaa",
        Name.Class: "#4ec9b0",
        Name.Namespace: "#4ec9b0",
        Name.Builtin: "#4ec9b0",
        # Decorators like @pconfig / @pconfiged
        Name.Decorator: "#dcdcaa",
        # Keyword-argument names like constructs= in decorators/calls
        Name.Attribute: "#dcdcaa",
        Name.Variable: "#9cdcfe",
        String: "#ce9178",
        Literal.String.Affix: "#ce9178",
        Number: "#b5cea8",
        Operator: "#d4d4d4",
        Punctuation: "#d4d4d4",
        Generic.Deleted: "#f14c4c",
        Generic.Inserted: "#b5cea8",
        Generic.Heading: "bold #d4d4d4",
        Generic.Subheading: "bold #d4d4d4",
    }
