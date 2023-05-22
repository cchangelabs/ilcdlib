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
import datetime
from pathlib import Path
from unittest import TestCase

from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.medium.archive import ZipIlcdReader


class EpdReaderTestCase(TestCase):
    TEST_DATA_BASE = Path(__file__).parent.parent.parent / "test_data"
    LANG = "en"

    epd_reader_industry: IlcdEpdReader

    def setUp(self):
        self.epd_reader_industry = IlcdEpdReader(
            "2eb43850-0ab2-4068-afe5-218d69a096f8",
            "00.01.000",
            ZipIlcdReader(self.TEST_DATA_BASE / "ibu_with_dependencies.zip"),
        )

    def tearDown(self) -> None:
        self.epd_reader_industry.data_provider.close()

    def test_read_basic_fields_industry_epd(self):
        self.assertEqual(self.epd_reader_industry.get_product_name(self.LANG), "2-layer parquet")
        self.assertIsNotNone(self.epd_reader_industry.get_product_description(self.LANG))
        self.assertTrue(self.epd_reader_industry.is_epd())
        self.assertTrue(self.epd_reader_industry.is_industry_epd())

        classes = self.epd_reader_industry.get_product_classes()
        self.assertEqual(classes.get("OEKOBAU.DAT")[-1].id, "3.3.02")
        self.assertEqual(classes.get("OEKOBAU.DAT")[-1].name, "Parkett")
        self.assertEqual(
            [x.name for x in classes.get("IBUCategories")],
            ["02 Bauprodukte", "Produkte aus Bauholz", "Vollholzprodukte"],
        )
        self.assertEqual(self.epd_reader_industry.get_program_operator_id(), "EPD-HAM-20220202-ICD1-DE")
        self.assertEqual(self.epd_reader_industry.get_date_published(), datetime.date.fromisoformat("2022-10-10"))

    def test_to_openepd(self):
        openepd_org = self.epd_reader_industry.to_openepd_epd("de")
        if openepd_org:
            print(openepd_org.json(indent=2))
