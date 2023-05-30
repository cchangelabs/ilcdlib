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
import re

PHONE_REGEX = re.compile(r"[+\d\s\-()]+", re.IGNORECASE)


def cleanup_phone(phone: str | None) -> str | None:
    """
    Try to perform cleanup of the given phone number.

    E.g. if the input is `Tel: +49 (0) 123 456 789 blah`, the output will be ``+49 (0) 123 456 789``.
    """
    if phone is None:
        return None
    for m in sorted(PHONE_REGEX.findall(phone), key=lambda x: len(x), reverse=True):
        if len(m.strip()) > 0:
            return m.strip()
    return phone
