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
from ilcdlib.common import IlcdXmlReader, NoopBaseReader
from ilcdlib.dto import Category
from ilcdlib.xml_parser import T_ET


class CategorySystemReader(IlcdXmlReader):
    """Read an ILCD PCR XML file."""

    def __init__(
        self,
        element: T_ET.Element,
    ):
        super().__init__(NoopBaseReader())
        self._entity = element
        self.xml_parser.xml_ns["cat"] = "http://lca.jrc.it/ILCD/Categories"
        self.xml_parser.xml_ns["sapi"] = "http://www.ilcd-network.org/ILCD/ServiceAPI"

    def get_categories_flat_list(self, data_type: str) -> list[Category]:
        """Get the UUID of the entity described by this data set."""
        result: list[Category] = []
        root = self._get_all_els(self._entity, (f'cat:categories[@dataType="{data_type}"]',))
        for x in root:
            self.__process_categories(x, result, [])
        return result

    def get_categories_flat_list_4x(self, parent: Category | None = None) -> list[Category]:
        """Get list of categories from XML for Soda4lca 4.x."""
        result: list[Category] = []
        root = self._get_all_els(self._entity, ("sapi:category",))
        for x in root:
            result.append(
                Category(
                    id=x.attrib.get("classId"),
                    name=x.text,
                    parent_id=parent.id if parent else None,
                    full_path=([parent.name] if parent else []) + [x.text],
                )
            )
        return result

    def __process_categories(
        self, current_el: T_ET.Element, result: list[Category], parent_cats: list[Category]
    ) -> list[Category]:
        parent_id = current_el.attrib.get("id") if current_el.attrib else None
        processed_categories: list[Category] = []
        for cat_el in self._get_all_els(current_el, ("cat:category",)):
            cat_id = cat_el.attrib.get("id") if cat_el.attrib else None
            if cat_id is None:
                raise ValueError("Category element has no id attribute")
            cat_name = cat_el.attrib.get("name") if cat_el.attrib else None
            cat = Category(
                id=cat_id,
                name=cat_name,
                parent_id=parent_id,
                full_path=[x.name for x in parent_cats if x.name] + ([cat_name] if cat_name else []),
            )
            self.__process_categories(cat_el, result, parent_cats + [cat])
            result.append(cat)
            processed_categories.append(cat)
        return processed_categories
