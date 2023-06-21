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
from ilcdlib.dto import ProductClassDef
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.utils import none_throws


class OekobauDatIlcdXmlEpdReader(IlcdEpdReader):
    """Reader for EPDs in the Oekobau.DAT specific ILCD XML format."""

    @classmethod
    def is_known_url(cls, url: str) -> bool:
        """Return whether the URL recognized as a known Environdec URL."""
        return "oekobaudat" in url.lower()

    def _product_classes_to_openepd(self, classes: dict[str, list[ProductClassDef]]) -> dict[str, list[str] | str]:
        """
        Convert the product classes to OpenEPD format.

        The Oekobau.DAT format according to openEPD is a string containing full id and
        the name of the most specific class. Example: "1.1.01 Cement"
        """
        result = super()._product_classes_to_openepd(classes)
        for classification_name, class_defs in classes.items():
            if classification_name.lower() == "oekobau.dat" and len(class_defs) > 0:
                last_class = class_defs[-1]
                del result[classification_name]
                result["oekobau.dat"] = " ".join((none_throws(last_class.id), none_throws(last_class.name)))
        return result
