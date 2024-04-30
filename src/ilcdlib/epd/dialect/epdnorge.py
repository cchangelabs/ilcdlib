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
from ilcdlib.dto import MappedCategory
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.mapping.category import CsvCategoryMapper


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
