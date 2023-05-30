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
from ilcdlib.mapping.common import SimpleDataMapper


class PropertiesUUIDMapper(SimpleDataMapper[str]):
    """A data mapper that maps units ILCD UUIDs to standartized names."""

    DATABASE = {
        "7e18d0ad-e78e-47a0-8e96-1c0a581902e2": "mass",
        "838aaa23-0117-11db-92e3-0800200c9a66": "length",
    }


default_properties_uuid_mapper = PropertiesUUIDMapper()
