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
from pathlib import Path

from ilcdlib.epd.factory import EpdReaderFactory
from ilcdlib.medium.archive import ZipIlcdReader
from ilcdlib.medium.soda4lca import Soda4LcaZipReader
from ilcdlib.soda4lca.api_client_4x import Soda4LcaXmlApiClient4x


class DefaultIlcdProvider:
    """Default ILCD provider for the bulk data processing."""

    @staticmethod
    def get_api_client(base_url: str) -> Soda4LcaXmlApiClient4x:
        """Create a new API client for the given base URL."""
        return Soda4LcaXmlApiClient4x(base_url)

    @staticmethod
    def get_reader_factory() -> EpdReaderFactory:
        """Create a new reader factory."""
        return EpdReaderFactory()

    @staticmethod
    def get_medium(doc_ref: str) -> ZipIlcdReader | Soda4LcaZipReader:
        """Get the medium for the given document reference."""
        return Soda4LcaZipReader(doc_ref) if doc_ref.startswith("http") else ZipIlcdReader(Path(doc_ref))
