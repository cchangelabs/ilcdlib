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
from typing import Type

from ilcdlib.epd.dialect.environdec import EnvirondecIlcdXmlEpdReader
from ilcdlib.epd.dialect.indata import IndataIlcdXmlEpdReader
from ilcdlib.epd.dialect.oekobaudat import OekobauDatIlcdXmlEpdReader
from ilcdlib.epd.reader import IlcdEpdReader


class EpdReaderFactory:
    """Factory for creating EPD readers."""

    __DIALECTS: dict[str, Type[IlcdEpdReader]] = {
        "environdec": EnvirondecIlcdXmlEpdReader,
        "indata": IndataIlcdXmlEpdReader,
        "oekobau.dat": OekobauDatIlcdXmlEpdReader,
        "oekobaudat": OekobauDatIlcdXmlEpdReader,
    }
    DEFAULT_READER_CLASS = IlcdEpdReader

    def get_supported_dialects(self) -> list[str]:
        """Return a list of supported dialects."""
        return list(self.__DIALECTS.keys())

    def is_dialect_supported(self, dialect: str):
        """Return `True` if the dialect is supported, `False` otherwise."""
        return dialect.lower() in self.__DIALECTS

    def get_reader_class_or_default(self, dialect: str | None) -> Type[IlcdEpdReader]:
        """
        Return the reader class for the dialect.

        If dialect is `None` or if dialect is not supported return the default reader class.
        """
        if dialect is None:
            return self.DEFAULT_READER_CLASS
        dialect = dialect.lower()
        if dialect not in self.__DIALECTS:
            return self.DEFAULT_READER_CLASS
        return self.__DIALECTS[dialect]

    def get_reader_class(self, dialect: str | None) -> Type[IlcdEpdReader]:
        """
        Return the reader class for the dialect or throw an error.

        If dialect is `None` the default dialect will be returned.
        If dialect is not supported  - raise an ValueError.
        """
        if dialect is None:
            return self.DEFAULT_READER_CLASS
        dialect = dialect.lower()
        if dialect not in self.__DIALECTS:
            raise ValueError(f"Unknown dialect: {dialect}.")
        return self.__DIALECTS[dialect]

    def autodiscover_by_url(self, url: str) -> tuple[Type[IlcdEpdReader], str]:
        """
        Return the reader class for the dialect.

        If nothing recognized, return the default reader class.

        @:return tuple of reader class and dialect name
        """
        if url.startswith("http"):
            for name, cls in self.__DIALECTS.items():
                if cls.is_known_url(url):
                    return cls, name
        return self.DEFAULT_READER_CLASS, "default"
