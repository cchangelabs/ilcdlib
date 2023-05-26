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

from openepd.model.pcr import Pcr

from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader, OpenEpdPcrSupportReader
from ilcdlib.dto import IlcdReference
from ilcdlib.entity.contact import IlcdContactReader
from ilcdlib.type import LangDef
from ilcdlib.utils import create_openepd_attachments, none_throws
from ilcdlib.xml_parser import T_ET


class IlcdPcrReader(OpenEpdPcrSupportReader, IlcdXmlReader):
    """Read an ILCD PCR XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        contact_reader_cls: Type[IlcdContactReader] = IlcdContactReader,
    ):
        super().__init__(data_provider)
        self.contact_reader_cls = contact_reader_cls
        self._entity = element

    def get_own_reference(self) -> IlcdReference | None:
        """Get the reference to this data set."""
        return IlcdReference(entity_type="sources", entity_id=self.get_uuid(), entity_version=self.get_version())

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

    def get_name(self, lang: LangDef) -> str | None:
        """Get the name of the entity described by this data set."""
        return self._get_localized_text(
            self._entity, ("source:sourceInformation", "source:dataSetInformation", "common:shortName"), lang
        )

    def get_reference_to_contact_reader(self) -> IlcdContactReader | None:
        """Return the reader for the reference contact."""
        element = self._get_external_tree(
            self._entity,
            (
                "source:sourceInformation",
                "source:dataSetInformation",
                "source:referenceToContact",
            ),
        )
        return self.contact_reader_cls(element, self.data_provider) if element is not None else None

    def to_openepd_pcr(self, lang: LangDef, base_url: str | None = None) -> Pcr:
        """Read as OpenEPD Pcr object."""
        issuer_reader = self.get_reference_to_contact_reader()
        issuer = issuer_reader.to_openepd_org(lang) if issuer_reader is not None else None
        return Pcr.construct(
            name=self.get_name(lang),
            issuer=issuer,
            attachments=create_openepd_attachments(self.get_own_reference(), base_url),
        )
