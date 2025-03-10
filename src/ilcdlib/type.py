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
from typing import Sequence

LangDef = str | Sequence[str | None] | None


class LocalizedStr(str):
    """A string with language code attached."""

    def __new__(cls, *args, **kwargs):  # noqa: D102
        return super().__new__(cls, args[0])

    def __init__(self, s: str, lang: str | None = None):
        super().__init__()
        self.lang: str | None = lang
