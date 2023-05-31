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

from ilcdlib.dto import Category
from ilcdlib.entity.category import CategorySystemReader
from ilcdlib.http import BaseApiClient


class Soda4LcaXmlApiClient(BaseApiClient):
    """
    API client for Soda4LCA.

    Documentation for the API is available at https://bitbucket.org/okusche/soda4lca/src/7.x-branch/Doc/src/Service_API/Service_API.md.
    """

    def __init__(
        self, base_url: str, *, category_reader_cls: Type[CategorySystemReader] = CategorySystemReader, **kwargs
    ) -> None:
        """
        Create a new API client.

        :param base_url: Base API endpoint should be something like https://your-host.tld/resource
        :param kwargs: all kwargs supported by BaseApiClient
        """
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/resource"):
            base_url += "/resource"
        super().__init__(base_url, **kwargs)
        self.category_reader_cls = category_reader_cls

    def list_categories(self, category_system: str, data_type: str = "Process", lang: str = "en") -> list[Category]:
        """
        Return a flat list of all available categories for a given category system.

        :param str category_system: category system
        """
        xml_doc = self._do_xml_request(
            "get", f"/categorySystems/{self._urlencode(category_system)}", params=dict(format="xml", lang=lang)
        )
        reader = self.category_reader_cls(xml_doc)
        return reader.get_categories_flat_list(data_type)
