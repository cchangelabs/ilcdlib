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
from io import BytesIO
from typing import IO, Iterable, Type
from urllib.parse import urlencode

from requests import HTTPError

from ilcdlib.dto import Category, IlcdReference, ListResponseMeta, ProcessBasicInfo, ProcessSearchResponse
from ilcdlib.entity.category import CategorySystemReader
from ilcdlib.http_common import BaseApiClient


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

    def export_to_zip(self, ref: IlcdReference, stock: str | None = None) -> IO[bytes]:
        """
        Export an ILCD entity to a ZIP file.

        :param IlcdReference ref: reference to the entity
        :param str stock: stock ID (optional)
        """
        params = dict(format="zip")
        if stock is not None:
            params["stock"] = stock
        if ref.entity_version is not None:
            params["version"] = ref.entity_version
        response = self._do_request(
            "get",
            f"/{self._urlencode(ref.entity_type)}/{self._urlencode(ref.entity_id)}/zipexport",
            params=params,
            stream=True,
        )
        return BytesIO(response.content)

    def get_download_epd_document_link(self, process_uuid: str, version: str | None = None) -> str | None:
        """
        Get link to download an EPD document (typically in PDF format).

        This method performs a check if the document exists and returns None if it doesn't.

        :param str process_uuid: UUID of the process
        :param str version: version of the process (optional)
        """
        params = dict()
        if version is not None:
            params["version"] = version
        url = f"{self.base_url}/processes/{self._urlencode(process_uuid)}/epd" + "?" + urlencode(params)
        response = self._do_request("head", url, raise_for_status=False)
        return url if response.ok else None

    def download_epd_document(self, process_uuid: str, version: str | None = None) -> IO[bytes]:
        """
        Download an EPD document (typically in PDF format).

        :param str process_uuid: UUID of the process
        :param str version: version of the process (optional)
        :raise NotFoundError: if the process file does not exist
        """
        url = self.get_download_epd_document_link(process_uuid, version)
        if url is None:
            raise FileNotFoundError(f"Process {process_uuid} (ver={version}) doesn't have EPD document attached")
        try:
            response = self._do_request("get", url, stream=True)
            return BytesIO(response.content)
        except HTTPError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(
                    f"Process {process_uuid} (ver={version}) doesn't have EPD document attached"
                ) from e
            raise e

    def search_processes(
        self, offset: int = 0, page_size: int = 100, lang: str | None = None, **other_params
    ) -> ProcessSearchResponse:
        """
        Filter processes by various criteria.

        :param offset: offset from the beginning of the dataset
        :param page_size: size of the page
        :param lang: language code (2 letters)
        :param other_params: refer to Soda4LCA documentation for other parameters
        :return:
        """
        params = dict(
            format="json",
            startIndex=offset,
            pageSize=page_size,
            search="true",
            *other_params,
        )
        if lang is not None:
            params["lang"] = lang
            params["langFallback"] = True
        response = self._do_request("get", "/processes", params=params)
        obj = response.json()
        meta = ListResponseMeta(
            offset=obj.get("startIndex", 0),
            page_size=obj.get("pageSize", 0),
            total_items_count=obj.get("totalCount", 0),
        )
        items = []
        for x in obj.get("data", []):
            items.append(
                ProcessBasicInfo(
                    uuid=x.get("uuid"),
                    name=x.get("name"),
                    version=x.get("version"),
                    class_id=x.get("classificId"),
                    class_name=x.get("classific"),
                    classification_system=x.get("classificSystem"),
                    type=x.get("type"),
                    sub_type=x.get("subType"),
                    original=x,
                )
            )
        return ProcessSearchResponse(meta=meta, items=items)

    def get_processes_iter(
        self, offset: int = 0, page_size: int = 100, **search_params
    ) -> tuple[Iterable[ProcessBasicInfo], int]:
        """
        Return an iterator over all processes matching the given criteria.

        :param offset: offset from the beginning of the dataset
        :param page_size: size of the page
        :param search_params: refer to Soda4LCA documentation for search parameters
        :return:
        """
        response = self.search_processes(0, page_size=1, **search_params)
        return self._create_process_iterator(offset, page_size, **search_params), response.meta.total_items_count

    def _create_process_iterator(
        self, offset: int = 0, page_size: int = 100, **search_params
    ) -> Iterable[ProcessBasicInfo]:
        """
        Create an iterator over all processes matching the given criteria.

        :param search_params: refer to Soda4LCA documentation for other parameters
        :return:
        """
        has_next = True
        while has_next:
            response = self.search_processes(offset=offset, page_size=page_size, **search_params)
            for item in response.items:
                yield item
            total = response.meta.total_items_count
            processed_items_count = len(response.items)
            if processed_items_count == 0:
                has_next = False
            else:
                has_next = offset + processed_items_count <= total
            offset += processed_items_count
