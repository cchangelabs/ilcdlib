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
import abc
from typing import IO, Literal, Self, TextIO, overload


class BaseIlcdMediumSpecificReader(metaclass=abc.ABCMeta):
    """
    Base class for medium specific readers.

    This class is used to read ILCD data from a specific medium, e.g. a zip file, http api, etc.
    """

    @overload
    def get_entity_stream(
        self, entity_type: str, entity_id: str, entity_version: str | None = None, *, binary: Literal[True]
    ) -> IO[bytes]:
        ...

    @overload
    def get_entity_stream(
        self, entity_type: str, entity_id: str, entity_version: str | None = None, *, binary: Literal[False] = False
    ) -> TextIO:
        ...

    @abc.abstractmethod
    def get_entity_stream(
        self, entity_type: str, entity_id: str, entity_version: str | None = None, *, binary: bool = False
    ) -> IO[bytes] | TextIO:
        """
        Get xml stream for the given entity.

        If you want to refer file by name only, you can use the entity_id and skip version parameter.

        :param entity_type: The type of the entity. e.g. "process", "contact", "flow", etc.
        :param entity_id: The id of the entity, typically a GUID.
        :param entity_version: The version of the entity e.g. 12.34.56
        :param binary: If True, the stream is opened in binary mode, otherwise in text mode.
        :raise: ValueError if the entity does not exist.
        """
        pass

    @abc.abstractmethod
    def entity_exists(self, entity_type: str, entity_id: str, entity_version: str | None = None) -> bool:
        """
        Check if the given entity exists.

        If you want to refer file by name only, you can use the entity_id and skip version parameter.

        :param entity_type: The type of the entity. e.g. "process", "contact", "flow", etc.
        :param entity_id: The id of the entity, typically a GUID.
        :param entity_version: The version of the entity e.g. 12.34.56
        """
        pass

    @abc.abstractmethod
    def close(self):
        """
        Close the reader and release any resources.

        This method is called automatically when used in a context manager.
        """
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(self, _type, value, traceback):
        self.close()
