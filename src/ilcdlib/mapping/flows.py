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


class FlowsUUIDToOpenIdMapper(SimpleDataMapper[str]):
    """Map ILCD UUIDs to openEPD flow names."""

    DATABASE = {
        "a2b32f97-3fc7-4af2-b209-525bc6426f33": "cru",
        "4da0c987-2b76-40d6-9e9e-82a017aaaf29": "ee",
        "98daf38a-7a79-46d3-9a37-2b7bd0955810": "eh",
        "430f9e0f-59b2-46a0-8e0d-55e0e84948fc": "hwd",
        "59a9181c-3aaf-46ee-8b13-2b3723b6e447": "mer",
        "d7fe48a5-4103-49c8-9aae-b0b5dfdbd6ae": "mfr",
        "b29ef66b-e286-4afa-949f-62f1a7b4d7fa": "nhwd",
        "3449546e-52ad-4b39-b809-9fb77cea8ff6": "rwd",
    }


default_flows_uuid_mapper = FlowsUUIDToOpenIdMapper()
