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
#  This software was developed with support from the Skanska USA,
#  Charles Pankow Foundation, Microsoft Sustainability Fund, Interface, MKA Foundation, and others.
#  Find out more at www.BuildingTransparency.org
#
import datetime

from ilcdlib.dto import IlcdContactInfo, MappedCategory, OpenEpdIlcdOrg, ValidationDto
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.mapping.category import CsvCategoryMapper
from ilcdlib.type import LangDef


class EpdNorgeCategoryMapper(CsvCategoryMapper):
    """A category mapper for EpdNorge."""

    def map(self, input_value: str, default_value: list[MappedCategory] | None) -> list[MappedCategory] | None:
        """Map the EPD Norge classifier to a list of MappedCategory objects."""
        # For EpdNorge the input might be either just uid or uid separated by space from name.
        # e.g. '071f9a38-08af-4ee5-909a-9884e93816c0 Bygg / Teknisk-kjemiske byggevareprodukter'
        # In that case we drop the name and use just uuid
        if " " in input_value:
            input_value = input_value.split(" ")[0]
        return super().map(input_value, default_value)


class EpdNorgeIlcdXmlEpdReader(IlcdEpdReader):
    """Reader for EPDs in the EpdNorge specific ILCD XML format."""

    EPDNORGE_CLASSIFICATION_NAME = "epdnorge"
    _TIME_REPR_DESC_DELIMITER = "\r\n"

    @classmethod
    def is_known_url(cls, url: str) -> bool:
        """Return whether the URL recognized as a known EPD Norge URL."""
        normalized_url = url.lower()
        return "epdnorway" in normalized_url or "digi-norge" in normalized_url

    @classmethod
    def _create_category_mapper(cls, classification_name: str) -> CsvCategoryMapper | None:
        if classification_name.lower() == cls.EPDNORGE_CLASSIFICATION_NAME:
            return EpdNorgeCategoryMapper.from_file("epdnorge.csv")
        return None

    def get_third_party_verifier_email(self, validations: list[ValidationDto]) -> OpenEpdIlcdOrg | None:
        """
        Return first third party verifier email.

        EpdNorge contains personal info instead of organization info.
        """
        verifier = self.get_third_party_verifier(validations)
        if not verifier:
            return None
        contact = verifier.get_contact()
        if contact is None:
            return None
        return IlcdContactInfo.parse_obj(contact).email

    def get_product_description(self, lang: LangDef) -> str | None:
        """Return the product description in the given language."""
        return self._get_localized_text(
            self.epd_el_tree,
            ("process:processInformation", "process:technology", "process:technologicalApplicability"),
            lang,
        )

    def _get_time_repr_description(self) -> str | None:
        return self._get_localized_text(
            self.epd_el_tree,
            (
                "process:processInformation",
                "process:time",
                "common:timeRepresentativenessDescription",
            ),
            ("en", None),
        )

    def get_validity_ends_date(self) -> datetime.date | None:
        """Return the date the EPD is valid until."""
        descr = self._get_time_repr_description()
        if descr and self._TIME_REPR_DESC_DELIMITER in descr:
            try:
                date_str = descr.split(self._TIME_REPR_DESC_DELIMITER)[1].strip().rsplit(" ", 1)[-1].strip()
                return datetime.date.fromisoformat(date_str)
            except Exception:
                pass
        return super().get_validity_ends_date()

    def get_date_published(self) -> datetime.date | None:
        """Return the date the EPD was published."""
        descr = self._get_time_repr_description()
        if descr and self._TIME_REPR_DESC_DELIMITER in descr:
            try:
                date_str = descr.split(self._TIME_REPR_DESC_DELIMITER)[0].strip().rsplit(" ", 1)[-1].strip()
                return datetime.date.fromisoformat(date_str)
            except Exception:
                pass
        return super().get_date_published()
