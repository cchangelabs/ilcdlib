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


class ImpactsUUIDToOpenIdMapper(SimpleDataMapper[str]):
    """Map ILCD UUIDs to openEPD impact names."""

    DATABASE = {
        "77e416eb-a363-4258-a04e-171d843a6460": "gwp",
        "6a37f984-a4b3-458a-a20a-64418c145fa2": "gwp",
        "5f635281-343e-44fb-83df-1971b155e6b6": "gwp-fossil",
        "2356e1ab-0185-4db5-86e5-16de51c7485c": "gwp-biogenic",
        "4331bbdb-978a-490d-8707-eeb047f01a55": "gwp-luluc",
        "06dcd26f-025f-401a-a7c1-5e457eb54637": "odp",
        "1e84a202-dae6-42aa-9e9d-71ea48b8be00": "pocp",
        "b5c611c6-def3-11e6-bf01-fe55135034f3": "ap",
        "b4274add-93b7-4905-a5e4-2e878c4e4216": "ap",
        "b53ec18f-7377-4ad3-86eb-cc3f4f276b2b": "ep-fresh",
        "f58827d0-b407-4ec6-be75-8b69efb98a0f": "ep-fresh",
        "b5c619fa-def3-11e6-bf01-fe55135034f3": "ep-marine",
        "b5c614d2-def3-11e6-bf01-fe55135034f3": "ep-terr",
        "b2ad66ce-c78d-11e6-9d9d-cec0c932ce01": "WDP",
    }


default_impacts_uuid_mapper = ImpactsUUIDToOpenIdMapper()
