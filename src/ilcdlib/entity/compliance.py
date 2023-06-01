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

from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader
from ilcdlib.dto import ComplianceDto
from ilcdlib.type import LangDef
from ilcdlib.xml_parser import T_ET

from .source import IlcdSourceReader


class IlcdComplianceReader(IlcdSourceReader):
    """Reader that can parse a single ILCD Standard specification from an XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
    ):
        super().__init__(element, data_provider)
        self._entity = element

    def get_compliance(self, lang: LangDef, base_url: str | None = None) -> ComplianceDto:
        """Return single compliance entity."""
        ref = self.get_own_reference()
        return ComplianceDto(
            uuid=self.get_uuid(),
            short_name=self.get_short_name(lang),
            name=self.get_name(lang),
            link=ref.to_url(base_url) if ref and base_url else None,
            issuer=None,  # haven't found examples
        )


class IlcdComplianceListReader(IlcdXmlReader):
    """Reader that can parse an ILCD Standard specifications from an XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        compliance_reader_cls: Type[IlcdComplianceReader] = IlcdComplianceReader,
    ):
        super().__init__(data_provider)
        self._entity = element
        self.compliance_reader_cls = compliance_reader_cls

    def _get_compliance_elements(self):
        compliance_els = self._get_all_els(self._entity, ("process:compliance",))
        return compliance_els

    def get_compliances(self, lang: LangDef, base_url: str | None = None) -> list[ComplianceDto]:
        """Return all compliance data."""
        result = []
        for compliance_el in self._get_compliance_elements():
            tree = self._get_external_tree(compliance_el, ("common:referenceToComplianceSystem",))
            if tree is None:
                continue
            if standard := IlcdComplianceReader(tree, self.data_provider):
                result.append(standard.get_compliance(lang, base_url))
        return result
