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
from ilcdlib.dto import Category
from ilcdlib.soda4lca.api_client import Soda4LcaXmlApiClient


class Soda4LcaXmlApiClient4x(Soda4LcaXmlApiClient):
    """
    API client for Soda4LCA 4.x.

    Documentation for the API is available at https://bitbucket.org/okusche/soda4lca/src/842d85bb3b3b8f77415f20b431bb7b0789fee68f/Doc/src/Service_API/Service_API.md.
    """

    def __init__(self, *args, **kwargs):
        super(Soda4LcaXmlApiClient4x, self).__init__(*args, **kwargs)

    def list_categories(self, category_system: str, data_type: str = "Process", lang: str = "en") -> list[Category]:
        """
        Return a flat list of all available categories for a given category system.

        :param str category_system: category system
        :param str data_type: type of dataset
        :param str lang: language
        """
        xml_doc = self._do_xml_request(
            "get",
            "/processes/categories/",
            params=dict(format="xml", lang=lang, catSystem="The International EPD System"),
        )
        reader = self.category_reader_cls(xml_doc)
        categories = reader.get_categories_flat_list_4x()

        result = categories.copy()

        for category in categories:
            result += self.__list_subcategories(category, lang)

        return result

    def __list_subcategories(self, category: Category, lang: str = "en") -> list[Category]:
        xml_doc = self._do_xml_request(
            "get", f"/processes/categories/{category.name}/subcategories", params=dict(format="xml", lang=lang)
        )
        reader = self.category_reader_cls(xml_doc)
        return reader.get_categories_flat_list_4x(parent=category)
