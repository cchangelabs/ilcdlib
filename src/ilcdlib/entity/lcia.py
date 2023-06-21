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
from openepd.model.lcia import Impacts, ImpactSet, ScopeSet

from ilcdlib.common import OpenEpdImpactSetSupportReader
from ilcdlib.entity.base_scope_set_reader import BaseIlcdScopeSetsReader
from ilcdlib.mapping.common import SimpleDataMapper
from ilcdlib.mapping.impacts import default_impacts_uuid_mapper


class IlcdLciaResultsReader(OpenEpdImpactSetSupportReader, BaseIlcdScopeSetsReader):
    """Read an ILCD PCR XML file."""

    def __init__(
        self,
        *args,
        impact_mapper: SimpleDataMapper[str] = default_impacts_uuid_mapper,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.impact_mapper = impact_mapper

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
            )
        if len(ext) == 0:
            del impacts["ext"]
        return ImpactSet(**impacts)  # type: ignore

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
