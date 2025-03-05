#
#  Copyright 2025 by C Change Labs Inc. www.c-change-labs.com
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
import unittest

from ilcdlib.entity.material import MatMlMaterial, MatMlMaterialProperty, MatMlReader


class MeterialMlParserTestCase(unittest.TestCase):
    def test_reading_valid(self):
        test_cases: list[tuple[str, MatMlMaterial]] = [
            (
                """
<mm:MatML_Doc xmlns:mm="http://www.matml.org/" xmlns="http://www.matml.org/">
   <Material>
      <BulkDetails>
         <Name>test-material</Name>
         <PropertyData property="pr2">
            <Data format="float">138.696</Data>
         </PropertyData>
         <PropertyData property="pr3">
            <Data format="float">123.0</Data>
         </PropertyData>
      </BulkDetails>
   </Material>
   <Metadata>
      <PropertyDetails id="pr2">
         <Name>gross density</Name>
         <Units name="kg/m^3" description="kilograms per cubic metre">
            <Unit>
               <Name>kg</Name>
            </Unit>
            <Unit power="-3">
               <Name>m</Name>
            </Unit>
         </Units>
      </PropertyDetails>
      <PropertyDetails id="pr3">
         <Name>conversion factor to 1 kg</Name>
         <Units name="-" description="Without Unit">
            <Unit>
               <Name>-</Name>
            </Unit>
         </Units>
      </PropertyDetails>
   </Metadata>
</mm:MatML_Doc>
            """,
                MatMlMaterial(
                    name="test-material",
                    properties={
                        "gross density": MatMlMaterialProperty(
                            value=138.696, unit="kg/m^3", data_format="float", internal_id="pr2"
                        ),
                        "conversion factor to 1 kg": MatMlMaterialProperty(
                            value=123.0, unit=None, data_format="float", internal_id="pr3"
                        ),
                    },
                ),
            ),
        ]
        i = 1
        for xml, expected in test_cases:
            with self.subTest(f"TC-{i}"):
                actual = MatMlReader(xml).get_material()
                self.assertEqual(expected, actual)
            i += 1
