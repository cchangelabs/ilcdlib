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
from openepd.model.lcia import Impacts, ImpactSet, OutputFlowSet, ResourceUseSet
from openepd.model.specs import Specs
from openepd.model.standard import Standard

from ilcdlib import const
from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader, OpenEpdEdpSupportReader
from ilcdlib.const import IlcdDatasetType, IlcdTypeOfReview
from ilcdlib.dto import ComplianceDto, IlcdReference, OpenEpdIlcdOrg, ProductClassDef, ValidationDto
from ilcdlib.entity.compliance import IlcdComplianceListReader
from ilcdlib.entity.contact import IlcdContactReader
from ilcdlib.entity.exchage import IlcdExchangesReader
from ilcdlib.entity.flow import IlcdExchangeDto, IlcdFlowReader
from ilcdlib.entity.lcia import IlcdLciaResultsReader
from ilcdlib.entity.material import MatMlMaterial
from ilcdlib.entity.pcr import IlcdPcrReader
from ilcdlib.entity.validation import IlcdValidationListReader
from ilcdlib.extension import IlcdEpdExtension
from ilcdlib.mapping.compliance import StandardNameToLCIAMethodMapper, default_standard_names_to_lcia_mapper
from ilcdlib.sanitizing.text import trim_text
from ilcdlib.type import LangDef
from ilcdlib.utils import (
    MarkdownSectionBuilder,
    create_ext,
    create_openepd_attachments,
    none_throws,
    provider_domain_name_from_url,
)


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
        exchanges_reader_cls: Type[IlcdExchangesReader] = IlcdExchangesReader,
        compliance_reader_cls: Type[IlcdComplianceListReader] = IlcdComplianceListReader,
        standard_names_to_lcia_mapper: StandardNameToLCIAMethodMapper = default_standard_names_to_lcia_mapper,
        validation_reader_cls: Type[IlcdValidationListReader] = IlcdValidationListReader,
    ):
        super().__init__(data_provider)
        self.contact_reader_cls = contact_reader_cls
        self.pcr_reader_cls = pcr_reader_cls
        self.flow_reader_cls = flow_reader_cls
        self.lcia_results_reader_cls = lcia_results_reader_cls
        self.compliance_reader_cls = compliance_reader_cls
        self.exchanges_reader_cls = exchanges_reader_cls
        self.standard_names_to_lcia_mapper = standard_names_to_lcia_mapper
        self.validation_reader_cls = validation_reader_cls
        if epd_process_id is None:
            entities = data_provider.list_entities(IlcdDatasetType.Processes)
            self.__epd_entity_ref = entities[0]
        else:
            self.__epd_entity_ref = IlcdReference(IlcdDatasetType.Processes, epd_process_id, epd_version)
        self.epd_el_tree = self.get_xml_tree(*self.__epd_entity_ref, allow_static_datasets=False)
        self.remap_xml_ns(self.epd_el_tree.nsmap)  # type: ignore
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

    def get_url_attachment(self, lang: LangDef) -> str | None:
        """Return URL attachment if exists."""
        return None

    def get_dataset_type(self) -> str | None:
        """Return the ILCD dataset type. e.g. 'average dataset', 'industry dataset', 'generic dataset', etc."""
        return self._get_text(
            self.epd_el_tree,
            ("process:modellingAndValidation", "process:LCIMethodAndAllocation", "common:other", "epd2013:subType"),
        )

    def is_industry_epd(self):
        """Return True if the dataset represents an industry EPD."""
        return self.get_dataset_type() == "average dataset"

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

    def get_general_comment(self, lang: LangDef) -> str | None:
        """Return the general comment in the given language."""
        return self._get_localized_text(
            self.epd_el_tree,
            ("process:processInformation", "process:dataSetInformation", "common:generalComment"),
            lang,
        )

    def get_product_description(self, lang: LangDef) -> str | None:
        """Return the product description in the given language."""
        return self.get_general_comment(lang)

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

    def get_technology_description(self, lang: LangDef) -> str | None:
        """
        Return the technology description in the given language.

        Description of the technological characteristics including operating conditions
        of the process or product system.
        """
        return self._get_localized_text(
            self.epd_el_tree,
            ("process:processInformation", "process:technology", "process:technologyDescriptionAndIncludedProcesses"),
            lang,
        )

    def get_technological_applicability(self, lang: LangDef) -> str | None:
        """
        Return the technological applicability in the given language.

        Description of the technological applicability of the process or product system.
        """
        return self._get_localized_text(
            self.epd_el_tree,
            ("process:processInformation", "process:technology", "process:technologicalApplicability"),
            lang,
        )

    def get_dataset_use_advice(self, lang: LangDef) -> str | None:
        """
        Return the dataset use advice in the given language.

        Specific methodological advice for use of the data set as application options (e.g. data set shall be used
        for LCA of buildings) or restrictions (e.g. data set shall not be used for products produced in 'wet process').
        """
        return self._get_localized_text(
            self.epd_el_tree,
            (
                "process:modellingAndValidation",
                "process:dataSourcesTreatmentAndRepresentativeness",
                "process:useAdviceForDataSet",
            ),
            lang,
        )

    def get_lca_discussion(self, lang: LangDef) -> str | None:
        """Return the product lca discussion in the given language. See openEPD/lca_discussion field docs."""
        mb = MarkdownSectionBuilder()
        mb.add_section("Use Advice", self.get_dataset_use_advice(lang))
        mb.add_section("Technology Description And Included Processes", self.get_technology_description(lang))
        mb.add_section("Location description of restrictions", self.get_location_description_of_restrictions(lang))
        return mb.build()

    def get_location_description_of_restrictions(self, lang: LangDef) -> str | None:
        """Return the location description of restrictions in the given language."""
        return self._get_localized_text(
            self.epd_el_tree,
            (
                "process:processInformation",
                "process:geography",
                "process:locationOfOperationSupplyOrProduction",
                "process:descriptionOfRestrictions",
            ),
            lang,
        )

    def get_production_location(self) -> str | None:
        """Return production regions in the given language."""
        el = self._get_el(
            self.epd_el_tree,
            ("process:processInformation", "process:geography", "process:locationOfOperationSupplyOrProduction"),
        )

        if el is None:
            return None

        return el.attrib.get("location") if el.attrib else None

    def get_validation_reader(self) -> IlcdValidationListReader | None:
        """Return the reader for the reviewer."""
        element = self._get_el(
            self.epd_el_tree,
            (
                "process:modellingAndValidation",
                "process:validation",
            ),
        )
        return self.validation_reader_cls(element, self.data_provider) if element is not None else None

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

    def get_publisher_reader(self) -> IlcdContactReader | None:
        """Return the reader for the publisher."""
        element = self._get_external_tree(
            self.epd_el_tree,
            (
                "process:administrativeInformation",
                "process:publicationAndOwnership",
                "common:other",
                "epd2019:referenceToPublisher",
            ),
        )

        if element is None:
            element = self._get_external_tree(
                self.epd_el_tree,
                (
                    "process:administrativeInformation",
                    "common:commissionerAndGoal",
                    "common:referenceToCommissioner",
                ),
            )

        return self.contact_reader_cls(element, self.data_provider) if element is not None else None

    def get_data_entry_by_reader(self) -> IlcdContactReader | None:
        """Return the reader for the data entry by."""
        element = self._get_external_tree(
            self.epd_el_tree,
            (
                "process:administrativeInformation",
                "process:dataEntryBy",
                "common:referenceToPersonOrEntityEnteringTheData",
            ),
        )
        return self.contact_reader_cls(element, self.data_provider) if element is not None else None

    def get_data_entry_by(self, lang: LangDef, base_url: str | None = None) -> OpenEpdIlcdOrg | None:
        """Return the data entry by org."""
        data_entry_by_reader = self.get_data_entry_by_reader()
        return data_entry_by_reader.to_openepd_org(lang, base_url) if data_entry_by_reader else None

    def get_compliance_reader(self) -> IlcdComplianceListReader | None:
        """Return the reader for the standard included in compliance declarations."""
        element = self._get_el(
            self.epd_el_tree,
            (
                "process:modellingAndValidation",
                "process:complianceDeclarations",
            ),
        )
        return self.compliance_reader_cls(element, self.data_provider) if element is not None else None

    def get_compliance_declarations(self, lang: LangDef, base_url: str | None = None) -> list[ComplianceDto]:
        """Return list of compliance data."""
        reader = self.get_compliance_reader()
        if reader is None:
            return []
        return reader.get_compliances(lang, base_url)

    def get_openepd_compliance(self, lang: LangDef, base_url: str | None = None) -> list[Standard]:
        """Return list of OpenEPD Standards."""
        result = []
        for compliance in self.get_compliance_declarations(lang, base_url):
            result.append(
                Standard(
                    short_name=none_throws(compliance.short_name),
                    name=compliance.name,
                    link=compliance.link,  # type: ignore
                    issuer=compliance.issuer,
                )
            )
        return result

    def get_ilcd_validations(
        self, lang: LangDef, base_url: str | None = None, provider_domain: str | None = None
    ) -> list[ValidationDto]:
        """Return list of all verifiers."""
        reader = self.get_validation_reader()
        if reader is None:
            return []
        return reader.get_validations(lang, base_url, provider_domain)

    def get_third_party_verifier(self, validations: list[ValidationDto]) -> OpenEpdIlcdOrg | None:
        """Return first third party verifier."""
        for verifier in validations:
            if verifier.validation_type in (
                IlcdTypeOfReview.IndependentExternalReview,
                IlcdTypeOfReview.AccreditedThirdPartyReview,
            ):
                return verifier.org
        return None

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

    def get_scenario_names(self, lang: LangDef) -> dict[str, str]:
        """Return dictionary with mapping short scenario names to full names in given language."""
        scenarios = self._get_all_els(
            self.epd_el_tree,
            (
                "process:processInformation",
                "process:dataSetInformation",
                "common:other",
                "epd2013:scenarios",
                "epd2013:scenario",
            ),
        )

        result: dict[str, str] = dict()

        for scenario in scenarios:
            if not scenario.attrib:
                continue

            short_name = scenario.attrib.get("{http://www.iai.kit.edu/EPD/2013}name")
            name = self._get_localized_text(scenario, ("epd2013:description",), lang)

            if name and short_name:
                result[short_name] = name

        return result

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

    def get_exchanges_reader(self) -> IlcdExchangesReader | None:
        """Return the LCIA results reader."""
        element = self._get_el(
            self.epd_el_tree,
            ("process:exchanges",),
        )
        return self.exchanges_reader_cls(element, self.data_provider) if element is not None else None

    def get_lcia_results(self, scenario_names: dict[str, str]) -> ImpactSet | None:
        """Return the LCIA results."""
        reader = self.get_lcia_results_reader()
        if reader is None:
            return None
        return reader.get_impact_set(scenario_names)

    def get_impacts(self, scenario_names: dict[str, str], lca_method: str | None = None) -> Impacts | None:
        """Return the LCIA results."""
        reader = self.get_lcia_results_reader()
        if reader is None:
            return None
        return reader.to_openepd_impacts(scenario_names, lcia_method=lca_method)

    def get_resource_uses(self, scenario_names: dict[str, str]) -> ResourceUseSet | None:
        """Return resource uses."""
        reader = self.get_exchanges_reader()
        if reader is None:
            return None
        return reader.get_resource_uses(scenario_names)

    def get_output_flows(self, scenario_names: dict[str, str]) -> OutputFlowSet | None:
        """Return output flows."""
        reader = self.get_exchanges_reader()
        if reader is None:
            return None
        return reader.get_output_flows(scenario_names)

    def _product_classes_to_openepd(self, classes: dict[str, list[ProductClassDef]]) -> dict[str, list[str] | str]:
        result: dict[str, list[str] | str] = {}
        for classification_name, class_defs in classes.items():
            if len(class_defs) > 0:
                result[classification_name] = (
                    (class_defs[-1].id or "") + " " + " / ".join([none_throws(x.name) for x in class_defs])
                ).strip()
        return result

    def to_openepd_epd(
        self, lang: LangDef, base_url: str | None = None, provider_domain: str | None = None
    ) -> Epd:  # NOSONAR
        """Return the EPD as OpenEPD object."""
        if provider_domain is None:
            provider_domain = provider_domain_name_from_url(base_url)
        lang_code = lang if isinstance(lang, str) else None
        if isinstance(lang, Sequence):
            lang_code = lang[0] if len(lang) > 0 else None
        manufacturer_reader = self.get_manufacturer_reader()
        manufacturer = (
            manufacturer_reader.to_openepd_org(lang, base_url, provider_domain) if manufacturer_reader else None
        )
        publisher_reader = self.get_publisher_reader()
        publisher = publisher_reader.to_openepd_org(lang, base_url, provider_domain) if publisher_reader else None
        program_operator_reader = self.get_program_operator_reader()
        program_operator = (
            program_operator_reader.to_openepd_org(lang, base_url, provider_domain) if program_operator_reader else None
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
        scenario_names = self.get_scenario_names(lang)

        compliance = self.get_openepd_compliance(lang, base_url)
        lcia_method: str | None = None
        for c in compliance:
            mapped = self.standard_names_to_lcia_mapper.map(c.short_name, None)
            if mapped:
                lcia_method = mapped
                break

        epd_developer = self.get_data_entry_by(lang, base_url)
        epd_developer_contact = epd_developer.get_contact() if epd_developer else None
        ilcd_validations = self.get_ilcd_validations(lang, base_url, provider_domain)
        epd = Epd(
            doctype="OpenEPD",
            language=lang_code,
            attachments=create_openepd_attachments(own_ref, base_url) if base_url else None,  # type: ignore
            declaration_url=own_ref.to_url(base_url) if own_ref and base_url else None,  # type: ignore
            product_name=product_name,
            product_description=trim_text(self.get_product_description(lang), 2000, ellipsis="..."),
            date_of_issue=self.get_date_published(),
            valid_until=self.get_validity_ends_date(),
            program_operator_doc_id=self.get_program_operator_id(),
            manufacturer=manufacturer,
            epd_developer=epd_developer,
            epd_developer_email=epd_developer_contact.email if epd_developer_contact else None,
            program_operator=program_operator,
            product_classes=self._product_classes_to_openepd(self.get_product_classes()),
            manufacturing_description=self.get_technology_description(lang),
            product_usage_description=self.get_technological_applicability(lang),
            lca_discussion=self.get_lca_discussion(lang),
            third_party_verifier=self.get_third_party_verifier(ilcd_validations),
            pcr=pcr,
            declared_unit=declared_unit,
            impacts=self.get_impacts(scenario_names, lca_method=lcia_method),
            resource_uses=self.get_resource_uses(scenario_names),
            output_flows=self.get_output_flows(scenario_names),
            specs=specs,
            compliance=compliance,
        )
        if own_ref:
            epd.set_alt_id(provider_domain, own_ref.entity_id)

        pdf_url = self.data_provider.get_pdf_url()
        epd.set_attachment_if_any(const.PDF_ATTACHMENT, pdf_url)
        epd.set_attachment_if_any(const.URL_ATTACHMENT, self.get_url_attachment(lang))

        ilcd_ext = IlcdEpdExtension(
            dataset_type=self.get_dataset_type(),
            dataset_version=self.get_version(),
            dataset_uuid=self.get_uuid(),
            production_location=self.get_production_location(),
            epd_verifiers=ilcd_validations,
        )
        if publisher:
            ilcd_ext.epd_publishers.append(publisher)
        epd.set_ext(ilcd_ext)
        return epd

    @classmethod
    def is_known_url(cls, url: str) -> bool:
        """
        Return whether the URL recognized by this particular reader.

        This method should be overriden by the dialect and return true if the input URL is know url for this dialect.
        """

        return False
