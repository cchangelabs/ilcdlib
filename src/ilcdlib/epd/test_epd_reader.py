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
from abc import abstractmethod
import datetime
from io import BytesIO
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch
from zipfile import ZipFile

from openepd.model.lcia import EolScenario, LCIAMethod

from ilcdlib.entity.flow import IlcdExchangeDto, IlcdFlowPropertyDto
from ilcdlib.epd.dialect.environdec import EnvirondecIlcdXmlEpdReader
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


class EpdValidityDateTestCase(TestCase):
    def test_validity_ends_date(self):
        cases = [
            ("2024-02-29", 2025, datetime.date(2025, 2, 28)),
            ("2024-02-29", 2028, datetime.date(2028, 2, 29)),
            ("2096-02-29", 2100, datetime.date(2100, 2, 28)),
            ("1996-02-29", 2000, datetime.date(2000, 2, 29)),
            ("2024-02-28", 2025, datetime.date(2025, 2, 28)),
            ("2024-06-19", 2025, datetime.date(2025, 6, 19)),
            (None, 2025, datetime.date(2025, 1, 1)),
            ("2024-02-29", None, None),
            (None, None, None),
        ]
        for reader_cls in (IlcdEpdReader, EnvirondecIlcdXmlEpdReader):
            for publication_date, valid_until_year, expected in cases:
                with self.subTest(
                    reader=reader_cls.__name__, publication_date=publication_date, valid_until_year=valid_until_year
                ):
                    publication_xml = (
                        f"<epd2019:publicationDateOfEPD>{publication_date}</epd2019:publicationDateOfEPD>"
                        if publication_date is not None
                        else ""
                    )
                    validity_xml = (
                        f"<common:dataSetValidUntil>{valid_until_year}</common:dataSetValidUntil>"
                        if valid_until_year is not None
                        else ""
                    )
                    xml = f"""
                        <process:processDataSet xmlns:process="http://lca.jrc.it/ILCD/Process"
                            xmlns:common="http://lca.jrc.it/ILCD/Common"
                            xmlns:epd2019="http://www.indata.network/EPD/2019">
                            <process:processInformation>
                                <process:time>
                                    {validity_xml}
                                    <common:other>{publication_xml}</common:other>
                                </process:time>
                            </process:processInformation>
                        </process:processDataSet>
                    """
                    with BytesIO() as archive:
                        with ZipFile(archive, "w") as zip_file:
                            zip_file.writestr("ILCD/processes/12345678-1234-1234-1234-123456789012.xml", xml)
                        archive.seek(0)
                        with ZipIlcdReader(archive) as medium:
                            reader = reader_cls("12345678-1234-1234-1234-123456789012", None, medium)
                            self.assertEqual(reader.get_validity_ends_date(), expected)


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
        self.assertEqual(
            self.epd_reader.get_date_published(),
            datetime.date.fromisoformat("2022-10-10"),
        )

    def test_read_basic_fields_scenario_epd(self):
        self.assertEqual(
            self.epd_reader.get_scenario_names(self.LANG),
            {"S1": "100% recycling", "S2": "Scenario 2"},
        )

    def test_to_openepd(self):
        openepd_org = self.epd_reader.to_openepd_declaration("de")
        if openepd_org:
            print(openepd_org.model_dump_json(indent=2))

    def test_zero_flow_property_values_are_preserved(self):
        unit = Mock()
        unit.mean_value = 1.0
        unit.name = "kg"
        unit_group_reader = Mock()
        unit_group_reader.get_reference_unit.return_value = unit
        property_reader = Mock()
        property_reader.get_unit_group_reader.return_value = unit_group_reader
        property_reader.get_name.return_value = "Carbon content (biogenic)"
        flow_property = IlcdFlowPropertyDto(dataset_reader=property_reader, mean_value=0.0)
        flow_reader = Mock()
        flow_reader.get_flow_other_properties.return_value = [flow_property]
        flow_reader.get_reference_flow_property.return_value = flow_property
        exchange = IlcdExchangeDto(flow_dataset_reader=flow_reader, mean_value=None)

        with patch.object(self.epd_reader, "get_product_flow", return_value=exchange):
            product_properties = self.epd_reader.get_product_flow_properties()
            declared_unit = self.epd_reader.get_declared_unit()

        self.assertEqual(product_properties["carbon content (biogenic)"].mean, 0.0)
        self.assertEqual(declared_unit.qty, 0.0)

        exchange.mean_value = 0.0
        flow_property.mean_value = 1.0
        with patch.object(self.epd_reader, "get_product_flow", return_value=exchange):
            product_properties = self.epd_reader.get_product_flow_properties()
            declared_unit = self.epd_reader.get_declared_unit()

        self.assertEqual(product_properties["carbon content (biogenic)"].mean, 0.0)
        self.assertEqual(declared_unit.qty, 0.0)


class OekobaudatTestCase(BaseEpdReaderTestCase):
    __test__ = True

    def setUp(self):
        self.epd_reader = OekobauDatIlcdXmlEpdReader(
            "2eb43850-0ab2-4068-afe5-218d69a096f8",
            "00.01.000",
            ZipIlcdReader(self.TEST_DATA_BASE / "ibu_with_dependencies.zip"),
        )

    def test_read_oekobaudat_fields_scenario(self):
        self.assertEqual(
            self.epd_reader.get_scenario_names(self.LANG),
            {"S1": "100% recycling", "S2": "Scenario 2"},
        )


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
            {
                "100% riciclo": "100% riciclo",
                "100% incenerimento": "100% incenerimento",
            },
        )


class BaseEnvirondecTestCase(BaseEpdReaderTestCase):
    EPD_UUID: str
    EPD_VERSION: str
    DATA_FILE: str

    def setUp(self):
        self.epd_reader = EnvirondecIlcdXmlEpdReader(
            self.EPD_UUID,
            self.EPD_VERSION,
            ZipIlcdReader(self.TEST_DATA_BASE / self.DATA_FILE),
        )

    def assert_epd_basics(
        self,
        epd,
        *,
        product_name: str,
        date_of_issue: datetime.date,
        valid_until: datetime.date,
        program_operator_doc_id: str,
        manufacturer: str,
        gwp_a1a2a3: float | None = None,
    ):
        self.assertEqual(epd.product_name.strip(), product_name)
        self.assertEqual(epd.date_of_issue.date(), date_of_issue)
        self.assertEqual(epd.valid_until.date(), valid_until)
        self.assertEqual(epd.program_operator_doc_id, program_operator_doc_id)
        self.assertEqual(epd.manufacturer.name, manufacturer)
        if gwp_a1a2a3 is not None:
            gwp = epd.impacts.root[LCIAMethod.UNKNOWN].gwp
            self.assertEqual(gwp.A1A2A3.mean, gwp_a1a2a3)


class EnvirondecTestCase(BaseEnvirondecTestCase):
    __test__ = True

    EPD_UUID = "2f0a9725-0aad-4cce-8c97-08dd8baae985"
    EPD_VERSION = "07.02.006"
    DATA_FILE = "2f0a9725-0aad-4cce-8c97-08dd8baae985_dependencies.zip"

    def test_to_openepd_epd(self):
        epd = self.epd_reader.to_openepd_epd(self.LANG)

        self.assert_epd_basics(
            epd,
            product_name="ABT16 100/150 AN 10 LTA asphalt from Umeå asphalt plant - Brännland",
            date_of_issue=datetime.date(2025, 6, 19),
            valid_until=datetime.date(2030, 6, 19),
            program_operator_doc_id="EPD-IES-0022654:003",
            manufacturer="NCC Industry AB",
            gwp_a1a2a3=17.9766951999211,
        )
        gwp = epd.impacts.root[LCIAMethod.UNKNOWN].gwp
        EolScenario.model_validate(gwp.C_scenarios[0].model_dump())


class EnvirondecLongNameTestCase(BaseEnvirondecTestCase):
    __test__ = True

    EPD_UUID = "fb47e4d3-95ba-4c2f-e3db-08de02c10684"
    EPD_VERSION = "07.10.003"
    DATA_FILE = "fb47e4d3-95ba-4c2f-e3db-08de02c10684_dependencies.zip"

    def test_to_openepd_epd(self):
        epd = self.epd_reader.to_openepd_epd(self.LANG)

        # The original name exceeds the OpenEPD limit of 200 chars and must be trimmed
        self.assertLessEqual(len(epd.product_name), 200)
        self.assertTrue(epd.product_name.strip().startswith("PPG Tikkurila Akvilac FD 25"))
        self.assertTrue(epd.product_name.endswith("..."))
        self.assertEqual(epd.date_of_issue.date(), datetime.date(2025, 12, 19))
        self.assertEqual(epd.valid_until.date(), datetime.date(2030, 12, 19))
        self.assertEqual(epd.program_operator_doc_id, "EPD-IES-0026131:004")
        self.assertEqual(epd.manufacturer.name, "PPG Industries")
        gwp = epd.impacts.root[LCIAMethod.UNKNOWN].gwp
        self.assertEqual(gwp.A1A2A3.mean, 1.82387952738546)
