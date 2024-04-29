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
#  This software was developed with support from the Skanska USA,
#  Charles Pankow Foundation, Microsoft Sustainability Fund, Interface, MKA Foundation, and others.
#  Find out more at www.BuildingTransparency.org
#
from ilcdlib.dto import IlcdContactInfo, OpenEpdIlcdOrg, ValidationDto
from ilcdlib.epd.reader import IlcdEpdReader


class ItbIlcdXmlEpdReader(IlcdEpdReader):
    """Reader for EPDs in the Itb specific ILCD XML format."""

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
