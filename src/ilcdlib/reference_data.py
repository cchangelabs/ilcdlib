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
__all__ = ("get_ilcd_epd_reference_data_provider",)

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ilcdlib.medium.archive import ZipIlcdReader

_CACHE: dict[str, "ZipIlcdReader"] = {}


def get_ilcd_epd_reference_data_provider() -> "ZipIlcdReader":
    """Get the ILCD+EPD reference data from the ILCD format."""
    cache_key = "ilcd_epd_ref"
    if cache_key not in _CACHE:
        from ilcdlib.medium.archive import ZipIlcdReader

        _CACHE[cache_key] = ZipIlcdReader(Path(__file__).parent / "data" / "ilcd_epd_ref.zip")
    return _CACHE[cache_key]
