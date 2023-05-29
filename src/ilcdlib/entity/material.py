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
import dataclasses
from enum import StrEnum
from typing import IO, Literal

from ilcdlib.xml_parser import T_ET, XmlParser


class IlcdStandardMatProperties(StrEnum):
    """Represent ILCD standard material properties."""

    GrossDensity = "gross density"
    BulkDensity = "bulk density"
    LinearDensity = "linear density"
    ConversionToKgFactor = "conversion factor to 1 kg"
    Grammage = "grammage"
    LayerThickness = "layer thickness"
    Productiveness = "productiveness"


@dataclasses.dataclass
class MatMlMaterialProperty:
    """Represent MatML Material Property."""

    value: str | int | float | None
    data_format: Literal["float", "integer", "string", "exponential", "mixed"]
    unit: str | None = None
    internal_id: str | None = None

    def to_unit_string(self) -> str | None:
        """Get unit string."""
        if self.value is not None and self.unit is not None:
            return f"{self.value} {self.unit}"
        if self.unit is None and self.value is not None:
            return str(self.value)
        if self.data_format == "string" and self.value is not None:
            return str(self.value)
        return None


@dataclasses.dataclass
class MatMlMaterial:
    """Represent MatML Material."""

    name: str
    properties: dict[str, MatMlMaterialProperty] = dataclasses.field(default_factory=dict)


class MatMlReader:
    """Reader for MatML XML format."""

    def __init__(self, element_or_stream: T_ET.Element | str | IO[str]):
        self.xml_parser = XmlParser(
            ns_map={
                "mm": "http://www.matml.org/",
            }
        )
        if isinstance(element_or_stream, (str, IO)):
            self._entity = self.xml_parser.get_xml_tree(element_or_stream)
        else:
            self._entity = element_or_stream
        if hasattr(self._entity, "nsmap") and None not in self._entity.nsmap.keys():  # type: ignore
            self._entity.nsmap[None] = "http://www.matml.org/"

    def get_material(self) -> MatMlMaterial | None:
        """Get MatML Material from XML."""
        material_name = self.xml_parser.get_el_text(self._entity, "mm:Material/mm:BulkDetails/mm:Name")
        if material_name is None:
            return None
        result = MatMlMaterial(name=material_name)
        all_props_data = self.xml_parser.get_all_els(self._entity, "mm:Material/mm:BulkDetails/mm:PropertyData")
        for prop_el in all_props_data:
            prop_ref = prop_el.attrib.get("property") if prop_el.attrib else None
            prop_data = self.xml_parser.get_el(prop_el, "mm:Data")
            prop_format, prop_value = self.__parse_prop_data(prop_data)
            if prop_ref is None or prop_value is None:
                continue
            prop_meta = self.xml_parser.get_el(self._entity, f"mm:Metadata/mm:PropertyDetails[@id='{prop_ref}']")
            if prop_meta is None:
                continue
            prop_name = self.xml_parser.get_el_text(prop_meta, "mm:Name")
            if prop_name is None:
                continue
            prop_name = prop_name.lower()
            units_obj = self.xml_parser.get_el(prop_meta, "mm:Units")
            if units_obj is None:
                continue
            unit = self.__map_unit_name(units_obj.attrib.get("name")) if units_obj.attrib else None
            result.properties[prop_name] = MatMlMaterialProperty(
                value=prop_value, data_format=prop_format, unit=unit, internal_id=prop_ref  # type: ignore
            )
        return result

    def __map_unit_name(self, unit_name: str | None) -> str | None:
        if unit_name is None:
            return None
        match unit_name.strip():
            case "-":
                return None
            case _:
                return unit_name

    def __parse_prop_data(
        self, prop_data
    ) -> tuple[Literal["float", "integer", "string", "exponential", "mixed"], str | int | float | None]:
        prop_format = prop_data.attrib.get("format") if prop_data is not None else None
        prop_value_raw = prop_data.text if prop_data is not None else None
        match prop_format:
            case "float":
                prop_value = float(prop_value_raw)
            case "integer":
                prop_value = int(prop_value_raw)
            case _:
                prop_value = prop_value_raw
        return prop_format, prop_value
