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
import json
from typing import Any, Generic, NamedTuple, Self

from openepd.model.base import BaseOpenEpdSchema
from openepd.model.org import Org
from openepd.model.specs import Specs

from ilcdlib.compat.pydantic import pyd
from ilcdlib.const import IlcdTypeOfReview
from ilcdlib.utils import T


class IlcdReference(NamedTuple):
    """A reference to an ILCD entity."""

    entity_type: str
    entity_id: str
    entity_version: str | None
    entity_uri: str | None = None

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


class Category(pyd.BaseModel):
    """A category DTO."""

    id: str
    name: str | None = None
    parent_id: str | None = None
    full_path: list[str] | None = None


class MappedCategory(Category):
    """Represent mapping between external classification and openEPD category."""

    comment: str | None = None
    openepd_category_original: str | None = None
    openepd_category_id: str | None = None
    openepd_material_specs: dict[str, Any] = pyd.Field(default_factory=dict)

    @pyd.root_validator
    def parse_openepd_category_id(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Parse category id.

        The input string might be either just a name of the category or some human-readable name and category id in {}.
        """
        if "{" in (data.get("openepd_category_original", "") or ""):
            data["openepd_category_id"] = data["openepd_category_original"][
                : data["openepd_category_original"].index("{")
            ].strip()
        return data

    def openepd_material_specs_as_str(self) -> str:
        """Return openepd_material_specs as a string."""
        result: list[str] = []
        if not self.openepd_material_specs:
            return ""
        for prop_name, prop_val in self.openepd_material_specs.items():
            if prop_val == "TRUE" or prop_val == "FALSE":
                converted_value = prop_val
            elif isinstance(prop_val, str):
                converted_value = '"' + prop_val + '"'
            elif isinstance(prop_val, (int, float)):
                converted_value = str(prop_val)
            else:
                converted_value = str(prop_val)
            result.append(f"{prop_name} = {converted_value}")
        return ", ".join(result)

    @classmethod
    def create_from(cls, other: Self) -> Self:
        """Create a new instance from another instance."""
        return cls.parse_obj(json.loads(other.json()))


class CategoryCandidate(pyd.BaseModel):
    """Class holding information about potential category and related properties for the given object."""

    category: str
    specs: Specs = pyd.fields.Field(default_factory=Specs)


class ListResponseMeta(pyd.BaseModel):
    """Metadata for a list response."""

    offset: int
    total_items_count: int
    page_size: int


class ProcessBasicInfo(pyd.BaseModel):
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

    contact_person: str | None = pyd.Field(description="Name of the contact person", example="John Doe", default=None)
    email: pyd.EmailStr | None = pyd.Field(description="Email", example="contact@c-change-labs.com", default=None)
    phone: str | None = pyd.Field(description="Phone number", example="+15263327352", default=None)
    website: pyd.AnyUrl | None = pyd.Field(
        description="Url of the website", example="http://buildingtransparency.org", default=None
    )
    address: str | None = pyd.Field(description="Address", example="123 Main St, San Francisco, CA 94105", default=None)


class OpenEpdIlcdOrg(Org):
    """Org object with ILCD specific extension."""

    def get_contact(self) -> IlcdContactInfo | None:
        """Return ILCD contact information from extension field if any."""
        from ilcdlib.extension import IlcdOrgExtension

        ext = self.get_ext(IlcdOrgExtension)
        return ext.contact if ext else None


class ComplianceDto(pyd.BaseModel):
    """Basic information about a Compliance."""

    uuid: str
    short_name: str | None
    name: str | None
    link: str | None
    issuer: OpenEpdIlcdOrg | None


class ValidationDto(pyd.BaseModel):
    """Basic information about a Compliance."""

    validation_type: IlcdTypeOfReview | None
    org: OpenEpdIlcdOrg
