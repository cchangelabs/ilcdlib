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
#  This software was developed with support from the Skanska USA,
#  Charles Pankow Foundation, Microsoft Sustainability Fund, Interface, MKA Foundation, and others.
#  Find out more at www.BuildingTransparency.org
#
from pathlib import Path
from unittest import TestCase

from ilcdlib.entity.contact import IlcdContactReader
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.medium.archive import ZipIlcdReader


class ContactReaderTestCase(TestCase):
    TEST_DATA_BASE = Path(__file__).parent.parent.parent / "test_data"
    LANG = "en"

    epd_reader: IlcdEpdReader
    contact_reader: IlcdContactReader

    def setUp(self):
        self.epd_reader = IlcdEpdReader(
            "2eb43850-0ab2-4068-afe5-218d69a096f8",
            "00.01.000",
            ZipIlcdReader(self.TEST_DATA_BASE / "ibu_with_dependencies.zip"),
        )
        self.contact_reader = IlcdContactReader(
            self.epd_reader._get_external_tree(
                self.epd_reader.epd_el_tree,
                (
                    "process:modellingAndValidation",
                    "process:validation",
                    "process:review",
                    "common:referenceToNameOfReviewerAndInstitution",
                ),
            ),
            self.epd_reader.data_provider,
        )

    def tearDown(self) -> None:
        self.epd_reader.data_provider.close()

    def test_read_contact_fields(self):
        self.assertEqual(self.contact_reader.get_uuid(), "d111dbec-b024-4be5-86c5-752d6eb2cf95")
        self.assertEqual(self.contact_reader.get_phone(), "Tel.: +49 30 30 87 7")
        self.assertEqual(self.contact_reader.get_email(), "info@bau-umwelt.de")
        self.assertEqual(self.contact_reader.get_website(), "www.bau-umwelt.com")
        self.assertEqual(self.contact_reader.get_version(), "25.00.000")
        self.assertEqual(self.contact_reader.get_short_name("de"), "IBU")
        self.assertEqual(self.contact_reader.get_name("de"), "Institut Bauen und Umwelt e. V.")
        self.assertEqual(self.contact_reader.get_address(), "Panoramastr. 1, 10178 Berlin")

    def test_to_openepd(self):
        openepd_org = self.contact_reader.to_openepd_org("de")
        if openepd_org:
            print(openepd_org.model_dump_json(indent=2, warnings=False))
