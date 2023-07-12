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
from hashlib import sha1
from io import BytesIO
from typing import IO, Iterable, Type
from urllib.parse import urlencode

from requests import HTTPError, Response

from ilcdlib.dto import Category, IlcdReference, ListResponseMeta, ProcessBasicInfo, ProcessSearchResponse
from ilcdlib.entity.category import CategorySystemReader
from ilcdlib.http_common import BaseApiClient
from ilcdlib.xml_parser import T_ET


class Soda4LcaXmlApiClient(BaseApiClient):
    """
    API client for Soda4LCA.

    Documentation for the API is available at https://bitbucket.org/okusche/soda4lca/src/7.x-branch/Doc/src/Service_API/Service_API.md.
    """

    ns = {
        "p": "http://www.ilcd-network.org/ILCD/ServiceAPI/Process",
        "sapi": "http://www.ilcd-network.org/ILCD/ServiceAPI",
        "epd": "http://www.iai.kit.edu/EPD/2013",
    }

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
        url = f"{self.base_url}/processes/{self._urlencode(process_uuid)}/epd"
        if params:
            url += "?" + urlencode(params)
        response = self._do_request("head", url, raise_for_status=False)
        return url if response.ok else None

    def get_entity_url(self, ref: IlcdReference, digital_file: str | None, verify: bool = False) -> str | None:
        """Get URL to download an ILCD entity or a digital file attached to it."""
        params = dict()
        if ref.entity_version is not None:
            params["version"] = ref.entity_version
        url = f"{self.base_url}/{ref.entity_type}/{self._urlencode(ref.entity_id)}"
        if digital_file is not None:
            url += f"/{self._urlencode(digital_file)}"
        url += "?" + urlencode(params)
        if verify:
            response = self._do_request("head", url, raise_for_status=False)
            return url if response.ok else None
        return url

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
            format="xml",
            startIndex=offset,
            pageSize=page_size,
            search="true",
            **other_params,
        )
        if lang is not None:
            params["lang"] = lang
            params["langFallback"] = True
        response = self._do_request("get", "/processes", params=params)

        return self.__search_processes_xml(response)

    def __get_element_text(self, elem: T_ET.Element, path: str) -> str | None:
        child = elem.find(path, namespaces=self.ns)

        if child is not None:
            return child.text
        return None

    def __search_processes_xml(self, response: Response) -> ProcessSearchResponse:
        obj = response.text

        tree = T_ET.fromstring(obj)

        processes = tree.findall("p:process", namespaces=self.ns)

        meta = ListResponseMeta(
            offset=tree.attrib.get(f"{{{self.ns['sapi']}}}startIndex", 0),
            page_size=tree.attrib.get(f"{{{self.ns['sapi']}}}pageSize", 0),
            total_items_count=tree.attrib.get(f"{{{self.ns['sapi']}}}totalSize", 0),
        )
        items = []
        for process in processes:
            items.append(
                ProcessBasicInfo(
                    uuid=self.__get_element_text(process, "sapi:uuid"),
                    name=self.__get_element_text(process, "sapi:name"),
                    version=self.__get_element_text(process, "sapi:dataSetVersion"),
                    class_id=self.__get_element_text(process, "sapi:classId"),
                    class_name=self.__get_element_text(process, "sapi:classific"),
                    classification_system=self.__get_element_text(process, "sapi:classificSystem"),
                    type=self.__get_element_text(process, "p:type"),
                    sub_type=self.__get_element_text(process, "sapi:other/epd:subType"),
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

    def get_sha1_by_url(self, url: str) -> str:
        """
        Get SHA1 hash of the file at the given URL or raise error if it is impossible to fetch the file.

        :param url: URL of the file
        """
        response = self._do_request("get", url, stream=True)
        hasher = sha1()
        for x in response.iter_content(chunk_size=200):
            hasher.update(x)
        return hasher.hexdigest()

    def get_sha1_by_url_or_none(self, url: str) -> str | None:
        """
        Get SHA1 hash of the file at the given URL or return none if it is impossible to fetch the file.

        :param url: URL of the file
        """
        try:
            return self.get_sha1_by_url(url)
        except HTTPError:
            return None
