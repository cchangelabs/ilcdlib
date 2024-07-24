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
import logging

from openepd.model.common import Measurement
from openepd.model.lcia import Impacts, ImpactSet, ScopeSet

from ilcdlib.common import OpenEpdImpactSetSupportReader
from ilcdlib.entity.base_scope_set_reader import BaseIlcdScopeSetsReader
from ilcdlib.mapping.common import BaseDataMapper
from ilcdlib.mapping.impacts import default_impacts_mapper
from ilcdlib.mapping.units import default_scope_to_units_mapper


class IlcdLciaResultsReader(OpenEpdImpactSetSupportReader, BaseIlcdScopeSetsReader):
    """Read an ILCD PCR XML file."""

    def __init__(
        self,
        *args,
        impact_mapper: BaseDataMapper[str, str] = default_impacts_mapper,
        scope_to_units_mapper: BaseDataMapper[str, str] = default_scope_to_units_mapper,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.impact_mapper = impact_mapper
        self.scope_to_units_mapper = scope_to_units_mapper

    def get_impact_set(self, scenario_names: dict[str, str]) -> ImpactSet:
        """Get the impacts from the ILCD EPD file."""
        ext: dict[str, ScopeSet] = {}
        lcia_results = self._get_all_els(self._entity, ("process:LCIAResult",))
        impacts: dict[str, ScopeSet | dict] = {"ext": ext}

        for lr in lcia_results:
            self._extract_and_set_scope_set(
                el=lr,
                reference_path=("process:referenceToLCIAMethodDataSet",),
                scope_set_type=ImpactSet,
                scope_set_dict=impacts,
                ext=ext,
                mapper=self.impact_mapper,
                scenario_names=scenario_names,
                scope_to_units_mapper=self.scope_to_units_mapper,
            )

        self._extract_and_set_a1a2a3_impact(impacts)

        if len(ext) == 0:
            del impacts["ext"]
        return ImpactSet(**impacts)  # type: ignore

    @staticmethod
    def __process_a1a2a3_impact(scope_set: ScopeSet) -> None:
        if scope_set.A1A2A3 is None and (scope_set.A1 or scope_set.A2 or scope_set.A3):
            s: float = 0
            unit = None

            for a_impact in (scope_set.A1, scope_set.A2, scope_set.A3):
                if a_impact:
                    if unit and unit != a_impact.unit:
                        logging.warning(f"Units in A impacts does not match each other in {scope_set}")
                        return
                    unit = a_impact.unit
                    s += a_impact.mean

            scope_set.A1A2A3 = Measurement(mean=s, unit=unit)

    def _extract_and_set_a1a2a3_impact(self, impacts: dict[str, ScopeSet | dict]) -> None:
        """Set A1A2A3 value if None provided."""

        for impact_value in impacts.values():
            if type(impact_value) is dict:
                for v in impact_value.values():
                    self.__process_a1a2a3_impact(v)
            if type(impact_value) is ScopeSet:
                self.__process_a1a2a3_impact(impact_value)

    def to_openepd_impacts(
        self,
        scenario_names: dict[str, str],
        lcia_method: str | None = None,
        base_url: str | None = None,
        provider_domain: str | None = None,
    ) -> Impacts:
        """Read as openEPD ImpactSet object."""
        impact_set = self.get_impact_set(scenario_names)
        impacts = Impacts(__root__={})
        impacts.set_impact_set(lcia_method, impact_set)
        return impacts
