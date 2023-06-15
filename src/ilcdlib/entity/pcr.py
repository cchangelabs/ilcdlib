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

from ilcdlib import const
from ilcdlib.common import BaseIlcdMediumSpecificReader, OpenEpdPcrSupportReader
from ilcdlib.entity.contact import IlcdContactReader
from ilcdlib.entity.source import IlcdSourceReader
from ilcdlib.type import LangDef
from ilcdlib.utils import create_openepd_attachments, provider_domain_name_from_url
from ilcdlib.xml_parser import T_ET


class IlcdPcrReader(OpenEpdPcrSupportReader, IlcdSourceReader):
    """Read an ILCD PCR XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        contact_reader_cls: Type[IlcdContactReader] = IlcdContactReader,
    ):
        super().__init__(element, data_provider)
        self.contact_reader_cls = contact_reader_cls
        self._entity = element

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

    def get_references_to_digital_files(self) -> list[str]:
        """Return the references to digital files."""
        els = self._get_all_els(
            self._entity,
            (
                "source:sourceInformation",
                "source:dataSetInformation",
                "source:referenceToDigitalFile",
            ),
        )
        return [el.attrib["uri"] for el in els if el.attrib and "uri" in el.attrib]

    def to_openepd_pcr(self, lang: LangDef, base_url: str | None = None, provider_domain: str | None = None) -> Pcr:
        """Read as OpenEPD Pcr object."""
        issuer_reader = self.get_reference_to_contact_reader()
        issuer = issuer_reader.to_openepd_org(lang) if issuer_reader is not None else None
        reference = self.get_own_reference()
        pcr = Pcr(
            name=self.get_name(lang),
            issuer=issuer,
            attachments=create_openepd_attachments(reference, base_url) if base_url else None,  # type: ignore
        )
        if provider_domain is None:
            provider_domain = provider_domain_name_from_url(base_url)
        digital_files = self.get_references_to_digital_files()
        if len(digital_files) > 0 and reference is not None:
            pdf_url = self.data_provider.resolve_entity_url(reference, digital_files[0])
            pcr.set_attachment_if_any(const.PDF_ATTACHMENT, pdf_url)
        pcr.set_alt_id(provider_domain, self.get_uuid())
        return pcr
