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

from ilcdlib.mapping.common import BaseDataMapper, RegexMapper, SimpleDataMapper
from ilcdlib.utils import is_valid_uuid


class UnitsUUIDMapper(SimpleDataMapper[str]):
    """A data mapper that maps units ILCD UUIDs to their symbols."""

    DATABASE = {
        "c20a03d7-bd90-4569-bc94-66cfd364dfc8": "m2",
        "42e089ac-92bf-4bf2-8ca1-5fc40d18f2ed": "molHe",
        "71b4d617-0ec9-4d3f-b65e-e438940c2401": "molNe",
        # Impact units
        "93a60a57-a3c8-11da-a746-0800200c9a66": "MJ",
        "6ae2df01-888e-46c8-b17d-49fa3869b476": "m3AWARE",
        "1ebf3012-d0db-4de2-aefd-ef30cedb0be1": "kgCO2e",
        "b5c629d6-def3-11e6-bf01-fe55135034f3": "kgCFC11e",
        "d9e957c9-7309-4474-bf3a-7777df6c4e5b": "kgCFC11e",
        "88054749-b0a6-47ea-a82b-dc5b29326512": "kgCFC11e",
        "b5c611c6-def3-11e6-bf01-fe55135034f3": "kgSO2e",
        "01c26c17-9a76-406e-8295-f17b55fd909e": "kgC2H4e",
        "67b5401d-873c-485f-bcf3-6ae83b918822": "kgPO4e",
        "b4274add-93b7-4905-a5e4-2e878c4e4216": "kgSO2e",
        "bc50c624-a9bc-45b1-a9b0-e6b10d00476f": "kgSO2e",
        "d05bb823-ecdf-4686-8c40-bf1d9257859f": "kgNe",
        "0429039d-a61d-4590-ba67-aa4a20a810a1": "kgPe",
        "d27c25f8-fbc1-44c6-b47b-4adbae4199c6": "kgNMVOCe",
        "54ccd2d9-a32a-4fc2-923d-f2c8c93e89d4": "kgSbe",
    }


class UnitsRegexMapper(RegexMapper[str]):
    """A data mapper that maps units to their symbols using regex."""

    _COMMON_PART = r"(?:[\W-]*\s*)?"
    _OPTIONAL_PART: str = r"(?:(-?[AÄ\u00c4]+[qo]+v?)|(?i:e?q?(uiv)?(alent)?(s)?))?"

    def __init__(self) -> None:
        self.PATTERNS = {k: self._construct_pattern(k) for k, v in self.PATTERNS.items()}
        super().__init__()

    @classmethod
    def _construct_pattern(cls, pattern_name: str) -> str:
        return rf"{cls.PATTERNS[pattern_name]}{cls._COMMON_PART}{cls._OPTIONAL_PART}\s*\.?\b"

    PATTERNS = {
        "kgCO2e": r"kg-?\s*CO[2₂]?",
        "tCO2e": r"t-?\s*CO[2₂]?",
        "lbCO2e": r"lb-?\s*CO[2₂]?",
        "gCO2e": r"g-?\s*CO[2₂]?",
        "kgR11e": r"kg-?\s*R-?\s*11",
        "tR11e": r"t-?\s*R-?\s*11",
        "lbR11e": r"lb-?\s*R-?\s*11",
        "gR11e": r"g-?\s*R-?\s*11",
        "kgSO2e": r"kg-?\s*SO[2₂]?",
        "tSO2e": r"t-?\s*SO[2₂]?",
        "lbSO2e": r"lb-?\s*SO[2₂]?",
        "gSO2e": r"g-?\s*SO[2₂]?",
        "kgCFC11e": r"kg-?\s*CFC-?\s*11",
        "tCFC11e": r"t-?\s*CFC-?\s*11",
        "lbCFC11e": r"lb-?\s*CFC-?v11",
        "gCFC11e": r"g-?\s*CFC-?\s*11",
        "kgPe": r"kg-?\s*P",
        "kgNe": r"kg-?\s*N",
        "tNe": r"t-?\s*N",
        "lbNe": r"lb-?\s*N",
        "gNe": r"g-?\s*N",
        "molNe": r"mol-?\s*N",
        "molHe": r"mol-?\s*H\+?",
        "kgPO4e": r"kg-?\s*\(?PO(4|₄)?\)?[³3]?",
        "tPO4e": r"t-?\s*\(?PO(4|₄)?\)?[³3]?",
        "lbPO4e": r"lb-?\s*\(?PO(4|₄)?\)?[³3]?",
        "gPO4e": r"g-?\s*\(?PO(4|₄)?\)?[³3]?",
        "kgO3e": r"kg-?\s*O[3₃]?",
        "tO3e": r"t-?\s*O[3₃]?",
        "lbO3e": r"lb-?\s*O[3₃]?",
        "gO3e": r"g-?\s*O[3₃]?",
        "kgCH4e": r"kg-?\s*CH(4)?[₄]?",
        "tCH4e": r"t-?\s*CH(4)?[₄]?",
        "lbCH4e": r"lb-?\s*CH(4)?[₄]?",
        "gCH4e": r"g-?\s*CH(4)?[₄]?",
        "kgC2H4e": r"kg-?\s*C(2)?H(4)?[₄]?",
        "tC2H4e": r"t-?\s*C(2)?H(4)?[₄]?",
        "lbC2H4e": r"lb-?\s*C(2)?H(4)?[₄]?",
        "gC2H4e": r"g-?\s*C(2)?H(4)?[₄]?",
        "kgC2H2e": r"kg-?\s*C(2)?H(4)?[₂]?",
        "tC2H2e": r"t-?\s*C(2)?H(2)?[₂]?",
        "lbC2H2e": r"lb-?\s*C(2)?H(2)?[₂]?",
        "gC2H2e": r"g-?\s*C(2)?H(2)?[₂]?",
        "kgNMVOCe": r"kg-?\s*NMVOC",
        "tNMVOCe": r"t-?\s*NMVOC",
        "lbNMVOCe": r"lb-?\s*NMVOC",
        "gNMVOCe": r"g-?\s*NMVOC",
        "kgSbe": r"kg-?\s*Sb",
        "tSbe": r"t-?\s*Sb",
        "lbSbe": r"lb-?\s*Sb",
        "gSbe": r"g-?\s*Sb",
    }


class ScopeToUnitsMapper(SimpleDataMapper[str]):
    """A data mapper that maps scope names to their default units."""

    DATABASE = {
        "gwp": "kgCO2e",
        "gwp-fossil": "kgCO2e",
        "gwp-biogenic": "kgCO2e",
        "gwp-luluc": "kgCO2e",
        "odp": "kgCFC11e",
        "pocp": "kgC2H4e",
        "ap": "kgSO2e",
        "ep-fresh": "kgPO4e",
        "ep-marine": "kgNe",
        "ep-terr": "molNe",
        "cru": "kg",
        "ee": "MJ",
        "hwd": "kg",
        "mer": "kg",
        "mfr": "kg",
        "fw": "m3",
        "nhwd": "kg",
        "penre": "MJ",
        "penrm": "MJ",
        "nrsf": "MJ",
        "rwd": "kg",
        "peret": "MJ",
        "perm": "MJ",
        "rsf": "MJ",
        "sm": "kg",
        "penrt": "MJ",
        "pert": "MJ",
    }


class DefaultUnitsMapper(BaseDataMapper[str, str]):
    """Map default scope units to their symbols."""

    def __init__(self) -> None:
        self._uuid_mapper = UnitsUUIDMapper()
        self._regex_mapper = UnitsRegexMapper()

    def map(self, input_value: str, default_value: str | None) -> str | None:
        """Map the input value to the output value."""
        unit: str | None = None
        if is_valid_uuid(input_value):
            unit = self._uuid_mapper.map(input_value, None)
        if unit is None and default_value:
            unit = self._regex_mapper.map(default_value, None)
        return unit or default_value


default_scope_to_units_mapper = ScopeToUnitsMapper()
default_units_mapper = DefaultUnitsMapper()
