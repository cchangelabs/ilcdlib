#
#  Copyright 2026 by C Change Labs Inc. www.c-change-labs.com
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
import datetime
from unittest import TestCase
from zoneinfo import ZoneInfo

from ilcdlib.utils import date_to_datetime


class DateToDatetimeTestCase(TestCase):
    def test_none_date(self) -> None:
        self.assertIsNone(date_to_datetime(None))

    def test_uses_utc_by_default(self) -> None:
        actual = date_to_datetime(datetime.date(2024, 2, 29))

        self.assertEqual(
            datetime.datetime(2024, 2, 29, tzinfo=datetime.UTC),
            actual,
        )

    def test_uses_requested_timezone(self) -> None:
        actual = date_to_datetime(datetime.date(2024, 2, 29), "Europe/Berlin")

        self.assertEqual(
            datetime.datetime(2024, 2, 29, tzinfo=ZoneInfo("Europe/Berlin")),
            actual,
        )
