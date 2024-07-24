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
import datetime
import io
import re
from typing import IO

import requests

from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.type import LangDef


class EnvirondecIlcdXmlEpdReader(IlcdEpdReader):
    """Reader for EPDs in the Environdec specific ILCD XML format."""

    _TIME_REPR_DESC_DELIMITER = "\r\n"
    _PATTERN_ENVIRONDEC_DETAIL_URL_V1 = re.compile(r"https://www.environdec.com/library/_\?Epd=\d+")
    _PATTERN_ENVIRONDEC_HTML_FRIENDLY_URL = re.compile(r'"friendlyUrl": ?"(epd\d+)"')
    _PATTERN_ENVIRONDEC_DETAIL_URL_v2 = re.compile(r"https://www.environdec.com/Detail/epd\d+")

    def get_epd_document_stream(self) -> IO[bytes] | None:
        """
        Download the EPD document from the Environdec API, if it is possible.

        In the case of Environdec EPD, the EPD document is not stored in the ILCD XML file, but is retrieved from the
        Environdec API and public EPD library.

        We will not use this method to get the EPD document link for OpenEPD,
        because it is a responsibility of the client to get related documents.
        """

        link = self.get_url_attachment("en")
        if not link:
            return None

        if re.match(self._PATTERN_ENVIRONDEC_DETAIL_URL_V1, link):
            # If we have an older url to product page, we need to parse the html response to get the friendly url
            # For example, https://www.environdec.com/library/_?Epd=14879
            response = requests.get(link)
            if not response.status_code == 200:
                return None
            foreign_ids = re.findall(self._PATTERN_ENVIRONDEC_HTML_FRIENDLY_URL, response.text)
            if not foreign_ids:
                return None
            foreign_id = foreign_ids[0]

        elif re.match(self._PATTERN_ENVIRONDEC_DETAIL_URL_v2, link):
            # If we have a newer url to product page, we can get it using url itself
            # For example, https://www.environdec.com/library/epd1452
            foreign_id = link.strip("/").split("/")[-1]
        else:
            # Otherwise, we can't get the foreign id
            return None

        response = requests.get(f"https://api.environdec.com/api/v1/EPDLibrary/EPD/{foreign_id}")
        if response.status_code != 200:
            return None
        document_id = response.json()["documents"][0]["id"]
        pdf_link = f"https://api.environdec.com/api/v1/EPDLibrary/Files/{document_id}/Data"
        pdf_response = requests.get(pdf_link)
        if pdf_response.status_code != 200:
            return None
        return io.BytesIO(pdf_response.content)

    def _get_url_attachments_v1(self, lang: LangDef) -> str | None:
        """Get the URL attachment from the Environdec specific ILCD XML document when the old link format is used."""
        element = self._get_external_tree(
            self.epd_el_tree,
            (
                "process:modellingAndValidation",
                "process:dataSourcesTreatmentAndRepresentativeness",
                "process:referenceToDataSource",
            ),
        )
        if not element:
            return None

        url = self._get_localized_text(
            element,
            ("source:sourceInformation", "source:dataSetInformation", "source:sourceDescriptionOrComment"),
            lang,
        )

        return url

    def _get_url_attachment_v2(self, lang: LangDef) -> str | None:
        """Get the URL attachment from the Environdec specific ILCD XML document when the new link format is used."""
        external_tree = self._get_external_tree(
            self.epd_el_tree,
            (
                "process:modellingAndValidation",
                "process:dataSourcesTreatmentAndRepresentativeness",
                "common:other",
                "epd2019:referenceToOriginalEPD",
            ),
        )
        if not external_tree:
            return None

        el = self._get_el(
            external_tree,
            ("source:sourceInformation", "source:dataSetInformation", "source:referenceToDigitalFile"),
        )
        url = el.attrib.get("uri") if el is not None and el.attrib is not None else None
        return url

    def get_url_attachment(self, lang: LangDef) -> str | None:
        """Return URL attachment if exists."""
        url = self._get_url_attachments_v1(lang)
        if not url:
            url = self._get_url_attachment_v2(lang)

        if not url or "environdec.com" not in url:
            return None

        return url

    def get_validity_ends_date(self) -> datetime.date | None:
        """Return the date the EPD is valid until."""
        descr = self.__get_time_repr_description()
        if descr and self._TIME_REPR_DESC_DELIMITER in descr:
            try:
                date_str = descr.split(self._TIME_REPR_DESC_DELIMITER)[1].strip().rsplit(" ", 1)[-1].strip()
                return datetime.date.fromisoformat(date_str)
            except Exception:
                pass
        return super().get_validity_ends_date()

    def get_date_published(self) -> datetime.date | None:
        """Return the date the EPD was published."""
        descr = self.__get_time_repr_description()
        if descr and self._TIME_REPR_DESC_DELIMITER in descr:
            try:
                date_str = descr.split(self._TIME_REPR_DESC_DELIMITER)[0].strip().rsplit(" ", 1)[-1].strip()
                return datetime.date.fromisoformat(date_str)
            except Exception:
                pass
        return super().get_date_published()

    @classmethod
    def is_known_url(cls, url: str) -> bool:
        """Return whether the URL recognized as a known Environdec URL."""
        return "environdec" in url.lower()

    def __get_time_repr_description(self) -> str | None:
        return self._get_localized_text(
            self.epd_el_tree,
            (
                "process:processInformation",
                "process:time",
                "common:timeRepresentativenessDescription",
            ),
            ("en", None),
        )
