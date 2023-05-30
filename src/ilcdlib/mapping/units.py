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


class UnitsUUIDMapper(SimpleDataMapper[str]):
    """A data mapper that maps units ILCD UUIDs to their symbols."""

    DATABASE = {
        "c20a03d7-bd90-4569-bc94-66cfd364dfc8": "m2",
        # Impact units
        "93a60a57-a3c8-11da-a746-0800200c9a66": "MJ",
        "6ae2df01-888e-46c8-b17d-49fa3869b476": "m3AWARE",
        "1ebf3012-d0db-4de2-aefd-ef30cedb0be1": "kgCO2e",
        "b5c629d6-def3-11e6-bf01-fe55135034f3": "kgCFC11e",
        "88054749-b0a6-47ea-a82b-dc5b29326512": "kgCFC11e",
        "b5c611c6-def3-11e6-bf01-fe55135034f3": "kgSO2e",
        "01c26c17-9a76-406e-8295-f17b55fd909e": "kgC2H4e",
        "67b5401d-873c-485f-bcf3-6ae83b918822": "kgPO4e",
        "b4274add-93b7-4905-a5e4-2e878c4e4216": "kgSO2e",
        "bc50c624-a9bc-45b1-a9b0-e6b10d00476f": "kgSO2e",
    }


default_units_uuid_mapper = UnitsUUIDMapper()
