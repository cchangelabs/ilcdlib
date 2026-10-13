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
from io import BytesIO
from pathlib import Path
from unittest import TestCase
from zipfile import ZipFile

from ilcdlib.medium.archive import ZipIlcdReader


class ZipMediumTestCase(TestCase):
    TEST_DATA_BASE = Path(__file__).parent.parent.parent / "test_data"

    def test_open_existing_file(self):
        ZipIlcdReader(self.TEST_DATA_BASE / "environdec_with_dependencies.zip")

    def test_open_non_existing_file(self):
        with self.assertRaises(ValueError):
            ZipIlcdReader(self.TEST_DATA_BASE / "non_existing.zip")

    def test_open_non_zip_file(self):
        with self.assertRaises(ValueError):
            ZipIlcdReader(self.TEST_DATA_BASE / "environdec_single_xml.xml")

    def test_open_existing_by_stream(self):
        with open(self.TEST_DATA_BASE / "environdec_with_dependencies.zip", "rb") as f:
            ZipIlcdReader(f)

    def test_check_existing_entity(self):
        reader = ZipIlcdReader(self.TEST_DATA_BASE / "environdec_with_dependencies.zip")
        self.assertTrue(reader.entity_exists("contacts", "9e4aaaf4-2af3-4c77-ac32-cb2ade909608", "00.00.001"))
        self.assertFalse(reader.entity_exists("contacts", "aaaaaaaa-2af3-4c77-ac32-cb2ade909608", "00.00.001"))

    def test_read_existing_entity(self):
        reader = ZipIlcdReader(self.TEST_DATA_BASE / "environdec_with_dependencies.zip")
        with reader.get_entity_stream("contacts", "9e4aaaf4-2af3-4c77-ac32-cb2ade909608", "00.00.001") as f:
            self.assertEqual(len(f.read()), 1442)

    def test_read_binary_entity(self):
        reader = ZipIlcdReader(self.TEST_DATA_BASE / "environdec_with_dependencies.zip")
        with reader.get_entity_stream("external_docs", "EPD_logotype_stor_rgb.jpg", binary=True) as f:
            self.assertEqual(len(f.read()), 28859)

    def test_list_entities_with_and_without_versions(self):
        archive = BytesIO()
        with ZipFile(archive, "w") as zip_file:
            zip_file.writestr("ILCD/processes/12345678-1234-1234-1234-123456789012_00.00.001.xml", "")
            zip_file.writestr("ILCD/processes/12345678-1234-1234-1234-123456789013.xml", "")
            zip_file.writestr("ILCD/processes/not_an_entity.txt", "")

        archive.seek(0)
        reader = ZipIlcdReader(archive)
        self.assertEqual(
            reader.list_entities("processes"),
            [
                ("processes", "12345678-1234-1234-1234-123456789012", "00.00.001", None),
                ("processes", "12345678-1234-1234-1234-123456789013", None, None),
            ],
        )
        reader.close()
