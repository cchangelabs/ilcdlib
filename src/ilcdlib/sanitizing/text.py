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
def trim_text(in_str: str | None, max_length: int, ellipsis="...") -> str | None:
    """Trim a string to a maximum length."""
    if in_str is None:
        return None
    if len(in_str) <= max_length:
        return in_str
    return in_str[: max_length - len(ellipsis)] + ellipsis
