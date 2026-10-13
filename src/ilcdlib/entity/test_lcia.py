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
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from annotated_types import MaxLen
from openepd.model.lcia import EolScenario

from ilcdlib.entity.base_scope_set_reader import _truncate_scenario_name
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.medium.archive import ZipIlcdReader


class ScenarioNameTestCase(TestCase):
    def test_truncation_uses_field_constraint(self):
        with patch.object(EolScenario.model_fields["name"], "metadata", [MaxLen(12)]):
            self.assertEqual(_truncate_scenario_name("Recycling"), "Recycling")
            self.assertEqual(_truncate_scenario_name("a" * 12), "a" * 12)
            self.assertEqual(_truncate_scenario_name("a" * 13), "a" * 9 + "...")
            self.assertEqual(_truncate_scenario_name("Recycle  asphalt"), "Recycle  ...")

    def test_no_length_constraint(self):
        with patch.object(EolScenario.model_fields["name"], "metadata", []):
            name = "a" * 100
            self.assertEqual(_truncate_scenario_name(name), name)


class LciaTestCase(TestCase):
    TEST_DATA_BASE = Path(__file__).parent.parent.parent / "test_data"
    LANG = "en"

    epd_reader: IlcdEpdReader

    def setUp(self):
        self.epd_reader = IlcdEpdReader(
            "a6ef2d29-49bd-4aaf-ac19-1e3975e4fa51",
            "00.01.000",
            ZipIlcdReader(self.TEST_DATA_BASE / "epditaly_without_a1a2a3.zip"),
        )

    def tearDown(self) -> None:
        self.epd_reader.data_provider.close()

    def test_missing_a1a2a3_impact(self):
        """If A1A2A3 values is missing, it should be calculated as sum of a1,a2,a3."""

        impacts = self.epd_reader.to_openepd_declaration(self.LANG).impacts.as_dict()
        impacts_value = list(impacts.values())[0].to_serializable()

        ext = impacts_value.pop("ext")
        for v in ext.values():
            if v.get("A1") and v.get("A2") and v.get("A1"):
                self.assertIsNotNone(v.get("A1A2A3"))

        for v in impacts_value.values():
            if v and v.get("A1") and v.get("A2") and v.get("A1"):
                self.assertIsNotNone(v.get("A1A2A3"))
