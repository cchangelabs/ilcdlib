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
from openepd.model.common import ExternalIdentification
from openepd.model.org import Contact, Org

from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader, OpenEpdContactSupportReader
from ilcdlib.const import IlcdContactClass
from ilcdlib.sanitizing.domain import domain_from_url
from ilcdlib.sanitizing.phone import cleanup_phone
from ilcdlib.type import LangDef
from ilcdlib.utils import create_openepd_identification, none_throws
from ilcdlib.xml_parser import T_ET


class IlcdContactReader(OpenEpdContactSupportReader, IlcdXmlReader):
    """Reader for ILCD contact data sets."""

    def __init__(self, element: T_ET.Element, data_provider: BaseIlcdMediumSpecificReader):
        super().__init__(data_provider)
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

    def get_name(self, lang: LangDef) -> str | None:
        """Get the name of the entity described by this data set."""
        return self._get_localized_text(
            self._entity, ("contact:contactInformation", "contact:dataSetInformation", "common:name"), lang
        )

    def get_short_name(self, lang: LangDef) -> str | None:
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
                "common:classification",  # "common:classification[not(@class)]",
                "common:class[@level='0']",
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

    def to_openepd_org(self, lang: LangDef) -> Org:
        """Convert this data set to an OpenEPD org object."""
        open_epd_contact = Contact.construct(
            email=self.get_email(),
            phone=cleanup_phone(self.get_phone()),
            website=self.get_website(),
        )
        identification = ExternalIdentification.construct(
            id=self.get_uuid(),
            version=self.get_version(),
        )
        return Org.construct(
            name=self.get_name(lang),
            web_domain=domain_from_url(self.get_website()),
            contacts=open_epd_contact if open_epd_contact.has_values() else None,
            identified=create_openepd_identification(identification),
        )
