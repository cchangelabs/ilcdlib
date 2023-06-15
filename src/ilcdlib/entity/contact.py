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

from openepd.model.common import Location

from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader, OpenEpdContactSupportReader
from ilcdlib.const import IlcdContactClass
from ilcdlib.dto import IlcdContactInfo, IlcdReference, OpenEpdIlcdOrg
from ilcdlib.extension import IlcdOrgExtension
from ilcdlib.sanitizing.domain import cleanup_website, domain_from_url
from ilcdlib.sanitizing.phone import cleanup_phone
from ilcdlib.type import LangDef
from ilcdlib.utils import create_openepd_attachments, none_throws, provider_domain_name_from_url
from ilcdlib.xml_parser import T_ET


class IlcdContactReader(OpenEpdContactSupportReader, IlcdXmlReader):
    """Reader for ILCD contact data sets."""

    def __init__(self, element: T_ET.Element, data_provider: BaseIlcdMediumSpecificReader):
        super().__init__(data_provider)
        self._entity = element

    def get_own_reference(self) -> IlcdReference | None:
        """Get the reference to this data set."""
        return IlcdReference(entity_type="contacts", entity_id=self.get_uuid(), entity_version=self.get_version())

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

    def to_openepd_org(
        self, lang: LangDef, base_url: str | None = None, provider_domain: str | None = None
    ) -> OpenEpdIlcdOrg:
        """Convert this data set to an OpenEPD org object."""
        open_epd_contact = IlcdContactInfo(
            email=self.get_email(),  # type: ignore
            phone=cleanup_phone(self.get_phone()),
            website=cleanup_website(self.get_website()),  # type: ignore
            address=self.get_address(),
        )
        org = OpenEpdIlcdOrg(
            name=self.get_name(lang),
            web_domain=domain_from_url(self.get_website()),  # type: ignore
            attachments=create_openepd_attachments(self.get_own_reference(), base_url)
            if base_url
            else None,  # type: ignore
        )
        if provider_domain is None:
            provider_domain = provider_domain_name_from_url(base_url)
        if open_epd_contact.address:
            org.hq_location = Location(address=open_epd_contact.address)
        org.set_alt_id(provider_domain, self.get_uuid())
        if open_epd_contact.has_values():
            org.set_ext(IlcdOrgExtension(contact=open_epd_contact))
        return org
