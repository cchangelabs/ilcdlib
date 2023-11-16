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
from typing import IO

from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader
from ilcdlib.dto import IlcdReference
from ilcdlib.type import LangDef
from ilcdlib.utils import none_throws
from ilcdlib.xml_parser import T_ET


class IlcdSourceReader(IlcdXmlReader):
    """Reader that can parse an ILCD Standard specification from an XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
    ):
        super().__init__(data_provider)
        self._entity = element

    def get_uuid(self) -> str:
        """Get the UUID of the entity described by this data set."""
        return none_throws(
            self._get_text(self._entity, ("source:sourceInformation", "source:dataSetInformation", "common:UUID"))
        )

    def get_version(self) -> str | None:
        """Get the version of the entity described by this data set."""
        return self._get_text(
            self._entity,
            ("source:administrativeInformation", "source:publicationAndOwnership", "common:dataSetVersion"),
        )

    def get_own_reference(self) -> IlcdReference | None:
        """Get the reference to this data set."""
        return IlcdReference(entity_type="sources", entity_id=self.get_uuid(), entity_version=self.get_version())

    def get_short_name(self, lang: LangDef) -> str | None:
        """Get the short name of the entity described by this data set."""
        short_name = self._get_localized_text(
            self._entity, ("source:sourceInformation", "source:dataSetInformation", "common:shortName"), lang
        )
        return short_name

    def get_name(self, lang: LangDef) -> str | None:
        """Get the full name of the entity described by this data set."""
        return self._get_localized_text(
            self._entity,
            ("source:sourceInformation", "source:dataSetInformation", "source:sourceDescriptionOrComment"),
            lang,
        )

    def get_ref_to_digital_file(self) -> str | None:
        """Get the link to the digital file."""
        el = self._get_el(
            self._entity,
            ("source:sourceInformation", "source:dataSetInformation", "source:referenceToDigitalFile"),
        )
        return el.attrib.get("uri") if el is not None and el.attrib is not None else None

    def get_digital_file_stream(self) -> IO[bytes] | None:
        """Get the stream to the digital file."""
        ref = self.get_ref_to_digital_file()
        if ref:
            return self.data_provider.get_binary_stream_by_name(ref)
        return None
