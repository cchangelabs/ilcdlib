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
from typing import Type

from openepd.model.common import Measurement
from openepd.model.lcia import ImpactSet, ScopeSet

from ilcdlib.common import BaseIlcdMediumSpecificReader, IlcdXmlReader, OpenEpdImpactSetSupportReader
from ilcdlib.entity.unit import IlcdUnitGroupReader
from ilcdlib.mapping.common import SimpleDataMapper
from ilcdlib.mapping.impacts import default_impacts_uuid_mapper
from ilcdlib.type import LangDef
from ilcdlib.xml_parser import T_ET


class IlcdLciaResultsReader(OpenEpdImpactSetSupportReader, IlcdXmlReader):
    """Read an ILCD PCR XML file."""

    def __init__(
        self,
        element: T_ET.Element,
        data_provider: BaseIlcdMediumSpecificReader,
        *,
        unit_group_reader_cls: Type[IlcdUnitGroupReader] = IlcdUnitGroupReader,
        impact_mapper: SimpleDataMapper[str] = default_impacts_uuid_mapper,
    ):
        super().__init__(data_provider)
        self._entity = element
        self.impact_mapper = impact_mapper
        self.unit_group_reader_cls = unit_group_reader_cls

    def _get_scope_set_for_el(self, el: T_ET.Element) -> tuple[ScopeSet, str] | None:
        # Impact name
        type_el = self._get_el(el, ("process:referenceToLCIAMethodDataSet"))
        if type_el is None:
            return None
        type_uuid = type_el.attrib.get("refObjectId") if type_el is not None else None
        if type_uuid is None:
            return None
        impact_name: str | None = self.impact_mapper.map(type_uuid, type_uuid)
        if impact_name == type_uuid:
            impact_name = self._get_localized_text(
                el, ("process:referenceToLCIAMethodDataSet", "common:shortDescription"), ("en", None)
            )
        if impact_name is None:
            return None
        # UoM
        unit_el = self._get_external_tree(
            el,
            (
                "common:other",
                "epd2013:referenceToUnitGroupDataSet",
            ),
        )
        if unit_el is None:
            return None
        unit = self.unit_group_reader_cls(unit_el, self.data_provider).get_reference_unit(allow_mapping=True)
        unit_name: str | None
        if unit is not None:
            unit_name = unit.name
        else:
            unit_name = self._get_text(
                el, ("common:other", "epd2013:referenceToUnitGroupDataSet", "common:shortDescription")
            )
        if unit_name is None:
            return None
        # Stages
        scopes = self.__extract_scopes(el, unit_name)
        return ScopeSet.construct(**scopes), impact_name  # type: ignore

    def __extract_scopes(self, el: T_ET.Element, unit_name: str) -> dict[str, Measurement | dict]:
        ext: dict[str, Measurement] = {}
        scopes: dict[str, Measurement | dict] = {"ext": ext}
        for al in self._get_all_els(el, ("common:other", "epd2013:amount")):
            module_name = al.attrib.get("{http://www.iai.kit.edu/EPD/2013}module") if al.attrib else None
            module_name = self.__map_module_name(module_name)
            scenario_name = al.attrib.get("{http://www.iai.kit.edu/EPD/2013}scenario") if al.attrib else None
            if scenario_name is not None:
                continue  # TODO: Add support for scenarios
            if module_name is None or al.text is None:
                continue
            try:
                value = float(al.text)
            except ValueError:
                continue
            measurement = Measurement(mean=value, unit=unit_name)
            if ScopeSet.is_allowed_field_name(module_name):  # type: ignore
                scopes[module_name] = measurement
            else:
                ext[module_name] = measurement
        if len(ext) == 0:
            del scopes["ext"]
        return scopes

    def get_impacts(self) -> ImpactSet:
        """Get the impacts from the ILCD EPD file."""
        ext: dict[str, ScopeSet] = {}
        lcia_resilts = self._get_all_els(self._entity, ("process:LCIAResult",))
        impacts: dict[str, ScopeSet | dict] = {"ext": ext}
        for lr in lcia_resilts:
            scope_set_and_impact_name = self._get_scope_set_for_el(lr)
            if scope_set_and_impact_name is None:
                continue
            scope_set, impact_name = scope_set_and_impact_name
            if ImpactSet.is_allowed_field_name(impact_name):
                impacts[impact_name] = scope_set
            else:
                ext[impact_name] = scope_set
        if len(ext) == 0:
            del impacts["ext"]
        return ImpactSet.construct(**impacts)  # type: ignore

    def to_openepd_impact_set(self, lang: LangDef, base_url: str | None = None) -> ImpactSet:
        """Read as openEPD ImpactSet object."""
        return self.get_impacts()

    def __map_module_name(self, module_name: str | None) -> str | None:
        if module_name == "A1-A3":
            return "A1A2A3"
        return module_name
