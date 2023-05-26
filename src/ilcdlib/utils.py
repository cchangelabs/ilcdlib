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
from typing import TypeVar

from openepd.model.common import ExternalIdentification

from ilcdlib import const
from ilcdlib.dto import IlcdReference

T = TypeVar("T")


def none_throws(optional: T | None, message: str = "Unexpected `None`") -> T:
    """Convert an optional to its value. Raises an `AssertionError` if the value is `None`."""
    if optional is None:
        raise AssertionError(message)
    return optional


def create_openepd_identification(
    identification: ExternalIdentification | None,
) -> dict[str, ExternalIdentification] | None:
    """Create a dictionary of OpenEPD identification objects."""
    if identification is None or not identification.has_values():
        return None
    return {x: identification for x in const.ILCD_IDENTIFICATION}


def create_openepd_attachments(reference: IlcdReference | None, base_url: str | None = None) -> dict[str, str] | None:
    """Create a dictionary of OpenEPD attachments."""
    if reference is None:
        return None
    return {x: reference.to_url(base_url) for x in const.ILCD_IDENTIFICATION}
