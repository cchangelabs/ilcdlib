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
from typing import Any, Generic, NamedTuple

from openepd.model.base import BaseOpenEpdSchema
from openepd.model.org import Org
import pydantic
import pydantic as pyd

from ilcdlib.const import IlcdTypeOfReview
from ilcdlib.utils import T


class IlcdReference(NamedTuple):
    """A reference to an ILCD entity."""

    entity_type: str
    entity_id: str
    entity_version: str | None

    def to_url(self, base_url: str | None) -> str:
        """Convert the reference to a URL."""
        prefix = base_url if base_url is not None else "https://unknown.tld"
        if prefix.endswith("/"):
            prefix = prefix[:-1]
        prefix = prefix.removesuffix("/resource")
        return f"{prefix}/resource/{self.entity_type}/{self.entity_id}?version={self.entity_version}"


class ProductClassDef(NamedTuple):
    """A product class definition."""

    id: str | None
    name: str | None


class Category(pydantic.BaseModel):
    """A category DTO."""

    id: str
    name: str | None = None
    parent_id: str | None = None
    full_path: list[str] | None = None


class ListResponseMeta(pydantic.BaseModel):
    """Metadata for a list response."""

    offset: int
    total_items_count: int
    page_size: int


class ProcessBasicInfo(pydantic.BaseModel):
    """Basic information about a process."""

    uuid: str
    name: str | None = None
    version: str | None = None
    class_id: str | None = None
    class_name: str | None = None
    classification_system: str | None = None
    type: str | None = None
    sub_type: str | None = None
    original: dict[str, Any] | None = None

    def to_ilcd_ref(self) -> IlcdReference:
        """Return ILCD reference to this object."""
        return IlcdReference(entity_type="processes", entity_id=self.uuid, entity_version=self.version)


class BaseSearchResponse(Generic[T]):
    """Base class for search responses."""

    def __init__(self, meta: ListResponseMeta, items: list[T]):
        """Initialize the response."""
        self.meta = meta
        self.items = items


class ProcessSearchResponse(BaseSearchResponse[ProcessBasicInfo]):
    """A search response for processes."""

    pass


class IlcdContactInfo(BaseOpenEpdSchema):
    """Contact information extracted from ILCD contact."""

    contact_person: str | None = pyd.Field(
        default=None,
        description="Name of the contact person",
        json_schema_extra=dict(example="John Doe"),
    )
    email: pyd.EmailStr | None = pyd.Field(
        default=None,
        description="Email",
        json_schema_extra=dict(example="contact@c-change-labs.com"),
    )
    phone: str | None = pyd.Field(
        default=None,
        description="Phone number",
        json_schema_extra=dict(example="+15263327352"),
    )
    website: pyd.AnyUrl | None = pyd.Field(
        default=None,
        description="Url of the website",
        json_schema_extra=dict(example="http://buildingtransparency.org"),
    )
    address: str | None = pyd.Field(
        default=None,
        description="Address",
        json_schema_extra=dict(example="123 Main St, San Francisco, CA 94105"),
    )


class OpenEpdIlcdOrg(Org):
    """Org object with ILCD specific extension."""

    def get_contact(self) -> IlcdContactInfo | None:
        """Return ILCD contact information from extension field if any."""
        from ilcdlib.extension import IlcdOrgExtension

        ext = self.get_ext(IlcdOrgExtension)
        return ext.contact if ext else None


class ComplianceDto(pydantic.BaseModel):
    """Basic information about a Compliance."""

    uuid: str
    short_name: str | None = None
    name: str | None = None
    link: str | None = None
    issuer: OpenEpdIlcdOrg | None = None


class ValidationDto(pydantic.BaseModel):
    """Basic information about a Compliance."""

    validation_type: IlcdTypeOfReview | None = None
    org: OpenEpdIlcdOrg
