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
from abc import abstractmethod
import datetime
from pathlib import Path
from unittest import TestCase

from ilcdlib.epd.dialect.epditaly import EpdItalyIlcdXmlEpdReader
from ilcdlib.epd.dialect.oekobaudat import OekobauDatIlcdXmlEpdReader
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.medium.archive import ZipIlcdReader


class BaseEpdReaderTestCase(TestCase):
    __test__ = False

    TEST_DATA_BASE = Path(__file__).parent.parent.parent / "test_data"
    LANG = "en"

    epd_reader: IlcdEpdReader

    @abstractmethod
    def setUp(self):
        pass

    def tearDown(self) -> None:
        self.epd_reader.data_provider.close()


class EpdReaderTestCase(BaseEpdReaderTestCase):
    __test__ = True

    def setUp(self):
        self.epd_reader = IlcdEpdReader(
            "2eb43850-0ab2-4068-afe5-218d69a096f8",
            "00.01.000",
            ZipIlcdReader(self.TEST_DATA_BASE / "ibu_with_dependencies.zip"),
        )
        self.epd_reader.xml_parser.xml_ns["epd2019"] = "http://www.indata.network/EPD/2019"

    def test_read_basic_fields_industry_epd(self):
        self.assertEqual(self.epd_reader.get_product_name(self.LANG), "2-layer parquet")
        self.assertIsNotNone(self.epd_reader.get_product_description(self.LANG))
        self.assertTrue(self.epd_reader.is_epd())
        self.assertTrue(self.epd_reader.is_industry_epd())

        classes = self.epd_reader.get_product_classes()
        self.assertEqual(classes.get("OEKOBAU.DAT")[-1].id, "3.3.02")
        self.assertEqual(classes.get("OEKOBAU.DAT")[-1].name, "Parkett")
        self.assertEqual(
            [x.name for x in classes.get("IBUCategories")],
            ["02 Bauprodukte", "Produkte aus Bauholz", "Vollholzprodukte"],
        )
        self.assertEqual(self.epd_reader.get_program_operator_id(), "EPD-HAM-20220202-ICD1-DE")
        self.assertEqual(self.epd_reader.get_date_published(), datetime.date.fromisoformat("2022-10-10"))

    def test_read_basic_fields_scenario_epd(self):
        self.assertEqual(self.epd_reader.get_scenario_names(self.LANG), {"S1": "100% recycling", "S2": "Scenario 2"})

    def test_to_openepd(self):
        openepd_org = self.epd_reader.to_openepd_epd("de")
        if openepd_org:
            print(openepd_org.json(indent=2))


class OekobaudatTestCase(BaseEpdReaderTestCase):
    __test__ = True

    def setUp(self):
        self.epd_reader = OekobauDatIlcdXmlEpdReader(
            "2eb43850-0ab2-4068-afe5-218d69a096f8",
            "00.01.000",
            ZipIlcdReader(self.TEST_DATA_BASE / "ibu_with_dependencies.zip"),
        )

    def test_read_oekobaudat_fields_scenario(self):
        self.assertEqual(self.epd_reader.get_scenario_names(self.LANG), {"S1": "100% recycling", "S2": "Scenario 2"})


class EpdItalyTestCase(BaseEpdReaderTestCase):
    __test__ = True

    def setUp(self):
        self.epd_reader = EpdItalyIlcdXmlEpdReader(
            "8bc0d502-7f9b-43ab-af31-d55d23a708f1",
            "00.01.000",
            ZipIlcdReader(self.TEST_DATA_BASE / "epditaly_with_dependencies.zip"),
        )

    def test_read_epditaly_fields_scenario(self):
        self.assertEqual(
            self.epd_reader.get_scenario_names(self.LANG),
            {"100% riciclo": "100% riciclo", "100% incenerimento": "100% incenerimento"},
        )
