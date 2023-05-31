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
from dataclasses import dataclass
from typing import NamedTuple


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
        return f"{prefix}/resource/{self.entity_type}/{self.entity_id}?version={self.entity_version}"


class ProductClassDef(NamedTuple):
    """A product class definition."""

    id: str | None
    name: str | None


@dataclass(kw_only=True)
class Category:
    """A category DTO."""

    id: str
    name: str | None = None
    parent_id: str | None = None
    full_path: list[str] | None = None
