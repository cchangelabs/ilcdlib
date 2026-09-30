#
#  Copyright 2026 by C Change Labs Inc. www.c-change-labs.com
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
from unittest import TestCase

from ilcdlib.mapping.impacts import DefaultImpactsToOpenIdMapper

INDICATOR_DATA = {
    "test data": {
        "f7c73bb9-ab1a-4249-9c6d-379a0de6f67e": (
            "Abiotic depletion potential for non fossil resources (ADPE)",
            None,
            "gwp-nonCO2",
        ),
        "804ebcdf-309d-4098-8ed8-fdaf2f389981": (
            "Abiotic depletion potential for fossil resources (ADPF)",
            None,
            None,
        ),
        "b4274add-93b7-4905-a5e4-2e878c4e4216": (
            "Acidification potential of soil and water (AP)",
            "ap",
            "ap",
        ),
        "f58827d0-b407-4ec6-be75-8b69efb98a0f": ("Eutrophication potential (EP)", "ep-fresh", None),
        "77e416eb-a363-4258-a04e-171d843a6460": ("Global warming potential (GWP)", "gwp", "gwp"),
        "06dcd26f-025f-401a-a7c1-5e457eb54637": (
            "Depletion potential of the stratospheric ozone layer (ODP)",
            "odp",
            "odp",
        ),
        "1e84a202-dae6-42aa-9e9d-71ea48b8be00": (
            "Formation potential of tropospheric ozone (POCP)",
            "pocp",
            "pocp",
        ),
    },
    "EnvironDec dataset 941678b5-658d-4ff8-3901-08dec303011a": {
        "b2ad6110-c78d-11e6-9d9d-cec0c932ce01": (
            "Abiotic depletion potential - fossil resources (ADPF)",
            None,
            None,
        ),
        "b2ad6494-c78d-11e6-9d9d-cec0c932ce01": (
            "Abiotic depletion potential - non-fossil resources (ADPE)",
            None,
            None,
        ),
        "b5c611c6-def3-11e6-bf01-fe55135034f3": (
            "Acidifcation potential, Accumulated Exceedance (AP)",
            "ap",
            "ap",
        ),
        "b5c629d6-def3-11e6-bf01-fe55135034f3": (
            "Depletion potential of the stratospheric ozone layer (ODP)",
            None,
            "odp",
        ),
        "05316e7a-b254-4bea-9cf0-6bf33eb5c630": ("Eco-toxicity - freshwater (ETP-fw)", None, None),
        "b53ec18f-7377-4ad3-86eb-cc3f4f276b2b": (
            "Europhication potential - freshwater (EP-freshwater)",
            "ep-fresh",
            "ep-fresh",
        ),
        "b5c619fa-def3-11e6-bf01-fe55135034f3": (
            "Europhication potential - marine (EP-marine)",
            "ep-marine",
            "ep-marine",
        ),
        "b5c614d2-def3-11e6-bf01-fe55135034f3": (
            "Europhication potential - terrestrial (EP-terrestrial)",
            "ep-terr",
            "ep-terr",
        ),
        "e03c018f-8526-44bc-b5e4-bc03c3ab32f3": ("Global Warming Potential (GWP-GHG)", None, "gwp"),
        "a7ea186c-9749-11ed-a8fc-0242ac120002": (
            "Global Warming Potential - biogenic (GWP-biogenic)",
            None,
            "gwp-biogenic",
        ),
        "a7ea19c0-9749-11ed-a8fc-0242ac120002": (
            "Global Warming Potential - fossil fuels (GWP-fossil)",
            None,
            "gwp-fossil",
        ),
        "a7ea1ae2-9749-11ed-a8fc-0242ac120002": (
            "Global Warming Potential - land use and land use change (GWP-luluc)",
            None,
            "gwp-luluc",
        ),
        "a7ea142a-9749-11ed-a8fc-0242ac120002": ("Global Warming Potential - total (GWP-total)", None, "gwp"),
        "2299222a-bbd8-474f-9d4f-4dd1f18aea7c": ("Human toxicity, cancer effect (HTP-c)", None, None),
        "7cfdcfcf-b222-4b26-888a-a55f9fbf7ac8": ("Human toxicity, non-cancer effects (HTP-nc)", None, None),
        "b5c632be-def3-11e6-bf01-fe55135034f3": ("Ionizing radiation, human health (IRP)", None, None),
        "b2ad6890-c78d-11e6-9d9d-cec0c932ce01": ("Land use related impacts/Soil quality (SQP)", None, None),
        "b5c602c6-def3-11e6-bf01-fe55135034f3": ("Particulate Matter emissions (PM)", None, None),
        "b5c610fe-def3-11e6-bf01-fe55135034f3": (
            "Photochemical Ozone Creation Potential (POCP)",
            None,
            "pocp",
        ),
        "b2ad66ce-c78d-11e6-9d9d-cec0c932ce01": ("Water (user) deprivation potential (WDP)", "WDP", None),
    },
}

MAPPING_EXAMPLES = (
    ("unknown UUID uses default", "00000000-0000-0000-0000-000000000000", "custom", "custom"),
    ("keyword takes precedence over regex", "GWP terrestrial impact", "custom", "ep-terr"),
    (
        "keyword matching is case-insensitive",
        "DEPLETION POTENTIAL OF THE STRATOSPHERIC OZONE LAYER (ODP)",
        None,
        "odp",
    ),
    ("freshwater eutrophication", "Europhication potential - freshwater (EP-freshwater)", None, "ep-fresh"),
    ("freshwater ecotoxicity", "Eco-toxicity - freshwater (ETP-fw)", None, None),
    ("regex match", "Global warming potential (GWP)", None, "gwp"),
    ("unmatched input uses default", "Unknown metric", "custom", "custom"),
)


class DefaultImpactsToOpenIdMapperTestCase(TestCase):
    def setUp(self) -> None:
        self.mapper = DefaultImpactsToOpenIdMapper()

    def test_maps_dataset_indicators(self) -> None:
        for dataset, indicators in INDICATOR_DATA.items():
            for uuid, (indicator_name, uuid_expected, name_expected) in indicators.items():
                with self.subTest(dataset=dataset, uuid=uuid):
                    self.assertEqual(self.mapper.map(uuid, None), uuid_expected)
                with self.subTest(dataset=dataset, indicator_name=indicator_name):
                    self.assertEqual(self.mapper.map(indicator_name, None), name_expected)

    def test_maps_behavior_examples(self) -> None:
        for description, input_value, default, expected in MAPPING_EXAMPLES:
            with self.subTest(example=description):
                self.assertEqual(self.mapper.map(input_value, default), expected)
