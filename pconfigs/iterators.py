# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from typing import Any, Iterable, Iterator, List, Optional, Tuple, TypeVar

IdentifyResult = Tuple[Any, Optional[bool], Optional[bool]]
T = TypeVar("T")


def pairs(iterable: Iterable[T], first=False, last=False) -> Tuple[Optional[T], T]:
    """Iterate over pairs of elements in an iterable. First returned pair is (None, Any) if first=True."""
    if isinstance(iterable, Iterator):
        raise ValueError(
            "pairs() requires an iterable, but you passed an iterator. Try passing list(iterable) instead."
        )

    itb = iter(iterable)
    ita = iter(iterable)
    a = None
    for b in itb:
        if a is not None or first:
            yield a, b

        a = next(ita, None)

    if last:
        yield a, None


def markfirst(iterable: Iterable) -> Iterator[IdentifyResult]:
    return markings(iterable, first=True, last=False)


def marklast(iterable: Iterable) -> Iterator[IdentifyResult]:
    return markings(iterable, first=False, last=True)


def markends(iterable: Iterable) -> Iterator[IdentifyResult]:
    return markings(iterable, first=True, last=True)


def markings(iterable: Iterable, first: bool = True, last: bool = True) -> Iterator[IdentifyResult]:
    """Iterates an iterable and provides first/last flags: yields value, is_first, is_last."""

    def result(value, is_first, is_last):
        rets = [value]
        if first:
            rets.append(is_first)
        if last:
            rets.append(is_last)

        return tuple(rets)

    num_iters = 0
    first_iter = True
    for curr in iterable:
        if first_iter:
            prev = curr
            first_iter = False
        else:
            if num_iters == 1:
                # Is first and not last element
                yield result(prev, True, False)
            else:
                # Is neither first nor last element
                yield result(prev, False, False)

            prev = curr

        num_iters += 1

    if num_iters == 1:
        # Is first and last element
        yield result(prev, True, True)

    elif num_iters > 1:
        # Is last element, and not first
        yield result(prev, False, True)


def indexed(data: List, indices: List):
    for index in indices:
        yield data[index]
