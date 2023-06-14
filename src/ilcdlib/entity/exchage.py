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
from typing import Type, TypeVar

from openepd.model.lcia import OutputFlowSet, ResourceUseSet, ScopeSet

from ilcdlib.entity.base_scope_set_reader import BaseIlcdScopeSetsReader
from ilcdlib.mapping.common import SimpleDataMapper
from ilcdlib.mapping.flows import default_flows_uuid_mapper
from ilcdlib.mapping.indicators import default_indicators_uuid_mapper
from ilcdlib.xml_parser import T_ET

E = TypeVar("E", ResourceUseSet, OutputFlowSet)


class IlcdExchangesReader(BaseIlcdScopeSetsReader):
    """Read exchanges from XML file."""

    def __init__(
        self,
        *args,
        indicator_mapper: SimpleDataMapper[str] = default_indicators_uuid_mapper,
        flow_mapper: SimpleDataMapper[str] = default_flows_uuid_mapper,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.indicator_mapper = indicator_mapper
        self.flow_mapper = flow_mapper

    def __get_exchange_direction(self, el: T_ET.Element) -> str | None:
        exchange_direction = self._get_el(el, "process:exchangeDirection")
        if exchange_direction is not None:
            return exchange_direction.text
        return None

    def get_resource_uses(self, scenario_names: dict[str, str]) -> ResourceUseSet:
        """Get resource uses from the ILCD EPD file."""
        return self.__get_exchanges(
            direction="Input",
            scope_set_type=ResourceUseSet,
            mapper=self.indicator_mapper,
            scenario_names=scenario_names,
        )

    def get_output_flows(self, scenario_names: dict[str, str]) -> OutputFlowSet:
        """Get output flows from the ILCD EPD file."""
        return self.__get_exchanges(
            direction="Output", scope_set_type=OutputFlowSet, mapper=self.flow_mapper, scenario_names=scenario_names
        )

    def __get_exchanges(
        self, direction: str, scope_set_type: Type[E], mapper: SimpleDataMapper[str], scenario_names: dict[str, str]
    ) -> E:
        """Get indicators or flows from the ILCD EPD file."""
        ext: dict[str, ScopeSet] = {}
        exchanges = self._get_all_els(self._entity, ("process:exchange",))
        scope_sets: dict[str, ScopeSet | dict] = {"ext": ext}

        for exchange in exchanges:
            if self.__get_exchange_direction(exchange) == direction:
                self._extract_and_set_scope_set(
                    el=exchange,
                    reference_path=("process:referenceToFlowDataSet",),
                    scope_set_type=scope_set_type,
                    scope_set_dict=scope_sets,
                    ext=ext,
                    mapper=mapper,
                    scenario_names=scenario_names,
                )

        if len(ext) == 0:
            del scope_sets["ext"]
        return scope_set_type(**scope_sets)  # type: ignore
