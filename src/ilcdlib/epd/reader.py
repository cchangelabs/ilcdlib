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
from typing import IO, Sequence, Type

from openepd.model.common import Amount, Measurement
from openepd.model.epd import Epd
from openepd.model.lcia import ImpactSet
from openepd.model.specs import Specs

from ilcdlib import const
from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader, OpenEpdEdpSupportReader
from ilcdlib.const import IlcdDatasetType
from ilcdlib.dto import IlcdReference, ProductClassDef
from ilcdlib.entity.contact import IlcdContactReader
from ilcdlib.entity.flow import IlcdExchangeDto, IlcdFlowReader
from ilcdlib.entity.lcia import IlcdLciaResultsReader
from ilcdlib.entity.material import MatMlMaterial
from ilcdlib.entity.pcr import IlcdPcrReader
from ilcdlib.type import LangDef
from ilcdlib.utils import create_ext, create_openepd_attachments, none_throws


class IlcdEpdReader(OpenEpdEdpSupportReader, IlcdXmlReader):
    """Reader for ILCD+EPD datasets."""

    def __init__(
        self,
        epd_process_id: str | None,
        epd_version: str | None,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        contact_reader_cls: Type[IlcdContactReader] = IlcdContactReader,
        pcr_reader_cls: Type[IlcdPcrReader] = IlcdPcrReader,
        flow_reader_cls: Type[IlcdFlowReader] = IlcdFlowReader,
        lcia_results_reader_cls: Type[IlcdLciaResultsReader] = IlcdLciaResultsReader,
    ):
        super().__init__(data_provider)
        self.contact_reader_cls = contact_reader_cls
        self.pcr_reader_cls = pcr_reader_cls
        self.flow_reader_cls = flow_reader_cls
        self.lcia_results_reader_cls = lcia_results_reader_cls
        if epd_process_id is None:
            entities = data_provider.list_entities(IlcdDatasetType.Processes)
            self.__epd_entity_ref = entities[0]
        else:
            self.__epd_entity_ref = IlcdReference(IlcdDatasetType.Processes, epd_process_id, epd_version)
        self.epd_el_tree = self.get_xml_tree(*self.__epd_entity_ref, allow_static_datasets=False)
        self.post_init()

    def post_init(self):
        """
        Post-initialization actions, will be executed as a last step in constructor.

        It could be overriden by subclasses to perform additional initialization actions.
        """
        pass

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

    def get_own_reference(self) -> IlcdReference | None:
        """Get the reference to this data set."""
        return IlcdReference(entity_type="processes", entity_id=self.get_uuid(), entity_version=self.get_version())

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

    def get_epd_document_stream(self) -> IO[bytes] | None:
        """Extract the EPD document."""
        return self._get_external_binary(
            self.epd_el_tree,
            (
                "process:modellingAndValidation",
                "process:dataSourcesTreatmentAndRepresentativeness",
                "common:other",
                "epd2019:referenceToOriginalEPD",
            ),
        )

    def get_product_name(self, lang: LangDef) -> str | None:
        """Return the product name in the given language."""
        return self._get_localized_text(
            self.epd_el_tree,
            ("process:processInformation", "process:dataSetInformation", "process:name", "process:baseName"),
            lang,
        )

    def get_quantitative_product_props_str(self, lang: LangDef) -> str | None:
        """Return the quantitative product properties in the given language."""
        return self._get_localized_text(
            self.epd_el_tree,
            (
                "process:processInformation",
                "process:dataSetInformation",
                "process:name",
                "process:functionalUnitFlowProperties",
            ),
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
        return self.contact_reader_cls(element, self.data_provider) if element is not None else None

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
        return self.contact_reader_cls(element, self.data_provider) if element is not None else None

    def get_pcr_reader(self) -> IlcdPcrReader | None:
        """Return the reader for the PCR."""
        element = self._get_external_tree(
            self.epd_el_tree,
            (
                "process:modellingAndValidation",
                "process:LCIMethodAndAllocation",
                "process:referenceToLCAMethodDetails",
            ),
        )
        return self.pcr_reader_cls(element, self.data_provider) if element is not None else None

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
        return self.contact_reader_cls(element, self.data_provider) if element is not None else None

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

    def get_ref_to_product_flow_dataset(self) -> int | None:
        """
        Return the reference to the flow dataset.

        This number should be used to identify flow in the list of exchanges.
        """
        return self._get_int(
            self.epd_el_tree,
            ("process:processInformation", "process:quantitativeReference", "process:referenceToReferenceFlow"),
        )

    def get_material_properties(self) -> MatMlMaterial | None:
        """Return the material properties."""
        product_flow_dto = self.get_product_flow()
        if product_flow_dto is None or product_flow_dto.flow_dataset_reader is None:
            return None
        material_reader = product_flow_dto.flow_dataset_reader.get_material_reader()
        if material_reader is None:
            return None
        return material_reader.get_material()

    def get_product_flow_properties(self, include_ref_flow_prop: bool = False) -> dict[str, Measurement]:
        """Return product flow properties other than reference property."""
        exchange_dto = self.get_product_flow()
        if exchange_dto is None:
            return {}
        reference_flow_properties = none_throws(exchange_dto.flow_dataset_reader).get_flow_other_properties(
            include_ref_flow_prop
        )
        result = {}
        for rfp in reference_flow_properties:
            unit_group_reader = rfp.dataset_reader.get_unit_group_reader()
            unit = unit_group_reader.get_reference_unit() if unit_group_reader is not None else None
            if unit is None:
                continue
            amount = (exchange_dto.mean_value or 1.0) * (rfp.mean_value or 1.0) * unit.mean_value
            prop_name = rfp.dataset_reader.get_name(["en", None])
            if prop_name is None:
                continue
            result[prop_name.lower()] = Measurement(mean=amount, unit=unit.name)
        return result

    def get_product_flow(self) -> IlcdExchangeDto | None:
        """Return the product flow (includes mean value and ilcd flow reader)."""
        ref_id = self.get_ref_to_product_flow_dataset()
        if ref_id is None:
            return None
        exchange_element = self._get_el(
            self.epd_el_tree,
            (
                "process:exchanges",
                f"process:exchange[@dataSetInternalID='{ref_id}']",
            ),
        )
        if exchange_element is None:
            return None
        flow_dataset_el = self._get_external_tree(exchange_element, ("process:referenceToFlowDataSet",))
        if flow_dataset_el is None:
            return None
        exchange_dto = IlcdExchangeDto(
            mean_value=self._get_float(exchange_element, ("process:meanAmount",)),
            flow_dataset_reader=self.flow_reader_cls(flow_dataset_el, self.data_provider),
        )
        return exchange_dto

    def get_declared_unit(self) -> Amount | None:
        """Return the reader for the flow."""
        exchange_dto = self.get_product_flow()
        if exchange_dto is None:
            return None
        reference_flow_property = none_throws(exchange_dto.flow_dataset_reader).get_reference_flow_property()
        if reference_flow_property is None:
            return None
        unit_group_reader = reference_flow_property.dataset_reader.get_unit_group_reader()
        unit = unit_group_reader.get_reference_unit() if unit_group_reader is not None else None
        if unit is None:
            return None
        amount = (exchange_dto.mean_value or 1.0) * (reference_flow_property.mean_value or 1.0) * unit.mean_value
        return Amount(qty=amount, unit=unit.name)

    def get_program_operator_id(self) -> str | None:
        """Get document identifier assigned by program operator."""
        return self._get_text(
            self.epd_el_tree,
            ("process:administrativeInformation", "process:publicationAndOwnership", "common:registrationNumber"),
        )

    def get_lcia_results_reader(self) -> IlcdLciaResultsReader | None:
        """Return the LCIA results reader."""
        element = self._get_el(
            self.epd_el_tree,
            ("process:LCIAResults",),
        )
        return self.lcia_results_reader_cls(element, self.data_provider) if element is not None else None

    def get_lcia_results(self) -> ImpactSet | None:
        """Return the LCIA results."""
        reader = self.get_lcia_results_reader()
        if reader is None:
            return None
        return reader.get_impacts()

    def _product_classes_to_openepd(self, classes: dict[str, list[ProductClassDef]]) -> dict[str, str]:
        result: dict[str, str] = {}
        for classification_name, class_defs in classes.items():
            if classification_name.lower() == "oekobau.dat":
                result["oekobau.dat"] = none_throws(class_defs[-1].id)
            elif classification_name.lower() == "ibucategories":
                result["IBU"] = " >> ".join([none_throws(x.name) for x in class_defs])
            if len(class_defs) > 0:
                result[const.ILCD_IDENTIFICATION[0]] = (
                    (class_defs[-1].id or "") + " " + " / ".join([none_throws(x.name) for x in class_defs])
                ).strip()
        return result

    def to_openepd_epd(self, lang: LangDef, base_url: str | None = None) -> Epd:  # NOSONAR
        """Return the EPD as OpenEPD object."""
        lang_code = lang if isinstance(lang, str) else None
        if isinstance(lang, Sequence):
            lang_code = lang[0] if len(lang) > 0 else None
        manufacturer_reader = self.get_manufacturer_reader()
        manufacturer = manufacturer_reader.to_openepd_org(lang, base_url) if manufacturer_reader else None
        program_operator_reader = self.get_program_operator_reader()
        program_operator = program_operator_reader.to_openepd_org(lang, base_url) if program_operator_reader else None
        external_verifier_reader = self.get_external_verifier_reader()
        external_verifier = (
            external_verifier_reader.to_openepd_org(lang, base_url) if external_verifier_reader else None
        )
        pcr_reader = self.get_pcr_reader()
        pcr = pcr_reader.to_openepd_pcr(lang, base_url) if pcr_reader else None
        declared_unit = self.get_declared_unit()
        quantitative_props = self.get_quantitative_product_props_str(lang)
        own_ref = self.get_own_reference()
        product_name = self.get_product_name(lang)
        if product_name and quantitative_props:
            product_name += "; " + quantitative_props
        material_properties = self.get_material_properties()
        other_product_props = self.get_product_flow_properties()
        product_properties = {}
        if material_properties:
            product_properties.update({n: v.to_unit_string() for n, v in material_properties.properties.items()})
        if other_product_props:
            product_properties.update(
                {n: (str(v.mean) + " " + v.unit if v.unit else "").strip() for n, v in other_product_props.items()}
            )
        if product_properties:
            specs = Specs(ext=create_ext(product_properties))
        else:
            specs = Specs()
        return Epd.construct(
            doctype="openEPD",
            language=lang_code,
            attachments=create_openepd_attachments(own_ref, base_url),
            declaration_url=own_ref.to_url(base_url) if own_ref and base_url else None,
            name=product_name,
            description=self.get_product_description(lang),
            date_published=self.get_date_published(),
            valid_until=self.get_validity_ends_date(),
            program_operator_doc_id=self.get_program_operator_id(),
            manufacturer=manufacturer,
            program_operator=program_operator,
            product_class=self._product_classes_to_openepd(self.get_product_classes()),
            third_party_verifier=external_verifier,
            pcr=pcr,
            declared_unit=declared_unit,
            impacts=self.get_lcia_results(),
            specs=specs,
        )

    @classmethod
    def is_known_url(cls, url: str) -> bool:
        """
        Return whether the URL recognized by this particular reader.

        This method should be overriden by the dialect and return true if the input URL is know url for this dialect.
        """

        return False
