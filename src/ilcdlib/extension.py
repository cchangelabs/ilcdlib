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
from openepd.model.base import OpenEpdExtension
from openepd.model.org import Org
import pydantic as pyd

from ilcdlib import const


class IlcdEpdExtension(OpenEpdExtension):
    """An ILCD extension for OpenEPD Epd object."""

    dataset_type: str | None = None
    dataset_version: str | None = None
    dataset_uuid: str | None = None
    production_location: str | None = None
    ilcd_pdf_url: pyd.AnyUrl | None = None

    @classmethod
    def get_extension_name(cls) -> str:
        """Return the name of the extension to be used as a key in ext dict."""
        return const.ILCD_IDENTIFICATION[0]


class Ec3EpdExtension(OpenEpdExtension):
    """An EC3 extension for OpenEPD Epd object."""

    epd_publisher: Org | None = None
    epd_developer: Org | None = None

    @classmethod
    def get_extension_name(cls) -> str:
        """Return the name of the extension to be used as a key in ext dict."""
        return "ec3"
