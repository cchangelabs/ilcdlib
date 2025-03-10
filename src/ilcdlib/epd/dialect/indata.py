#
#  Copyright 2025 by C Change Labs Inc. www.c-change-labs.com
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


class IndataIlcdXmlEpdReader(IlcdEpdReader):
    """Reader for EPDs in the Indata specific ILCD XML format."""

    def post_init(self):
        """Configure Indata specific settings."""
        self.xml_parser.xml_ns["epd2019"] = "http://www.indata.network/EPD/2019"

    @classmethod
    def is_known_url(cls, url: str) -> bool:
        """Return whether the URL recognized as a known Environdec URL."""
        return "indata" in url.lower()
