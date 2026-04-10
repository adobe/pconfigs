# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

import ast
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExampleResult:
    effective_batch_size: int
    lr_schedule: list[float]


def make_lr_schedule(*, base_lr: float, total_steps: int, min_lr_ratio: float) -> list[float]:
    if (total_steps <= 0) or (not 0.0 <= min_lr_ratio <= 1.0):
        raise ValueError(f"Invalid schedule config: total_steps={total_steps} min_lr_ratio={min_lr_ratio}")

    min_lr = base_lr * min_lr_ratio
    cosine_denom = max(1, total_steps - 1)
    return [
        min_lr + (base_lr - min_lr) * 0.5 * (1.0 + math.cos(math.pi * step / cosine_denom))
        for step in range(total_steps)
    ]


def run_command(*, args: list[str], cwd: str) -> str:
    script_dir = os.path.dirname(__file__)
    repo_dir = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    pythonpath_parts = [script_dir, repo_dir]
    existing_pythonpath = os.environ.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)

    run_env = os.environ.copy()
    run_env["PYTHONPATH"] = ":".join(pythonpath_parts)

    completed = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=run_env,
    )
    return completed.stdout


def parse_trainer_lines(stdout: str) -> ExampleResult:
    effective_batch_size_match = re.search(r"^effective_batch_size=(?P<value>\d+)\s*$", stdout, flags=re.MULTILINE)
    if effective_batch_size_match is None:
        raise ValueError(f"Could not find effective_batch_size line in output:\n{stdout}")

    lr_schedule_match = re.search(r"^lr_schedule=(?P<value>\[.*\])\s*$", stdout, flags=re.MULTILINE)
    if lr_schedule_match is None:
        raise ValueError(f"Could not find lr_schedule line in output:\n{stdout}")

    effective_batch_size = int(effective_batch_size_match.group("value"))
    lr_schedule_any: Any = ast.literal_eval(lr_schedule_match.group("value"))
    if not isinstance(lr_schedule_any, list) or not all(isinstance(x, (int, float)) for x in lr_schedule_any):
        raise TypeError(f"Unexpected lr_schedule type: {type(lr_schedule_any)}")

    lr_schedule = [float(x) for x in lr_schedule_any]
    return ExampleResult(effective_batch_size=effective_batch_size, lr_schedule=lr_schedule)


def parse_pconfigs_print(stdout: str) -> ExampleResult:
    effective_batch_size_match = re.search(r"effective_batch_size\s*=\s*(?P<value>\d+)\b", stdout)
    if effective_batch_size_match is None:
        raise ValueError(f"Could not find effective_batch_size in pconfigs.print output:\n{stdout}")

    lr_schedule_match = re.search(r"lr_schedule\s*=\s*(?P<value>\[[^\]]*\])", stdout)
    if lr_schedule_match is None:
        raise ValueError(f"Could not find lr_schedule in pconfigs.print output:\n{stdout}")

    effective_batch_size = int(effective_batch_size_match.group("value"))
    lr_schedule_any: Any = ast.literal_eval(lr_schedule_match.group("value"))
    if not isinstance(lr_schedule_any, list) or not all(isinstance(x, (int, float)) for x in lr_schedule_any):
        raise TypeError(f"Unexpected lr_schedule type: {type(lr_schedule_any)}")

    lr_schedule = [float(x) for x in lr_schedule_any]
    return ExampleResult(effective_batch_size=effective_batch_size, lr_schedule=lr_schedule)


def assert_close_lists(*, actual: list[float], expected: list[float]) -> None:
    if len(actual) != len(expected):
        raise AssertionError(f"Expected {len(expected)} steps, got {len(actual)}")

    for step, (a, e) in enumerate(zip(actual, expected)):
        if not math.isclose(a, e, rel_tol=0.0, abs_tol=1e-12):
            raise AssertionError(f"Mismatch at step={step}: actual={a} expected={e}")


def main() -> int:
    script_dir = os.path.dirname(__file__)
    repo_dir = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))

    expected = ExampleResult(
        effective_batch_size=8,
        lr_schedule=make_lr_schedule(base_lr=1e-3, total_steps=6, min_lr_ratio=0.1),
    )

    gin_stdout = run_command(
        args=[sys.executable, "train.py", "--gin_file", "experiments/second.gin"],
        cwd=os.path.join(script_dir, "gin"),
    )
    gin_result = parse_trainer_lines(gin_stdout)

    hydra_stdout = run_command(
        args=[sys.executable, "train.py", "experiment=second"],
        cwd=os.path.join(script_dir, "hydra"),
    )
    hydra_result = parse_trainer_lines(hydra_stdout)

    pconfigs_stdout = run_command(
        args=[sys.executable, "-m", "pconfigs.print", "project.experiments.second.config"],
        cwd=script_dir,
    )
    pconfigs_result = parse_pconfigs_print(pconfigs_stdout)

    if gin_result.effective_batch_size != expected.effective_batch_size:
        raise AssertionError(
            f"Gin effective_batch_size mismatch: {gin_result.effective_batch_size} vs {expected.effective_batch_size}"
        )

    if hydra_result.effective_batch_size != expected.effective_batch_size:
        raise AssertionError(
            f"Hydra effective_batch_size mismatch: {hydra_result.effective_batch_size} vs {expected.effective_batch_size}"
        )

    if pconfigs_result.effective_batch_size != expected.effective_batch_size:
        raise AssertionError(
            "pconfigs effective_batch_size mismatch: "
            f"{pconfigs_result.effective_batch_size} vs {expected.effective_batch_size}"
        )

    assert_close_lists(actual=gin_result.lr_schedule, expected=expected.lr_schedule)
    assert_close_lists(actual=hydra_result.lr_schedule, expected=expected.lr_schedule)
    assert_close_lists(actual=pconfigs_result.lr_schedule, expected=expected.lr_schedule)

    print("OK: gin/hydra/pconfigs schedules match expected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
