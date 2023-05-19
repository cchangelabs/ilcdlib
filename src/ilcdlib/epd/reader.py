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
from typing import Type

from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader
from ilcdlib.const import IlcdDatasetType
from ilcdlib.dto import IlcdReference
from ilcdlib.entity.contact import IlcdContactReader


class IlcdEpdReader(IlcdXmlReader):
    """Reader for ILCD+EPD datasets."""

    def __init__(
        self,
        epd_process_id: str,
        epd_version: str,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        contact_reader_cls: Type[IlcdContactReader] = IlcdContactReader,
    ):
        super().__init__(data_provider)
        self.contact_reader_cls = contact_reader_cls
        self.__epd_entity_ref = IlcdReference(IlcdDatasetType.Processes, epd_process_id, epd_version)
        self.epd_el_tree = self.get_xml_tree(*self.__epd_entity_ref, allow_static_datasets=False)
        self.xml_parser.xml_ns["epd2013"] = "http://www.iai.kit.edu/EPD/2013"
        self.xml_parser.xml_ns["epd2019"] = "http://www.iai.kit.edu/EPD/2019"

    def is_epd(self) -> bool:
        """Return True if the dataset represents an EPD."""
        return (
            self._get_text(
                self.epd_el_tree,
                ("process:modellingAndValidation", "process:LCIMethodAndAllocation", "process:typeOfDataSet"),
            )
            == "EPD"
        )

    def is_industry_epd(self):
        """Return True if the dataset represents an industry EPD."""
        return (
            self._get_text(
                self.epd_el_tree,
                ("process:modellingAndValidation", "process:LCIMethodAndAllocation", "common:other", "epd2013:subType"),
            )
            == "average dataset"
        )

    def get_product_name(self, lang: str) -> str | None:
        """Return the product name in the given language."""
        return self._get_localized_text(
            self.epd_el_tree,
            ("process:processInformation", "process:dataSetInformation", "process:name", "process:baseName"),
            lang,
        )

    def get_product_description(self, lang: str) -> str | None:
        """Return the product description in the given language."""
        return self._get_localized_text(
            self.epd_el_tree,
            ("process:processInformation", "process:dataSetInformation", "common:generalComment"),
            lang,
        )

    def get_date_published(self) -> datetime.date | None:
        """Return the date the EPD was published."""
        return self._get_date(
            self.epd_el_tree,
            ("process:processInformation", "process:time", "common:other", "epd2019:publicationDateOfEPD"),
        )

    def get_external_verifier_reader(self) -> IlcdContactReader | None:
        """Return the reader for the reviewer."""
        element = self._get_external_tree(
            self.epd_el_tree,
            (
                "process:modellingAndValidation",
                "process:validation",
                "process:review",
                "common:referenceToNameOfReviewerAndInstitution",
            ),
        )
        if element:
            return self.contact_reader_cls(
                element,
                self.data_provider,
            )
        else:
            return None
