#
#  Copyright 2026 by C Change Labs Inc. www.c-change-labs.com
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from __future__ import annotations

from typing import TYPE_CHECKING, overload

from annotated_types import MaxLen

if TYPE_CHECKING:
    import pydantic as pyd


@overload
def trim_text(in_str: None, max_length: int, ellipsis: str = "...") -> None: ...


@overload
def trim_text(in_str: str, max_length: int, ellipsis: str = "...") -> str: ...


def trim_text(in_str: str | None, max_length: int, ellipsis: str = "...") -> str | None:
    """Trim a string to a maximum length."""
    if in_str is None:
        return None
    if len(in_str) <= max_length:
        return in_str
    ellipsis = ellipsis[:max_length]
    return in_str[: max_length - len(ellipsis)] + ellipsis


@overload
def trim_to_model_field_max_length(
    model_type: type[pyd.BaseModel],
    field_name: str,
    value: None,
    *,
    ellipsis: str = "...",
) -> None: ...


@overload
def trim_to_model_field_max_length(
    model_type: type[pyd.BaseModel],
    field_name: str,
    value: str,
    *,
    ellipsis: str = "...",
) -> str: ...


def trim_to_model_field_max_length(
    model_type: type[pyd.BaseModel],
    field_name: str,
    value: str | None,
    *,
    ellipsis: str = "...",
) -> str | None:
    """Trim a value to the maximum length defined for a model field.

    :param model_type: Pydantic model containing the field.
    :param field_name: Name of the model field whose length constraint to use.
    :param value: Text to trim, or ``None``.
    :param ellipsis: Text to append when the value is trimmed.
    :return: The trimmed text, or the original value when no maximum is defined.
    """
    maximum_length = next(
        (
            constraint.max_length
            for constraint in model_type.model_fields[field_name].metadata
            if isinstance(constraint, MaxLen)
        ),
        None,
    )
    if maximum_length is None:
        return value
    return trim_text(value, maximum_length, ellipsis=ellipsis)
