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
import csv
import logging
from pathlib import Path
from typing import Any, Callable, Iterable, Self, cast

from ilcdlib.dto import Category, MappedCategory
from ilcdlib.mapping.common import BaseDataMapper, T
from ilcdlib.utils import csv_header_to_idx, parse_float_from_string

LOGGER = logging.getLogger(__name__)
DEFAULT_MAPPING_LOCATION = Path(__file__).parent.parent / "data" / "category_mapping"


class CategoryMapper(BaseDataMapper[str, list[MappedCategory]], metaclass=abc.ABCMeta):
    """A base class for category mapper."""

    IGNORE_CATEGORY = "IGNORE"


class NoopCategoryMapper(CategoryMapper):
    """A category mapper that does nothing."""

    def map(self, input_value: T, default_value: list[MappedCategory] | None) -> list[MappedCategory] | None:
        """Return the default value."""
        return default_value


class CsvCategoryMapper(CategoryMapper):
    """A category mapper that reads the mapping from a CSV file."""

    DEFAULT_PATH_DELIMITER = " -> "
    CATEGORY_MAPPING_FILE_FIELDS = [
        "External Full Name",
        "Level",
        "External ID",
        "Parent ID",
        "openEPD Category",
        "Material Properties",
        "Comment",
    ]

    def __init__(self, mapping: dict[str, list[MappedCategory]]) -> None:
        super().__init__()
        self._mapping = mapping

    @classmethod
    def from_file(cls, csv_path: Path | str) -> Self:
        """Create new instance from given CSV file."""
        file_path = Path(csv_path)
        if not file_path.is_absolute():
            file_path = DEFAULT_MAPPING_LOCATION / file_path
        mapping = cls._read_mapping_from_csv(file_path)
        return cls(mapping)

    @classmethod
    def from_list(
        cls, categories: Iterable[Category], key_fn: Callable[[MappedCategory], str], remove_duplicates: bool = False
    ) -> Self:
        """Create an instance from the list of categories."""
        mapping: dict[str, list[MappedCategory]] = {}
        for category in categories:
            mapped_category = cls.__to_mapped_category(category)
            key = key_fn(mapped_category)
            if key in mapping and not remove_duplicates:
                mapping[key].append(mapped_category)
            else:
                mapping[key] = [mapped_category]
        return cls(mapping)

    def map(self, input_value: str, default_value: list[MappedCategory] | None) -> list[MappedCategory] | None:
        """Map the input value to a list of MappedCategory objects."""
        result = self.__find_category_by_external_id(input_value)
        if not result:
            return default_value
        return result

    @classmethod
    def __to_mapped_category(cls, category: Category) -> MappedCategory:
        if isinstance(category, MappedCategory):
            return category
        return MappedCategory.parse_obj(category.dict())

    def __find_category_by_external_id(
        self, external_category_id: str, follow_hierarchy: bool = True
    ) -> list[MappedCategory]:
        mapped_categories = self._mapping.get(external_category_id) or []

        if len(mapped_categories) == 1:
            mapped_category: MappedCategory | None = mapped_categories[0]

            # Recursively check all parent nodes and append the closest associated category
            while True:
                if mapped_category is None:
                    return []
                if mapped_category.openepd_category_id or not follow_hierarchy:
                    return [mapped_category]
                parent_id = mapped_category.parent_id
                if parent_id:
                    categories = self._mapping.get(parent_id)
                    mapped_category = categories[0] if isinstance(categories, list) and len(categories) > 0 else None
                else:
                    return []
        else:
            return mapped_categories

    def export_to_csv(self, file_path: Path | str) -> None:
        """
        Export the mapping to a CSV file.

        :param file_path: The path to the file to save the mapping.
        """
        with open(file_path, "w") as f:
            writer = csv.writer(f, dialect="excel", quoting=csv.QUOTE_ALL)
            writer.writerow(self.CATEGORY_MAPPING_FILE_FIELDS)
            values: list[MappedCategory] = sum([val for k, val in self._mapping.items()], start=[])
            for x in sorted(values, key=lambda a: a.full_path):  # type: ignore
                writer.writerow(
                    [
                        x.name,
                        len(x.full_path) if x.full_path else 0,
                        x.id,
                        x.parent_id or "",
                        x.openepd_category_original or "",
                        x.openepd_material_specs_as_str(),
                        x.comment or "",
                    ]
                )

    @classmethod
    def preprocess_mapped_category(cls, mapped_category: MappedCategory, full_name: str) -> None:
        """
        Preprocess the mapped category before saving it to the mapping collection.

        This method might be overridden in a subclass to provide additional processing of the mapped category.
        """
        pass

    @classmethod
    def _read_mapping_from_csv(cls, file_path: Path) -> dict[str, list[MappedCategory]]:
        collection: dict[str, list[MappedCategory]] = {}
        with open(file_path) as f:
            reader = csv.reader(f, dialect="excel")
            header = next(reader)
            col_id = cast(int, csv_header_to_idx("External ID", header))
            col_ext_full_name = cast(int, csv_header_to_idx("External Full Name", header))
            col_parent_id = csv_header_to_idx("Parent ID", header, raise_when_not_found=False)
            col_comment = cast(int, csv_header_to_idx("Comment", header))
            col_category = cast(int, csv_header_to_idx("openEPD Category", header))
            col_material_properties: int | None = csv_header_to_idx(
                "Material Properties", header, raise_when_not_found=False
            )
            line_num = 1
            errors_counter = 0
            for x in reader:
                line_num += 1
                try:
                    external_id, full_name, comment, ec3_category = (
                        x[col_id].strip(),
                        x[col_ext_full_name].strip(),
                        x[col_comment].strip() or None,
                        x[col_category].strip() or None,
                    )
                    parent_id: str | None = None
                    material_properties = {}
                    if col_material_properties:
                        material_properties = cls._parse_material_properties_str(
                            x[col_material_properties].strip() or None
                        )
                    if col_parent_id:
                        parent_id = x[col_parent_id].strip() or None
                    obj_list = collection.get(external_id)

                    if obj_list is None:
                        collection[external_id], obj_list = [], []

                    for obj in obj_list:
                        if obj.openepd_category_original == ec3_category:
                            obj.comment = comment
                            obj.openepd_material_specs = material_properties
                            break
                    else:
                        mapped_item = MappedCategory(
                            id=external_id,
                            name=full_name,
                            parent_id=parent_id,
                            openepd_category_original=ec3_category,
                            openepd_material_specs=material_properties,
                            comment=comment,
                            full_path=full_name.split(cls.DEFAULT_PATH_DELIMITER),
                        )
                        cls.preprocess_mapped_category(mapped_item, full_name)
                        collection[external_id].append(mapped_item)

                except Exception as e:
                    LOGGER.warning(
                        "Invalid category mapping record at %s:%i. Reason: %s",
                        file_path,
                        line_num,
                        e,
                    )
                    errors_counter += 1
            if errors_counter > 0:
                raise ValueError(
                    f"Invalid data in category mapping file {file_path}. "
                    f"Found {errors_counter} errors. Details are above."
                )
        return collection

    @classmethod
    def _parse_material_properties_str(cls, properties_str: str | None) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if not properties_str:
            return result
        for prop_def in properties_str.split(","):
            prop_def = prop_def.strip()
            if "=" not in prop_def:
                raise ValueError('Invalid format. Expected format is prop_name = "value"')
            name, value_raw = prop_def.split("=")
            value_raw = value_raw.strip()
            name = name.strip()
            value: str | float | bool | None
            if len(value_raw) == 0:
                value = None
            elif (value_raw.startswith('"') and value_raw.endswith('"')) or (
                value_raw.startswith("'") and value_raw.endswith("'")
            ):
                value = value_raw[1:-1]
            elif value_raw[0].isnumeric():
                value = parse_float_from_string(value_raw)
            elif value_raw.upper() == "TRUE":
                value = "TRUE"
            elif value_raw.upper() == "FALSE":
                value = "FALSE"
            else:
                value = value_raw
            result[name] = value
        return result
