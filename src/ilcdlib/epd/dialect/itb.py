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
from typing import Any

from ilcdlib.dto import IlcdContactInfo, OpenEpdIlcdOrg, ValidationDto
from ilcdlib.entity.flow import UriBasedIlcdFlowReader
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.type import LangDef


class ItbIlcdXmlEpdReader(IlcdEpdReader):
    """Reader for EPDs in the Itb specific ILCD XML format."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs, flow_reader_cls=UriBasedIlcdFlowReader)

    @classmethod
    def is_known_url(cls, url: str) -> bool:
        """Return whether the URL recognized as a known Itb URL."""
        return "itb" in url.lower()

    def get_third_party_verifier_email(self, validations: list[ValidationDto]) -> OpenEpdIlcdOrg | None:
        """
        Return first third party verifier email.

        ITB contains personal info instead of organization info.
        """
        verifier = self.get_third_party_verifier(validations)
        if not verifier:
            return None
        contact = verifier.get_contact()
        if contact is None:
            return None
        return IlcdContactInfo.parse_obj(contact).email

    def get_product_description(self, lang: LangDef) -> str | None:
        """Return the product description in the given language."""
        return self._get_localized_text(
            self.epd_el_tree,
            ("process:processInformation", "process:technology", "process:technologicalApplicability"),
            lang,
        )
