#
#  Copyright 2023 by C Change Labs Inc. www.c-change-labs.com
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
#  This software was developed with support from the Skanska USA,
#  Charles Pankow Foundation, Microsoft Sustainability Fund, Interface, MKA Foundation, and others.
#  Find out more at www.BuildingTransparency.org
#
__all__ = (
    "BaseDataMapper",
    "SimpleDataMapper",
)

import abc
from typing import Generic, TypeVar

T = TypeVar("T")
K = TypeVar("K")


class BaseDataMapper(Generic[T, K], abc.ABC):
    """Base class for all data mappers."""

    @abc.abstractmethod
    def map(self, input_value: T, default_value: K) -> K:
        """
        Map the input value to the output value.

        :param input_value: The input value to map.
        :param default_value: The default value to return if there is no mapping for input value.
        """
        pass


class SimpleDataMapper(BaseDataMapper[T, T], Generic[T]):
    """A data mapper that does not change the type of the input value."""

    DATABASE: dict[T, T] = {}

    def map(self, input_value: T, default_value: T) -> T:
        """
        Map the input value to the output value.

        :param input_value: The input value to map.
        :param default_value: The default value to return if there is no mapping for input value.
        """
        return self.DATABASE.get(input_value, default_value)
