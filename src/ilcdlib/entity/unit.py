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

from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader
from ilcdlib.mapping.common import SimpleDataMapper
from ilcdlib.mapping.units import default_units_uuid_mapper
from ilcdlib.type import LangDef
from ilcdlib.utils import none_throws
from ilcdlib.xml_parser import T_ET


@dataclass(kw_only=True)
class UnitDto:
    """A DTO representing ILCD unit object."""

    name: str
    mean_value: float


class IlcdUnitGroupReader(IlcdXmlReader):
    """Read an ILCD Unit Group XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        unit_mapper: SimpleDataMapper[str] = default_units_uuid_mapper,
    ):
        super().__init__(data_provider)
        self._entity = element
        self.unit_mapper = unit_mapper

    def get_uuid(self) -> str:
        """Get the UUID of the entity described by this data set."""
        return none_throws(
            self._get_text(self._entity, ("ug:unitGroupInformation", "ug:dataSetInformation", "common:UUID"))
        )

    def get_version(self) -> str | None:
        """Get the version of the entity described by this data set."""
        return self._get_text(
            self._entity,
            ("ug:administrativeInformation", "ug:publicationAndOwnership", "common:dataSetVersion"),
        )

    def get_name(self, lang: LangDef) -> str | None:
        """Get the name of the entity described by this data set."""
        return self._get_localized_text(
            self._entity, ("flow:flowInformation", "flow:dataSetInformation", "flow:name", "flow:baseName"), lang
        )

    def get_ref_to_reference_unit(self) -> int | None:
        """Get the internal id of the reference flow property."""
        return self._get_int(
            self._entity, ("ug:unitGroupInformation", "ug:quantitativeReference", "ug:referenceToReferenceUnit")
        )

    def get_reference_unit(self, allow_mapping: bool = True) -> UnitDto | None:
        """Get the reader for the reference flow property with the given id."""
        reference_unit_id = self.get_ref_to_reference_unit()
        if reference_unit_id is None:
            return None
        element = self._get_el(
            self._entity,
            (
                "ug:units",
                f"ug:unit[@dataSetInternalID='{reference_unit_id}']",
            ),
        )
        if element is None:
            return None
        unit_name = none_throws(self._get_text(element, "ug:name"))
        unit_uuid = self.get_uuid()
        if allow_mapping and unit_uuid is not None:
            unit_name = self.unit_mapper.map(unit_uuid, unit_name)
        return (
            UnitDto(
                name=unit_name,
                mean_value=none_throws(self._get_float(element, "ug:meanValue")),
            )
            if element is not None
            else None
        )
