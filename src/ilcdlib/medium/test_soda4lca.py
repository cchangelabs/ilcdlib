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
from unittest import TestCase

from ilcdlib.dto import IlcdReference
from ilcdlib.medium.soda4lca import IlcdRemotePointer, Soda4LcaZipReader


class ZipMediumTestCase(TestCase):
    def test_endpoint_to_zip_conversion(self):
        test_cases: list[tuple[str, IlcdRemotePointer]] = [
            (
                "https://data.environdec.com/showProcess.xhtml?uuid=bfeb8678-b3cb-4a5b-b8cb-2512b551ad17&version=01.00.001&stock=Environdata",
                IlcdRemotePointer(
                    base_url="https://data.environdec.com/resource",
                    ref=IlcdReference(
                        entity_type="processes",
                        entity_version="01.00.001",
                        entity_id="bfeb8678-b3cb-4a5b-b8cb-2512b551ad17",
                    ),
                ),
            ),
            (
                "https://epdireland.lca-data.com/resource/processes/f256594a-a7bf-4bbb-91d0-65be256377c0/zipexport?version=00.03.001",
                IlcdRemotePointer(
                    base_url="https://epdireland.lca-data.com/resource",
                    ref=IlcdReference(
                        entity_type="processes",
                        entity_version="00.03.001",
                        entity_id="f256594a-a7bf-4bbb-91d0-65be256377c0",
                    ),
                ),
            ),
        ]
        cls = Soda4LcaZipReader
        for endpoint, expected_zip_url in test_cases:
            result = cls.soda_endpoint_to_pointer(endpoint)
            self.assertEqual(result, expected_zip_url)
