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
import abc
from typing import Any, Generic, TypeVar

from openepd.model.declaration import BaseDeclaration
from openepd.model.epd import EpdWithDeps
from openepd.model.generic_estimate import GenericEstimateWithDeps
from openepd.model.geography import Geography

from ilcdlib.extension import IlcdEpdExtension

TSource = TypeVar("TSource", bound=BaseDeclaration)
TTarget = TypeVar("TTarget", bound=BaseDeclaration)


class BaseDeclarationConvertor(Generic[TSource, TTarget], metaclass=abc.ABCMeta):
    """Base class for declaration convertors."""

    def _remove_property(self, property_name: str, raw_object: dict[str, Any]) -> bool:
        if property_name in raw_object:
            del raw_object[property_name]
            return True
        return False

    def _rename_property(self, old_name: str, new_name: str, raw_object: dict[str, Any]) -> bool:
        if old_name in raw_object:
            raw_object[new_name] = raw_object[old_name]
            del raw_object[old_name]
            return True
        return False

    def _obj_to_raw(self, obj: TSource) -> dict[str, Any]:
        return obj.to_serializable(exclude_unset=True, exclude_defaults=True, by_alias=True)

    def _normalize_ilcd_geography(self, ilcd_geography: str) -> list[Geography] | None:
        """Convert ILCD geography string into openEPD geography."""
        if ilcd_geography in list(Geography):
            return [Geography(ilcd_geography)]
        if ilcd_geography == "RER":
            return [Geography.m49_150]  # 150 -Europe
        return None

    @abc.abstractmethod
    def convert(self, source: TSource) -> TTarget:
        """Convert the source object into the target object."""
        raise NotImplementedError()


class EpdToGenericEstimateConvertor(BaseDeclarationConvertor[EpdWithDeps, GenericEstimateWithDeps]):
    """Convertor from EPD to GenericEstimate."""

    def convert(self, source: EpdWithDeps) -> GenericEstimateWithDeps:
        """Convert EPD to GenericEstimate."""
        raw_obj = self._obj_to_raw(source)
        self._remove_property("doctype", raw_obj)
        self._rename_property("product_description", "description", raw_obj)
        self._rename_property("product_name", "name", raw_obj)
        self._rename_property("third_party_verifier", "reviewer", raw_obj)
        self._rename_property("third_party_verifier_email", "reviewer_email", raw_obj)
        # Set geography
        ilcd_geography = source.get_ext_or_empty(IlcdEpdExtension).production_location
        if ilcd_geography:
            openepd_geography = self._normalize_ilcd_geography(ilcd_geography)
            if openepd_geography:
                raw_obj["geography"] = openepd_geography
        # Publisher
        publishers = source.get_ext_or_empty(IlcdEpdExtension).epd_publishers or []
        if len(publishers) > 0:
            raw_obj["publisher"] = publishers[0].to_serializable(exclude_unset=True, exclude_defaults=True)
            self._remove_property("manufacturer", raw_obj)
        else:
            self._rename_property("manufacturer", "publisher", raw_obj)
        return GenericEstimateWithDeps(**raw_obj)
