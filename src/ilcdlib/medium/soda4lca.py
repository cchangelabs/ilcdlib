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
from dataclasses import dataclass
import io
from typing import IO
from urllib.parse import parse_qs

import urllib3
from urllib3.util import parse_url

from ilcdlib.dto import IlcdReference
from ilcdlib.medium.archive import ZipIlcdReader
from ilcdlib.soda4lca.api_client import Soda4LcaXmlApiClient
from ilcdlib.utils import none_throws

http = urllib3.PoolManager()


@dataclass(kw_only=True)
class IlcdRemotePointer:
    """A pointer to an ILCD resource on a remote server."""

    base_url: str
    ref: IlcdReference
    stock: str | None = None


class Soda4LcaZipReader(ZipIlcdReader):
    """A reader for ILCD zip archives exported from the SODA4LCA interface."""

    def __init__(self, endpoint: str):
        pointer = self.soda_endpoint_to_pointer(endpoint)
        if pointer.ref.entity_type != "processes":
            raise ValueError(f"Invalid endpoint {endpoint}. Must point to the process.")
        self._soda4lca_client = Soda4LcaXmlApiClient(pointer.base_url)
        self._ref = pointer.ref
        zip_url = self.create_zip_export_endpoint(pointer)
        zip_file = self.dowload_zip_archive(zip_url)
        super().__init__(zip_file)

    @classmethod
    def create_zip_export_endpoint(cls, pointer: IlcdRemotePointer) -> str:
        """Create a zip export endpoint from a remote pointer."""
        return (
            f"{pointer.base_url}/{pointer.ref.entity_type}/{pointer.ref.entity_id}/"
            f"zipexport?version={pointer.ref.entity_version}"
        )

    @classmethod
    def soda_endpoint_to_pointer(cls, endpoint: str) -> IlcdRemotePointer:
        """Convert an endpoint to a remote pointer."""
        try:
            parsed_url = parse_url(endpoint)
            parsed_qs = parse_qs(parsed_url.query)
        except ValueError as e:
            raise ValueError(f"Invalid endpoint {endpoint}") from e
        host: str = none_throws(parsed_url.scheme) + "://" + none_throws(parsed_url.host)
        base_url = host
        uuid: str | None = None
        datastock: str | None = None
        resource_type_name: str | None = None
        original_path = parsed_url.path or ""
        url_path = "/resource"
        if url_path in original_path:
            base_path_prefix = original_path.split("/resource", 1)[0]
            url_path = base_path_prefix + url_path if len(base_path_prefix) > 0 else url_path
        if original_path.endswith(".xhtml"):
            resource_type_name = original_path.rsplit("/", 1)[-1].replace(".xhtml", "").lower()
            resource_type_name = cls.__map_type_name(resource_type_name)
            uuid = parsed_qs.pop("uuid", [None])[0]  # type: ignore
            if "/datasetdetail" in original_path:
                url_path = original_path.split("/datasetdetail", 1)[0] + url_path
        else:
            path_components = original_path.split("/")
            for i, x in enumerate(path_components):
                if x == "resource":
                    if i + 2 > len(path_components):
                        raise ValueError(f"Invalid endpoint {endpoint}")
                    resource_type_name = path_components[i + 1]
                    uuid = path_components[i + 2]
                    if resource_type_name == "datastocks":
                        datastock = uuid
                        resource_type_name = path_components[i + 3]
                        uuid = path_components[i + 4]
                    break
        if uuid is None or resource_type_name is None:
            raise ValueError(f"Invalid endpoint {endpoint}")
        version: str | None = parsed_qs.pop("version", [None])[0]  # type: ignore
        datastock = parsed_qs.pop("datastock", [None])[0] if datastock is None else datastock  # type: ignore
        base_url += url_path
        return IlcdRemotePointer(
            base_url=base_url,
            stock=datastock,
            ref=IlcdReference(entity_type=resource_type_name, entity_version=version, entity_id=uuid),
        )

    def dowload_zip_archive(self, url: str) -> IO[bytes]:
        """Download a zip archive from a URL."""
        # TODO: Move this to dedicated class
        response = http.request("GET", url)
        if response.status == 200:
            return io.BytesIO(response.data)
        raise ValueError(f"Could not download zip archive from {url}. Status code: {response.status}")

    def get_pdf_url(self) -> str | None:
        """Get the URL to the PDF document if any."""
        return self._soda4lca_client.get_download_epd_document_link(self._ref.entity_id, self._ref.entity_version)

    def download_pdf(self) -> IO[bytes] | None:
        """Download the associated PDF document if any."""
        url = self.get_pdf_url()
        if url is None:
            return None
        response = http.request("GET", url)
        if response.status == 200:
            return io.BytesIO(response.data)
        raise ValueError(f"Could not download PDF from {url}. Status code: {response.status}")

    def resolve_entity_url(self, ref: IlcdReference, digital_file: str | None) -> str | None:
        """
        Resolve the url of the given entity.

        If `digital_file` parameter is set, the link to the associated digital file is returned.

        :param ref: reference to the entity
        :param digital_file: optional name of the file, if link to the file is needed.
        """
        return self._soda4lca_client.get_entity_url(ref, digital_file=digital_file, verify=False)

    @staticmethod
    def __map_type_name(in_: str) -> str:
        match in_:
            case "process" | "showprocess":
                return "processes"
            case _:
                return in_
