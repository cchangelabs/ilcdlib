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
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.type import LangDef


class EpdItalyIlcdXmlEpdReader(IlcdEpdReader):
    """Reader for EPDs in the EpdItaly specific ILCD XML format."""

    @classmethod
    def is_known_url(cls, url: str) -> bool:
        """Return whether the URL recognized as a known Environdec URL."""
        return "epditaly" in url.lower()

    def post_init(self):
        """Configure EpdItaly specific settings."""
        self.xml_parser.xml_ns["epd2019"] = self.xml_parser.xml_ns["epd2019_indata"]

    def get_scenario_names(self, lang: LangDef) -> dict[str, str]:
        """Return dictionary with mapping short scenario names to full names in given language."""
        scenarios = self._get_all_els(
            self.epd_el_tree,
            (
                "process:processInformation",
                "process:dataSetInformation",
                "common:other",
                "epd2013:scenarios",
                "epd2013:scenario",
            ),
        )

        result: dict[str, str] = dict()

        for scenario in scenarios:
            if not scenario.attrib:
                continue

            short_name = scenario.attrib.get("{http://www.iai.kit.edu/EPD/2013}name")

            if short_name:
                result[short_name] = short_name

        return result
