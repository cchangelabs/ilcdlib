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

from ilcdlib.dto import OpenEpdIlcdOrg
from ilcdlib.entity.contact import IlcdContactReader
from ilcdlib.entity.flow import UriBasedIlcdFlowReader
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.type import LangDef


class EpdDenmarkIlcdXmlEpdReader(IlcdEpdReader):
    """Reader for EPDs in the Denmark specific ILCD XML format."""

    DENMARK_LANG_CODE: str = "da"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs, flow_reader_cls=UriBasedIlcdFlowReader)

    @classmethod
    def is_known_url(cls, url: str) -> bool:
        """Return whether the URL recognized as a known Denmark URL."""
        # Note: While Denmark EPDs contain the term "ecosmdp" in their URLs, this is not a unique identifier,
        # and no specific URL pattern can be reliably associated with Denmark EPDs alone.
        return False

    def get_program_operator(
        self,
        program_operator_reader: IlcdContactReader | None,
        lang: LangDef,
        base_url: str | None = None,
        provider_domain: str | None = None,
    ) -> OpenEpdIlcdOrg | None:
        """Return the program operator."""
        if not program_operator_reader:
            program_operator_name = self._get_localized_text(
                self.epd_el_tree,
                (
                    "process:administrativeInformation",
                    "process:publicationAndOwnership",
                    "common:referenceToRegistrationAuthority",
                    "common:shortDescription",
                ),
                ("en", None),
            )
            if program_operator_name:
                return OpenEpdIlcdOrg(name=program_operator_name)
        return super().get_program_operator(program_operator_reader, lang, base_url, provider_domain)

    def get_lang_code(self, lang: LangDef) -> str | None:
        """Return the language of the PDF."""
        pdf_title = self._get_localized_text(
            self.epd_el_tree,
            (
                "process:modellingAndValidation",
                "process:dataSourcesTreatmentAndRepresentativeness",
                "common:other",
                "epd2019:referenceToOriginalEPD",
                "common:shortDescription",
            ),
            ("en", None),
        )
        return (
            self.DENMARK_LANG_CODE
            if pdf_title and pdf_title.lower().endswith(f"-{self.DENMARK_LANG_CODE}")
            else super().get_lang_code(lang)
        )
