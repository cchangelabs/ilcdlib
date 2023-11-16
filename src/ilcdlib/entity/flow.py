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
from dataclasses import dataclass
from typing import Optional, Type

from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader
from ilcdlib.entity.material import MatMlReader
from ilcdlib.entity.unit import IlcdUnitGroupReader
from ilcdlib.mapping.properties import PropertiesUUIDMapper, default_properties_uuid_mapper
from ilcdlib.type import LangDef
from ilcdlib.utils import none_throws
from ilcdlib.xml_parser import T_ET


class IlcdFlowPropertyReader(IlcdXmlReader):
    """Read an ILCD Flow Property XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        unit_group_reader_cls: Type[IlcdUnitGroupReader] = IlcdUnitGroupReader,
        property_uuid_mapper: PropertiesUUIDMapper = default_properties_uuid_mapper,
    ):
        super().__init__(data_provider)
        self._entity = element
        self.unit_group_reader_cls = unit_group_reader_cls
        self.property_uuid_mapper = property_uuid_mapper

    def get_uuid(self) -> str:
        """Get the UUID of the entity described by this data set."""
        return none_throws(
            self._get_text(self._entity, ("fp:flowPropertiesInformation", "fp:dataSetInformation", "common:UUID"))
        )

    def get_version(self) -> str | None:
        """Get the version of the entity described by this data set."""
        return self._get_text(
            self._entity,
            ("fp:flowPropertiesInformation", "fp:publicationAndOwnership", "common:dataSetVersion"),
        )

    def get_name(self, lang: LangDef, use_mapper: bool = True) -> str | None:
        """Get the name of the entity described by this data set."""
        name = self._get_localized_text(
            self._entity, ("fp:flowPropertiesInformation", "fp:dataSetInformation", "common:name"), lang
        )
        if use_mapper:
            mapped_name = self.property_uuid_mapper.map(self.get_uuid(), name if name else "")
            return mapped_name if mapped_name is not None else None
        else:
            return name

    def get_unit_group_reader(self) -> IlcdUnitGroupReader | None:
        """Get the reader for the unit group."""
        element = self._get_external_tree(
            self._entity,
            ("fp:flowPropertiesInformation", "fp:quantitativeReference", "fp:referenceToReferenceUnitGroup"),
        )
        return self.unit_group_reader_cls(element, self.data_provider) if element is not None else None


@dataclass(kw_only=True)
class IlcdExchangeDto:
    """A DTO representing ILCD exchange object."""

    flow_dataset_reader: Optional["IlcdFlowReader"] = None
    mean_value: float | None = None


@dataclass(kw_only=True)
class IlcdFlowPropertyDto:
    """A DTO representing ILCD flow property object."""

    dataset_reader: IlcdFlowPropertyReader
    mean_value: float | None = None


class IlcdFlowReader(IlcdXmlReader):
    """Read an ILCD Flow XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        flow_property_reader_cls: Type[IlcdFlowPropertyReader] = IlcdFlowPropertyReader,
        mat_ml_reader_cls: Type[MatMlReader] = MatMlReader,
    ):
        super().__init__(data_provider)
        self._entity = element
        self.flow_property_reader_cls = flow_property_reader_cls
        self.mat_ml_reader_cls = mat_ml_reader_cls

    def get_uuid(self) -> str:
        """Get the UUID of the entity described by this data set."""
        return none_throws(
            self._get_text(self._entity, ("flow:flowInformation", "flow:dataSetInformation", "common:UUID"))
        )

    def get_version(self) -> str | None:
        """Get the version of the entity described by this data set."""
        return self._get_text(
            self._entity,
            ("flow:administrativeInformation", "flow:publicationAndOwnership", "common:dataSetVersion"),
        )

    def get_name(self, lang: LangDef) -> str | None:
        """Get the name of the entity described by this data set."""
        return self._get_localized_text(
            self._entity, ("flow:flowInformation", "flow:dataSetInformation", "flow:name", "flow:baseName"), lang
        )

    def get_ref_to_reference_flow_prop(self) -> int | None:
        """Get the internal id of the reference flow property."""
        return self._get_int(
            self._entity,
            ("flow:flowInformation", "flow:quantitativeReference", "flow:referenceToReferenceFlowProperty"),
        )

    def get_material_reader(self) -> MatMlReader | None:
        """Get the reader for the material properties."""
        element = self._get_el(
            self._entity,
            (
                "flow:flowInformation",
                "flow:dataSetInformation",
                "common:other",
                "mm:MatML_Doc",
            ),
        )
        return self.mat_ml_reader_cls(element) if element is not None else None

    def get_reference_flow_property(
        self,
    ) -> IlcdFlowPropertyDto | None:
        """Get the reader for the reference flow property with the given id."""
        reference_flow_property_id = self.get_ref_to_reference_flow_prop()
        if reference_flow_property_id is None:
            return None
        element = self._get_el(
            self._entity,
            (
                "flow:flowProperties",
                f"flow:flowProperty[@dataSetInternalID='{reference_flow_property_id}']",
            ),
        )
        if element is not None:
            flow_prop_el = self._get_external_tree(element, ("flow:referenceToFlowPropertyDataSet",))
            if flow_prop_el is None:
                return None
            return IlcdFlowPropertyDto(
                dataset_reader=self.flow_property_reader_cls(flow_prop_el, self.data_provider),
                mean_value=self._get_float(element, ("flow:meanValue",)),
            )
        return None

    def get_flow_other_properties(self, include_ref_flow_prop: bool = False) -> list[IlcdFlowPropertyDto]:
        """Get the reader for the other flow properties."""
        reference_flow_property_id = self.get_ref_to_reference_flow_prop() if include_ref_flow_prop else None
        flow_elements = self._get_all_els(
            self._entity,
            (
                "flow:flowProperties",
                "flow:flowProperty",
            ),
        )
        result: list[IlcdFlowPropertyDto] = []
        for e in flow_elements:
            if reference_flow_property_id is not None and e.attrib["dataSetInternalID"] == str(
                reference_flow_property_id
            ):
                continue
            flow_prop_el = self._get_external_tree(e, ("flow:referenceToFlowPropertyDataSet",))
            if flow_prop_el is None:
                continue
            result.append(
                IlcdFlowPropertyDto(
                    dataset_reader=self.flow_property_reader_cls(flow_prop_el, self.data_provider),
                    mean_value=self._get_float(e, ("flow:meanValue",)),
                )
            )
        return result
