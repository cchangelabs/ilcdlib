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
from os import PathLike
from typing import IO, Literal, Sequence, TextIO, overload
from zipfile import Path as ZipPath
from zipfile import ZipFile

from ilcdlib.common import BaseIlcdMediumSpecificReader
from ilcdlib.const import IlcdDatasetType
from ilcdlib.dto import IlcdReference


class ZipIlcdReader(BaseIlcdMediumSpecificReader):
    """
    Reader for ILCD objects packaged into zip archives.

    Typically, these objects represent export with all dependencies.
    """

    DATASET_TO_FOLDER: dict[IlcdDatasetType, str] = {
        IlcdDatasetType.Flows: "flows",
        IlcdDatasetType.Sources: "sources",
        IlcdDatasetType.UnitGroups: "unitgroups",
        IlcdDatasetType.Contacts: "contacts",
        IlcdDatasetType.Processes: "processes",
        IlcdDatasetType.FlowProperty: "flowproperties",
    }

    def __init__(self, zip_file: PathLike | IO[bytes]):
        try:
            self._zip_file = ZipFile(zip_file, "r")
        except Exception:
            raise ValueError("Could not open zip file. Please check if this is a valid zip file.")
        self.__ilcd_dir = ZipPath(self._zip_file) / "ILCD"
        if not self.__ilcd_dir.is_dir():
            raise ValueError("Could not find ILCD directory in the archive root. Is it really an ILCD archive?")

    @overload
    def get_entity_stream(
        self, entity_type: str, entity_id: str, entity_version: str | None = None, *, binary: Literal[True]
    ) -> IO[bytes]:
        ...

    @overload
    def get_entity_stream(
        self, entity_type: str, entity_id: str, entity_version: str | None = None, *, binary: Literal[False] = False
    ) -> TextIO:
        ...

    def get_entity_stream(
        self, entity_type: str, entity_id: str, entity_version: str | None = None, *, binary: bool = False
    ) -> IO[bytes] | TextIO:
        """
        Get xml stream for the given entity.

        If you want to refer file by name only, you can use the entity_id and skip version parameter.

        :param entity_type: The type of the entity. e.g. "process", "contact", "flow", etc.
        :param entity_id: The id of the entity, typically a GUID.
        :param entity_version: The version of the entity e.g. 12.34.56
        :param binary: If True, the stream is opened in binary mode, otherwise in text mode.
        :raise: ValueError if the entity does not exist.
        """
        full_path = self.__resolve_entity_path(entity_type, entity_id, entity_version)
        if full_path is None or not full_path.exists():
            raise ValueError(f"Could not find entity {entity_type} {entity_id} (version {entity_version}).")
        return full_path.open("rb" if binary else "r")  # type: ignore

    def get_binary_stream_by_name(self, name: str, entity_type: str | None = None) -> IO[bytes] | None:
        """
        Get binary stream for the given file name.

        :param name: The name of the file.
        :param entity_type: The type of the entity. e.g. "process", "contact", "flow", etc.
        """
        full_path = self.__ilcd_dir / "external_docs" / name
        if not full_path.exists():
            return None
        return full_path.open("rb")

    def entity_exists(self, entity_type: str, entity_id: str, entity_version: str | None = None) -> bool:
        """
        Check if the given entity exists.

        If you want to refer file by name only, you can use the entity_id and skip version parameter.

        :param entity_type: The type of the entity. e.g. "process", "contact", "flow", etc.
        :param entity_id: The id of the entity, typically a GUID.
        :param entity_version: The version of the entity e.g. 12.34.56
        """
        full_path = self.__get_file_path_for_entity(entity_type, entity_id, entity_version)
        return full_path.exists()

    def list_entities(self, entity_type: str) -> Sequence[IlcdReference]:
        """
        List all entities of the given type.

        :param entity_type: The type of the entity. e.g. "process", "contact", "flow", etc.
        """
        if isinstance(entity_type, IlcdDatasetType):
            entity_type_str = self.DATASET_TO_FOLDER.get(entity_type, str(entity_type))
        else:
            entity_type_str = entity_type
        type_dir = self.__ilcd_dir / entity_type_str
        if not type_dir.is_dir():
            return []
        return [
            IlcdReference(
                entity_type=entity_type,
                entity_id=x.name.split("_")[0],
                entity_version=x.name.split("_")[1].replace(".xml", ""),
            )
            for x in type_dir.iterdir()
            if x.is_file() and x.name.endswith(".xml")
        ]

    def __resolve_entity_path(
        self, entity_type: str, entity_id: str, entity_version: str | None = None
    ) -> ZipPath | None:
        if self.entity_exists(entity_type, entity_id, entity_version=entity_version):
            return self.__get_file_path_for_entity(entity_type, entity_id, entity_version)
        else:
            if isinstance(entity_type, IlcdDatasetType):
                entity_type_str = self.DATASET_TO_FOLDER.get(entity_type, str(entity_type))
            else:
                entity_type_str = entity_type
            type_dir = self.__ilcd_dir / entity_type_str
            if not type_dir.is_dir():
                return None
            for x in type_dir.iterdir():
                if x.is_file() and x.name.startswith(entity_id) and x.name.endswith(".xml"):
                    return self.__get_file_path_for_entity(entity_type, x.name)
        return None

    def __get_file_path_for_entity(
        self, entity_type: str, entity_id: str, entity_version: str | None = None
    ) -> ZipPath:
        if isinstance(entity_type, IlcdDatasetType):
            entity_type = self.DATASET_TO_FOLDER.get(entity_type, str(entity_type))
        if entity_version is None and "." in entity_id:
            file_name = entity_id
        elif entity_version is not None:
            file_name = f"{entity_id}_{entity_version}.xml"
        else:
            file_name = f"{entity_id}.xml"
        full_path = self.__ilcd_dir / entity_type / file_name
        return full_path

    def close(self):
        """
        Close the reader and release any resources.

        This method is called automatically when used in a context manager.
        """
        self._zip_file.close()

    def save_to(self, p: PathLike):
        """Save underling the zip file to the given path."""
        if self._zip_file.fp is None:
            raise ValueError("Cannot save closed zip file.")
        with open(p, "wb") as f:
            self._zip_file.fp.seek(0)
            f.write(self._zip_file.fp.read())
