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
from ilcdlib.dto import MappedCategory, ProductClassDef
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.mapping.category import CsvCategoryMapper
from ilcdlib.utils import none_throws


class OekobauDatCategoryMapper(CsvCategoryMapper):
    """A category mapper for Oekobau.DAT."""

    @classmethod
    def preprocess_mapped_category(cls, mapped_category: MappedCategory, full_name: str) -> None:
        """Preprocess mapped category to extract parent ID from the dotted path."""
        super().preprocess_mapped_category(mapped_category, full_name)
        # We know that external IDs in oekobaudat are dot separated path in hierarchy so the parent id
        # is everything before the last dot
        if "." in mapped_category.id and mapped_category.parent_id is None:
            mapped_category.parent_id = mapped_category.id.rsplit(".", 1)[0]

    def map(self, input_value: str, default_value: list[MappedCategory] | None) -> list[MappedCategory] | None:
        """Map the oekobaudat classifier to a list of MappedCategory objects."""
        # We expect just class ID (like 1.2.3) however we might get ID and name separated by space like "1.2.3 Cement"
        # so we need to get rid of the name before actual mapping
        if " " in input_value:
            input_value = input_value.split(" ")[0]
        return super().map(input_value, default_value)


class OekobauDatIlcdXmlEpdReader(IlcdEpdReader):
    """Reader for EPDs in the Oekobau.DAT specific ILCD XML format."""

    OEKOBAUDAT_CLASSIFICATION_NAME = "oekobau.dat"

    @classmethod
    def is_known_url(cls, url: str) -> bool:
        """Return whether the URL recognized as a known Environdec URL."""
        return "oekobaudat" in url.lower()

    def post_init(self):
        """Configure Oekobau.DAT specific settings."""
        self.xml_parser.xml_ns["epd2019"] = self.xml_parser.xml_ns["epd2019_indata"]

    def _product_classes_to_openepd(self, classes: dict[str, list[ProductClassDef]]) -> dict[str, str]:
        """
        Convert the product classes to OpenEPD format.

        The Oekobau.DAT format according to openEPD is a string containing full id and
        the name of the most specific class. Example: "1.1.01 Cement"
        """
        result = super()._product_classes_to_openepd(classes)
        for classification_name, class_defs in classes.items():
            if classification_name.lower() == self.OEKOBAUDAT_CLASSIFICATION_NAME and len(class_defs) > 0:
                last_class = class_defs[-1]
                del result[classification_name]
                result[self.OEKOBAUDAT_CLASSIFICATION_NAME] = " ".join(
                    (none_throws(last_class.id), none_throws(last_class.name))
                )
        return result

    @classmethod
    def _create_category_mapper(cls, classification_name: str) -> CsvCategoryMapper | None:
        if classification_name.lower() == cls.OEKOBAUDAT_CLASSIFICATION_NAME:
            return OekobauDatCategoryMapper.from_file("oekobaudat.csv")
        return None
