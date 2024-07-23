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
from typing import Type

from openepd.model.base import BaseOpenEpdSchema
from openepd.model.common import Measurement
from openepd.model.lcia import EolScenario, ScopeSet

from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader, XmlPath
from ilcdlib.entity.unit import IlcdUnitGroupReader
from ilcdlib.mapping.common import BaseDataMapper
from ilcdlib.xml_parser import T_ET


class BaseIlcdScopeSetsReader(IlcdXmlReader):
    """Read scope sets from XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        unit_group_reader_cls: Type[IlcdUnitGroupReader] = IlcdUnitGroupReader,
    ):
        super().__init__(data_provider)
        self._entity = element
        self.unit_group_reader_cls = unit_group_reader_cls

    def _get_scope_set_for_el(
        self,
        el: T_ET.Element,
        reference_data_set: XmlPath,
        mapper: BaseDataMapper[str, str],
        scenario_names: dict[str, str],
        scope_to_units_mapper: BaseDataMapper[str, str],
    ) -> tuple[ScopeSet, str] | None:
        """Extract all scope set information from element."""
        # Impact name
        type_el = self._get_el(el, reference_data_set)
        if type_el is None:
            return None
        type_uuid = type_el.attrib.get("refObjectId") if type_el is not None else None
        if type_uuid is None:
            return None
        impact_name: str | None = mapper.map(type_uuid, type_uuid)
        if impact_name == type_uuid:
            description = self._get_localized_text(type_el, ("common:shortDescription",), ("en", None))
            if description is not None:
                impact_name = mapper.map(description, description)

        if impact_name is None:
            return None
        unit_el = self._get_external_tree(
            el,
            (
                "common:other",
                "epd2013:referenceToUnitGroupDataSet",
            ),
        )
        unit_name: str | None
        if unit_el is None:
            # This step is assumption for cases, when program operator omit unit group reference in related ILCD file.
            # In future, we should add context to the curator notes field for such cases.
            if unit_name := scope_to_units_mapper.map(impact_name, None):
                scopes = self.__extract_scopes(el, unit_name, scenario_names)
                return ScopeSet(**scopes), impact_name  # type: ignore
            return None
        unit = self.unit_group_reader_cls(unit_el, self.data_provider).get_reference_unit(allow_mapping=True)
        if unit is not None:
            unit_name = unit.name
        else:
            unit_name = self._get_text(
                el, ("common:other", "epd2013:referenceToUnitGroupDataSet", "common:shortDescription")
            )
        if unit_name is None:
            return None
        # Stages
        scopes = self.__extract_scopes(el, unit_name, scenario_names)
        return ScopeSet(**scopes), impact_name  # type: ignore

    def __extract_scopes(
        self, el: T_ET.Element, unit_name: str, scenario_names: dict[str, str]
    ) -> dict[str, Measurement | dict | list]:
        """Extract all scopes from scope set element."""
        ext: dict[str, Measurement] = {}
        scopes: dict[str, Measurement | dict | list] = {"ext": ext}
        for al in self._get_all_els(el, ("common:other", "epd2013:amount")):
            self.__extract_scope(al, ext, scopes, unit_name, scenario_names)
        if len(ext) == 0:
            del scopes["ext"]
        return scopes

    def __extract_scope(
        self,
        el: T_ET.Element,
        ext: dict[str, Measurement],
        scopes: dict[str, Measurement | dict | list],
        unit_name: str,
        scenario_names: dict[str, str],
    ) -> None:
        """Extract single scope from given element."""
        module_name = el.attrib.get("{http://www.iai.kit.edu/EPD/2013}module") if el.attrib else None
        module_name = self.__map_module_name(module_name)
        scenario_name = el.attrib.get("{http://www.iai.kit.edu/EPD/2013}scenario") if el.attrib else None

        if module_name is None or el.text is None:
            return None
        try:
            value = float(el.text)
        except ValueError:
            return None
        measurement = Measurement(mean=value, unit=unit_name)

        if scenario_name is None or scenario_name == "Standard scenario":
            if ScopeSet.is_allowed_field_name(module_name):  # type: ignore
                scopes[module_name] = measurement
            else:
                ext[module_name] = measurement
        else:
            if not EolScenario.is_allowed_field_name(module_name) or scenario_name not in scenario_names:
                return None

            scenarios = scopes.get("C_scenarios") or list()
            scenario: dict[str, Measurement | str] = dict(
                name=scenario_names[scenario_name],
            )
            scenario[module_name] = measurement
            scenarios.append(EolScenario(**scenario))  # type: ignore
            scopes["C_scenarios"] = scenarios

    @staticmethod
    def __map_module_name(module_name: str | None) -> str | None:
        if module_name == "A1-A3":
            return "A1A2A3"
        return module_name

    def _extract_and_set_scope_set(
        self,
        el: T_ET.Element,
        reference_path: XmlPath,
        scope_set_type: Type[BaseOpenEpdSchema],
        scope_set_dict: dict[str, ScopeSet | dict],
        ext: dict[str, ScopeSet],
        mapper: BaseDataMapper[str, str],
        scenario_names: dict[str, str],
        scope_to_units_mapper: BaseDataMapper[str, str],
    ) -> None:
        """Extract scope set from element and set to its dictionary."""
        scope_set_and_impact_name = self._get_scope_set_for_el(
            el, reference_path, mapper, scenario_names, scope_to_units_mapper
        )
        if scope_set_and_impact_name is None:
            return None
        scope_set, impact_name = scope_set_and_impact_name
        if scope_set_type.is_allowed_field_name(impact_name):
            scope_set_dict[impact_name] = scope_set
        else:
            ext[impact_name] = scope_set
