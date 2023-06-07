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


class IndicatorsUUIDToOpenIdMapper(SimpleDataMapper[str]):
    """Map ILCD UUIDs to openEPD indicator names."""

    DATABASE = {
        "3cf952c8-f3a4-461d-8c96-96456ca62246": "fw",
        "ac857178-2b45-46ec-892a-a9a4332f0372": "penre",
        "1421caa0-679d-4bf4-b282-0eb850ccae27": "penrm",
        "89def144-d39a-4287-b86f-efde453ddcb2": "nrsf",
        "20f32be5-0398-4288-9b6d-accddd195317": "pere",
        "fb3ec0de-548d-4508-aea5-00b73bf6f702": "perm",
        "64333088-a55f-4aa2-9a31-c10b07816787": "rsf",
        "c6a1f35f-2d09-4f54-8dfb-97e502e1ce92": "sm",
        "06159210-646b-4c8d-8583-da9b3b95a6c1": "penrt",
        "53f97275-fa8a-4cdd-9024-65936002acd0": "pert",
    }


default_indicators_uuid_mapper = IndicatorsUUIDToOpenIdMapper()
