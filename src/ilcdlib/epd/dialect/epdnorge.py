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
import datetime

from openepd.model.pcr import Pcr

from ilcdlib.dto import MappedCategory, OpenEpdIlcdOrg, ValidationDto
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

    def get_third_party_verifier(self, validations: list[ValidationDto]) -> OpenEpdIlcdOrg | None:
        """
        Return the third party verifier.

        EPD Norge contains personal info instead of organization info.
        """
        validation_reader = self.get_validation_reader()
        validation_el = validation_reader.entity if validation_reader else None
        reviewer_el = (
            self._get_el(validation_el[0], ("common:referenceToNameOfReviewerAndInstitution",))
            if validation_el
            else None
        )
        third_party_verifier = super().get_third_party_verifier(validations)
        if reviewer_el:
            reviewer_name = self._get_localized_text(reviewer_el, ("common:shortDescription",), ("en", None))
            if not reviewer_name:
                return third_party_verifier
            normalized_reviewer_name = reviewer_name.split("-")[0].strip()
            if not third_party_verifier:
                third_party_verifier = OpenEpdIlcdOrg(name=normalized_reviewer_name)
            else:
                third_party_verifier.name = normalized_reviewer_name
        return third_party_verifier

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

    def get_data_entry_by(self, lang: LangDef, base_url: str | None = None) -> OpenEpdIlcdOrg | None:
        """Return the data entry by org."""
        developer = self._get_localized_text(
            self.epd_el_tree,
            (
                "process:administrativeInformation",
                "process:dataGenerator",
                "common:referenceToPersonOrEntityGeneratingTheDataSet",
                "common:shortDescription",
            ),
            ("en", None),
        )
        if developer:
            return OpenEpdIlcdOrg(name=developer)
        return super().get_data_entry_by(lang, base_url)

    def get_pcr(self, lang: LangDef, base_url: str | None = None) -> Pcr | None:
        """Return the PCR."""
        pcr = super().get_pcr(lang, base_url)
        if pcr is not None and pcr.name:
            pcr.name = (
                pcr.name.replace("Product descriptions and scenarios are based on", "")
                .replace("This also applies for inorganic coatings", "")
                .strip()
            )
        return pcr
