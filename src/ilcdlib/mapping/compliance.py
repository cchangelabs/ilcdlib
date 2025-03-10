#
#  Copyright 2025 by C Change Labs Inc. www.c-change-labs.com
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
from ilcdlib.mapping.common import SimpleDataMapper


class StandardNameToLCIAMethodMapper(SimpleDataMapper[str | None]):
    """Map standard name to LCIA method."""

    DATABASE = {
        "EN 15804+A2": "EF 3.0",
        "EN 15804+A1": "EF 3.0",
    }


default_standard_names_to_lcia_mapper = StandardNameToLCIAMethodMapper()
