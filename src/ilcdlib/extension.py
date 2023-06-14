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
from openepd.model.base import BaseOpenEpdSchema, OpenEpdExtension
from openepd.model.org import Org
import pydantic as pyd

from ilcdlib import const


class IlcdEpdExtension(OpenEpdExtension):
    """An ILCD extension for OpenEPD Epd object."""

    dataset_type: str | None = None
    dataset_version: str | None = None
    dataset_uuid: str | None = None
    production_location: str | None = None
    epd_publishers: list["OpenEpdIlcdOrg"] = pyd.Field(default_factory=list, description="List of EPD publishers")

    @classmethod
    def get_extension_name(cls) -> str:
        """Return the name of the extension to be used as a key in ext dict."""
        return const.ILCD_IDENTIFICATION[0]


class IlcdContactInfo(BaseOpenEpdSchema):
    """Contact information extracted from ILCD contact."""

    contact_person: str | None = pyd.Field(description="Name of the contact person", example="John Doe", default=None)
    email: pyd.EmailStr | None = pyd.Field(description="Email", example="contact@c-change-labs.com", default=None)
    phone: str | None = pyd.Field(description="Phone number", example="+15263327352", default=None)
    website: pyd.AnyUrl | None = pyd.Field(
        description="Url of the website", example="http://buildingtransparency.org", default=None
    )
    address: str | None = pyd.Field(description="Address", example="123 Main St, San Francisco, CA 94105", default=None)


class IlcdOrgExtension(OpenEpdExtension):
    """Extension to the Org object to store ILCD specific information."""

    contact: IlcdContactInfo | None = None

    @classmethod
    def get_extension_name(cls) -> str:
        """Return the name of the extension to be used as a key in ext dict."""
        return const.ILCD_IDENTIFICATION[0]


class OpenEpdIlcdOrg(Org):
    """Org object with ILCD specific extension."""

    def get_contact(self) -> IlcdContactInfo | None:
        """Return ILCD contact information from extension field if any."""
        ext = self.get_ext(IlcdOrgExtension)
        return ext.contact if ext else None
