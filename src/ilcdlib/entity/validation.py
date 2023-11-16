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
from ilcdlib.dto import ValidationDto
from ilcdlib.type import LangDef
from ilcdlib.xml_parser import T_ET

from ..const import IlcdTypeOfReview
from .contact import IlcdContactReader


class IlcdValidationReader(IlcdXmlReader):
    """Reader that can parse a single ILCD validation specification from an XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        contact_reader_cls: Type[IlcdContactReader] = IlcdContactReader,
    ):
        super().__init__(data_provider)
        self._entity = element
        self.contact_reader_cls = contact_reader_cls

    def get_validation(
        self, lang: LangDef, base_url: str | None = None, provider_domain: str | None = None
    ) -> ValidationDto | None:
        """Return single validation entity."""
        tree = self._get_external_tree(self._entity, ("common:referenceToNameOfReviewerAndInstitution",))
        if tree is None:
            return None
        if contact := self.contact_reader_cls(tree, self.data_provider):
            review_type = self._entity.attrib.get("type")
            validation = ValidationDto(
                validation_type=IlcdTypeOfReview(review_type) if review_type else None,
                org=contact.to_openepd_org(lang, base_url, provider_domain),
            )
            return validation
        return None


class IlcdValidationListReader(IlcdXmlReader):
    """Reader that can parse an ILCD Validation specifications from an XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        validation_reader_cls: Type[IlcdValidationReader] = IlcdValidationReader,
    ):
        super().__init__(data_provider)
        self._entity = element
        self.validation_reader_cls = validation_reader_cls

    def get_validations(
        self, lang: LangDef, base_url: str | None = None, provider_domain: str | None = None
    ) -> list[ValidationDto]:
        """Return all validation data."""
        result = []
        for validation_el in self._entity:
            if validation_data := self.validation_reader_cls(validation_el, self.data_provider):
                if validation := validation_data.get_validation(lang, base_url, provider_domain):
                    result.append(validation)
        return result
