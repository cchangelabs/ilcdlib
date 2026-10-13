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
from unittest import TestCase

from pydantic import BaseModel, Field

from ilcdlib.sanitizing.phone import cleanup_phone
from ilcdlib.sanitizing.text import trim_text, trim_to_model_field_max_length


class _LimitedTextModel(BaseModel):
    text: str = Field(max_length=5)


class _ShortTextModel(BaseModel):
    text: str = Field(max_length=2)


class _UnlimitedTextModel(BaseModel):
    text: str


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


class TextSanitizingTestCase(TestCase):
    def test_trim_text_preserves_none(self):
        self.assertIsNone(trim_text(None, 5))

    def test_trim_text_preserves_values_at_or_below_maximum(self):
        for value in ("", "abc", "abcde"):
            with self.subTest(value=value):
                self.assertEqual(value, trim_text(value, 5))

    def test_trim_text_trims_with_default_ellipsis(self):
        self.assertEqual("ab...", trim_text("abcdefgh", 5))

    def test_trim_text_trims_with_custom_ellipsis(self):
        self.assertEqual("abc..", trim_text("abcdefgh", 5, ellipsis=".."))

    def test_trim_text_caps_ellipsis_at_maximum_length(self):
        self.assertEqual("..", trim_text("abc", 2))

    def test_trim_to_model_field_max_length_with_custom_ellipsis(self):
        actual = trim_to_model_field_max_length(_LimitedTextModel, "text", "abcdefgh", ellipsis="..")
        self.assertEqual("abc..", actual)

    def test_trim_to_model_field_max_length_caps_ellipsis_at_maximum_length(self):
        actual = trim_to_model_field_max_length(_ShortTextModel, "text", "abc")
        self.assertEqual("..", actual)
        self.assertEqual(2, len(actual))
        _ShortTextModel(text=actual)

    def test_trim_to_model_field_max_length_with_default_ellipsis(self):
        actual = trim_to_model_field_max_length(_LimitedTextModel, "text", "abcdefgh")
        self.assertEqual("ab...", actual)

    def test_trim_to_model_field_max_length_preserves_none(self):
        actual = trim_to_model_field_max_length(_LimitedTextModel, "text", None)
        self.assertIsNone(actual)

    def test_trim_to_model_field_max_length_preserves_value_without_maximum(self):
        actual = trim_to_model_field_max_length(_UnlimitedTextModel, "text", "abcdefgh")
        self.assertEqual("abcdefgh", actual)

    def test_trim_to_model_field_max_length_preserves_none_without_maximum(self):
        actual = trim_to_model_field_max_length(_UnlimitedTextModel, "text", None)
        self.assertIsNone(actual)

    def test_trim_to_model_field_max_length_preserves_values_at_or_below_maximum(self):
        for value in ("abc", "abcde"):
            with self.subTest(value=value):
                actual = trim_to_model_field_max_length(_LimitedTextModel, "text", value)
                self.assertEqual(value, actual)
