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
from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader
from ilcdlib.const import IlcdContactClass
from ilcdlib.utils import none_throws
from ilcdlib.xml_parser import T_ET


class IlcdContactReader(IlcdXmlReader):
    """Reader for ILCD contact data sets."""

    def __init__(self, element: T_ET.Element, reader: BaseIlcdMediumSpecificReader):
        super().__init__(reader)
        self._entity = element

    def get_uuid(self) -> str:
        """Get the UUID of the entity described by this data set."""
        return none_throws(
            self._get_text(self._entity, ("contact:contactInformation", "contact:dataSetInformation", "common:UUID"))
        )

    def get_version(self) -> str | None:
        """Get the version of the entity described by this data set."""
        return self._get_text(
            self._entity,
            ("contact:administrativeInformation", "contact:publicationAndOwnership", "common:dataSetVersion"),
        )

    def get_name(self, lang: str) -> str | None:
        """Get the name of the entity described by this data set."""
        return self._get_localized_text(
            self._entity, ("contact:contactInformation", "contact:dataSetInformation", "common:name"), lang
        )

    def get_short_name(self, lang: str) -> str | None:
        """Get the short name of the entity described by this data set."""
        return self._get_localized_text(
            self._entity, ("contact:contactInformation", "contact:dataSetInformation", "common:shortName"), lang
        )

    def get_contact_class(self) -> IlcdContactClass | None:
        """Get the contact class of the contact by this data set."""
        ilcd_contact_class = self._get_text(
            self._entity,
            (
                "contact:contactInformation",
                "contact:dataSetInformation",
                "contact:classificationInformation",
                "common:classification[not(@class)]",
                "common:class[@level=0]",
            ),
        )
        if ilcd_contact_class is None:
            return None
        try:
            return IlcdContactClass(ilcd_contact_class)
        except ValueError:
            return None

    def get_phone(self) -> str | None:
        """Get the phone number of the contact described by this data set."""
        return self._get_text(
            self._entity, ("contact:contactInformation", "contact:dataSetInformation", "contact:telephone")
        )

    def get_email(self) -> str | None:
        """Get the email address of the contact described by this data set."""
        return self._get_text(
            self._entity, ("contact:contactInformation", "contact:dataSetInformation", "contact:email")
        )

    def get_website(self) -> str | None:
        """Get the website of the contact described by this data set."""
        return self._get_text(
            self._entity, ("contact:contactInformation", "contact:dataSetInformation", "contact:WWWAddress")
        )

    def get_address(self) -> str | None:
        """Get the address of the contact described by this data set."""
        return self._get_text(
            self._entity, ("contact:contactInformation", "contact:dataSetInformation", "contact:contactAddress")
        )
