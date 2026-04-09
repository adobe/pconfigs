#!/bin/bash

# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

DIR="$(cd "$(dirname "$0")" && pwd)"
QUESTIONS="$DIR/questions"
ANSWERS="$DIR/answers"
mkdir -p "$ANSWERS"

for qfile in $(ls "$QUESTIONS"/q*.md 2>/dev/null | sort); do
    base=$(basename "$qfile" .md)
    if [ ! -f "$ANSWERS/${base}.md" ]; then
        chmod 444 "$qfile" 2>/dev/null
        echo "Ready: questions/${base}.md"
        exit 0
    fi
    chmod 000 "$qfile" 2>/dev/null
done

chmod 444 "$QUESTIONS"/q*.md
COUNT=$(ls -1 "$QUESTIONS"/q*.md 2>/dev/null | wc -l | tr -d ' ')
echo "All $COUNT questions answered. Questions restored to readable."
