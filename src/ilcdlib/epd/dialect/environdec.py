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
import datetime

from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.type import LangDef


class EnvirondecIlcdXmlEpdReader(IlcdEpdReader):
    """Reader for EPDs in the Environdec specific ILCD XML format."""

    _TIME_REPR_DESC_DELIMITER = "\r\n"

    def get_url_attachment(self, lang: LangDef) -> str | None:
        """Return URL attachment if exists."""
        element = self._get_external_tree(
            self.epd_el_tree,
            (
                "process:modellingAndValidation",
                "process:dataSourcesTreatmentAndRepresentativeness",
                "process:referenceToDataSource",
            ),
        )

        url = (
            self._get_localized_text(
                element,
                ("source:sourceInformation", "source:dataSetInformation", "source:sourceDescriptionOrComment"),
                lang,
            )
            if element
            else None
        )

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
