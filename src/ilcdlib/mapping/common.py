#
#  Copyright 2024 by C Change Labs Inc. www.c-change-labs.com
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
__all__ = (
    "BaseDataMapper",
    "SimpleDataMapper",
)

import abc
import re
from typing import Generic, TypeVar, cast

T = TypeVar("T")
K = TypeVar("K")


class BaseDataMapper(Generic[T, K], abc.ABC):
    """Base class for all data mappers."""

    @abc.abstractmethod
    def map(self, input_value: T, default_value: K | None) -> K | None:
        """
        Map the input value to the output value.

        :param input_value: The input value to map.
        :param default_value: The default value to return if there is no mapping for input value.
        """
        pass


class SimpleDataMapper(BaseDataMapper[T, T], Generic[T]):
    """A data mapper that does not change the type of the input value."""

    DATABASE: dict[T, T] = {}

    def map(self, input_value: T, default_value: T | None) -> T | None:
        """
        Map the input value to the output value.

        :param input_value: The input value to map.
        :param default_value: The default value to return if there is no mapping for input value.
        """
        return self.DATABASE.get(input_value, default_value)


class KeyValueMapper(BaseDataMapper[str, T], Generic[T]):
    """A data mapper that maps input values to output values using keywords."""

    KV: dict[str, list[T]] = {}

    def map(self, input_value: str, default_value: T | None) -> T | None:
        """
        Map the input value to the output value using keywords.

        :param input_value: The input value to map.
        :param default_value: The default value to return if there is no mapping for input value.
        """
        for impact_name, keywords in self.KV.items():
            for keyword in keywords:
                if str(keyword).strip().lower() in input_value.strip().lower():
                    return cast(T, impact_name)
        return default_value


class RegexMapper(BaseDataMapper[str, T], Generic[T]):
    """A data mapper that maps input values to output values using regex."""

    PATTERNS: dict[str, str] = {}
    _compiled_patterns: dict[str, re.Pattern]

    def __init__(self) -> None:
        self._compiled_patterns: dict[str, re.Pattern] = {
            key: re.compile(pattern, re.IGNORECASE) for key, pattern in self.PATTERNS.items()
        }

    def map(self, input_value: str, default_value: T | None) -> T | None:
        """
        Map the input value to the output value using regex.

        :param input_value: The input value to map.
        :param default_value: The default value to return if there is no mapping for input value.
        """
        for impact_name, pattern in self._compiled_patterns.items():
            if pattern.search(input_value.strip().lower()):
                return cast(T, impact_name)
        return default_value
