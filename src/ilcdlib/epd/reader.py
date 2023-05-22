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
from typing import Sequence, Type

from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader, OpenEpdEdpSupportReader
from ilcdlib.const import IlcdDatasetType
from ilcdlib.dto import IlcdReference, ProductClassDef
from ilcdlib.entity.contact import IlcdContactReader
from ilcdlib.type import LangDef
from ilcdlib.utils import none_throws
from openepd.model.common import ExternalIdentification
from openepd.model.epd import Epd


class IlcdEpdReader(OpenEpdEdpSupportReader, IlcdXmlReader):
    """Reader for ILCD+EPD datasets."""

    def __init__(
        self,
        epd_process_id: str | None,
        epd_version: str | None,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        contact_reader_cls: Type[IlcdContactReader] = IlcdContactReader,
    ):
        super().__init__(data_provider)
        self.contact_reader_cls = contact_reader_cls
        if epd_process_id is None:
            entities = data_provider.list_entities(IlcdDatasetType.Processes)
            self.__epd_entity_ref = entities[0]
        else:
            self.__epd_entity_ref = IlcdReference(IlcdDatasetType.Processes, epd_process_id, epd_version)
        self.epd_el_tree = self.get_xml_tree(*self.__epd_entity_ref, allow_static_datasets=False)
        self.xml_parser.xml_ns["epd2013"] = "http://www.iai.kit.edu/EPD/2013"
        self.xml_parser.xml_ns["epd2019"] = "http://www.iai.kit.edu/EPD/2019"

    def get_supported_langs(self) -> list[str]:
        """Return the list of supported languages."""
        result: list[str] = []
        elements = self._get_all_els(
            self.epd_el_tree,
            ("process:processInformation", "process:dataSetInformation", "process:name", "process:baseName"),
        )
        for x in elements:
            if x.attrib and x.attrib.get(self._LANG_ATTRIB_NAME):
                result.append(none_throws(x.attrib.get(self._LANG_ATTRIB_NAME)))
        return result

    def get_uuid(self) -> str:
        """Get the UUID of the entity described by this data set."""
        return none_throws(
            self._get_text(
                self.epd_el_tree, ("process:processInformation", "process:dataSetInformation", "common:UUID")
            )
        )

    def get_version(self) -> str | None:
        """Get the version of the entity described by this data set."""
        return self._get_text(
            self.epd_el_tree,
            ("process:administrativeInformation", "process:publicationAndOwnership", "common:dataSetVersion"),
        )

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

    def get_product_name(self, lang: LangDef) -> str | None:
        """Return the product name in the given language."""
        return self._get_localized_text(
            self.epd_el_tree,
            ("process:processInformation", "process:dataSetInformation", "process:name", "process:baseName"),
            lang,
        )

    def get_product_description(self, lang: LangDef) -> str | None:
        """Return the product description in the given language."""
        return self._get_localized_text(
            self.epd_el_tree,
            ("process:processInformation", "process:dataSetInformation", "common:generalComment"),
            lang,
        )

    def get_date_published(self) -> datetime.date | None:
        """Return the date the EPD was published."""
        pub_date = self._get_date(
            self.epd_el_tree,
            ("process:processInformation", "process:time", "common:other", "epd2019:publicationDateOfEPD"),
        )
        if pub_date is None:
            ref_year = self._get_int(
                self.epd_el_tree,
                (
                    "process:processInformation",
                    "process:time",
                    "common:referenceYear",
                ),
            )
            if ref_year:
                return datetime.date(year=ref_year, month=1, day=1)
        return pub_date

    def get_validity_ends_date(self) -> datetime.date | None:
        """Return the date the EPD is valid until."""

        pub_date = self._get_date(
            self.epd_el_tree,
            ("process:processInformation", "process:time", "common:other", "epd2019:publicationDateOfEPD"),
        )
        valid_until_year = self._get_int(
            self.epd_el_tree,
            (
                "process:processInformation",
                "process:time",
                "common:dataSetValidUntil",
            ),
        )
        if pub_date is not None and valid_until_year is not None:
            return pub_date.replace(year=valid_until_year)
        elif valid_until_year is not None:
            return datetime.date(year=valid_until_year, month=1, day=1)
        return None

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
        if element is not None:
            return self.contact_reader_cls(
                element,
                self.data_provider,
            )
        else:
            return None

    def get_manufacturer_reader(self) -> IlcdContactReader | None:
        """Return the reader for the manufacturer."""
        element = self._get_external_tree(
            self.epd_el_tree,
            (
                "process:administrativeInformation",
                "process:publicationAndOwnership",
                "common:referenceToOwnershipOfDataSet",
            ),
        )
        if element is not None:
            return self.contact_reader_cls(
                element,
                self.data_provider,
            )
        else:
            return None

    def get_program_operator_reader(self) -> IlcdContactReader | None:
        """Return the reader for the program operator."""
        element = self._get_external_tree(
            self.epd_el_tree,
            (
                "process:administrativeInformation",
                "process:publicationAndOwnership",
                "common:referenceToRegistrationAuthority",
            ),
        )
        if element is not None:
            return self.contact_reader_cls(
                element,
                self.data_provider,
            )
        else:
            return None

    def get_product_classes(self) -> dict[str, list[ProductClassDef]]:
        """Return all product classes the product classes."""
        result: dict[str, list[ProductClassDef]] = {}
        classifications = self._get_el(
            self.epd_el_tree,
            (
                "process:processInformation",
                "process:dataSetInformation",
                "process:classificationInformation",
            ),
        )
        if classifications is None:
            return result
        for cl in classifications:
            classification_name = cl.attrib.get("name", "unknown") if cl.attrib else "unknown"
            classes = result[classification_name] = []
            for x in self._get_all_els(cl, ("common:class",)):
                cls_id = x.attrib.get("classId") if x.attrib and x.attrib.get("classId") else None
                cls_name = x.text if x.text else None
                classes.append(ProductClassDef(cls_id, cls_name))
        return result

    def get_program_operator_id(self) -> str | None:
        """Get document identifier assigned by program operator."""
        return self._get_text(
            self.epd_el_tree,
            ("process:administrativeInformation", "process:publicationAndOwnership", "common:registrationNumber"),
        )

    def _product_classes_to_openepd_org(self, classes: dict[str, list[ProductClassDef]]) -> dict[str, str]:
        result: dict[str, str] = {}
        for classification_name, class_defs in classes.items():
            if classification_name.lower() == "oekobau.dat":
                result["oekobau.dat"] = none_throws(class_defs[-1].id)
            elif classification_name.lower() == "ibucategories":
                result["IBU"] = " >> ".join([none_throws(x.name) for x in class_defs])
        return result

    def to_openepd_epd(self, lang: LangDef) -> Epd:
        """Return the EPD as OpenEPD object."""
        lang_code = lang if isinstance(lang, str) else None
        if isinstance(lang, Sequence):
            lang_code = lang[0] if len(lang) > 0 else None
        identification = ExternalIdentification.construct(
            id=self.get_uuid(),
            version=self.get_version(),
        )
        manufacturer_reader = self.get_manufacturer_reader()
        manufacturer = manufacturer_reader.to_openepd_org(lang) if manufacturer_reader else None
        program_operator_reader = self.get_program_operator_reader()
        program_operator = program_operator_reader.to_openepd_org(lang) if program_operator_reader else None
        external_verifier_reader = self.get_external_verifier_reader()
        external_verifier = external_verifier_reader.to_openepd_org(lang) if external_verifier_reader else None
        return Epd.construct(
            doctype="ILCD_EPD",
            language=lang_code,
            identified=identification,
            name=self.get_product_name(lang),
            description=self.get_product_description(lang),
            date_published=self.get_date_published(),
            valid_until=self.get_validity_ends_date(),
            program_operator_doc_id=self.get_program_operator_id(),
            manufacturer=manufacturer,
            program_operator=program_operator,
            product_class=self._product_classes_to_openepd_org(self.get_product_classes()),
            third_party_verifier=external_verifier,
        )
