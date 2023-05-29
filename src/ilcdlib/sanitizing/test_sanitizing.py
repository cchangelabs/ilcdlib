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
from unittest import TestCase

from ilcdlib.sanitizing.phone import cleanup_phone


class PhoneSanitizingTestCase(TestCase):
    def test_sanitizing(self):
        test_cases = [
            ("+1 263 232432", "+1 263 232432"),
            ("tel: +1 263 232432", "+1 263 232432"),
            ("Contact us at +1 263 232432", "+1 263 232432"),
            ("(+49) 521 93447681", "(+49) 521 93447681"),
            ("Tel (mobile): (+49) (521) 93447681", "(+49) (521) 93447681"),
        ]
        for input_, expected in test_cases:
            actual = cleanup_phone(input_)
            self.assertEqual(expected, actual)
