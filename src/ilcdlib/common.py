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
import abc
import datetime
from typing import IO, Literal, Self, Sequence, TextIO, overload

from openepd.model.epd import Epd
from openepd.model.lcia import ImpactSet
from openepd.model.org import Org
from openepd.model.pcr import Pcr

from ilcdlib.const import IlcdDatasetType
from ilcdlib.dto import IlcdReference
from ilcdlib.reference_data import get_ilcd_epd_reference_data_provider
from ilcdlib.type import LangDef, LocalizedStr
from ilcdlib.xml_parser import T_ET, XmlParser

XmlPath = str | tuple[str, ...] | list[str]


class BaseIlcdMediumSpecificReader(metaclass=abc.ABCMeta):
    """
    Base class for medium specific readers.

    This class is used to read ILCD data from a specific medium, e.g. a zip file, http api, etc.
    """

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

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    def entity_exists(self, entity_type: str, entity_id: str, entity_version: str | None = None) -> bool:
        """
        Check if the given entity exists.

        If you want to refer file by name only, you can use the entity_id and skip version parameter.

        :param entity_type: The type of the entity. e.g. "process", "contact", "flow", etc.
        :param entity_id: The id of the entity, typically a GUID.
        :param entity_version: The version of the entity e.g. 12.34.56
        """
        pass

    @abc.abstractmethod
    def close(self):
        """
        Close the reader and release any resources.

        This method is called automatically when used in a context manager.
        """
        pass

    @abc.abstractmethod
    def list_entities(self, entity_type: str) -> Sequence[IlcdReference]:
        """
        List all entities of the given type.

        :param entity_type: The type of the entity. e.g. "process", "contact", "flow", etc.
        """
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(self, _type, value, traceback):
        self.close()


class NoopBaseReader(BaseIlcdMediumSpecificReader):
    """A stub implementation of BaseIlcdMediumSpecificReader that does nothing."""

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
        """Generate exception. This class does not support get_entity_stream."""
        raise ValueError("NoopBaseReader does not support get_entity_stream")

    def entity_exists(self, entity_type: str, entity_id: str, entity_version: str | None = None) -> bool:
        """Return False regardless of parameters for this implementation."""
        return False

    def close(self):
        """Do nothing. This implementation does not need to be closed."""
        pass

    def list_entities(self, entity_type: str) -> Sequence[IlcdReference]:
        """Return empty list. NoopBaseReader does not support get_entity_stream."""
        return []


class IlcdXmlReader:
    """Base class for ILCD xml readers. It provides a set of helper methods to read ILCD data from ILCD xml."""

    _LANG_ATTRIB_NAME = "{http://www.w3.org/XML/1998/namespace}lang"

    def __init__(self, data_provider: BaseIlcdMediumSpecificReader):
        self.data_provider = data_provider
        self.reference_data_providers: dict[str, BaseIlcdMediumSpecificReader] = {
            "epd_ref_data": get_ilcd_epd_reference_data_provider()
        }
        self.xml_parser = XmlParser(
            ns_map=dict(
                xml="http://www.w3.org/XML/1998/namespace",
                common="http://lca.jrc.it/ILCD/Common",
                contact="http://lca.jrc.it/ILCD/Contact",
                flow="http://lca.jrc.it/ILCD/Flow",
                process="http://lca.jrc.it/ILCD/Process",
                source="http://lca.jrc.it/ILCD/Source",
                ug="http://lca.jrc.it/ILCD/UnitGroup",
                fp="http://lca.jrc.it/ILCD/FlowProperty",
                mm="http://www.matml.org/",
                epd2013="http://www.iai.kit.edu/EPD/2013",
                epd2019="http://www.iai.kit.edu/EPD/2019",
            )
        )

    def get_xml_tree(
        self, entity_type: str, entity_id: str, entity_version: str | None, *, allow_static_datasets: bool = True
    ) -> T_ET.Element:
        """
        Get the xml tree for the given entity.

        :param entity_type: The type of the entity. e.g. "process", "contact", "flow", etc.
        :param entity_id: The id of the entity, typically a GUID.
        :param entity_version: The version of the entity e.g. 12.34.56
        :param allow_static_datasets: whether to allow to check entity in static datasets if it doesn't
                                      exist in the given one.
        :raise: ValueError if the entity does not exist.
        """
        try:
            with self.data_provider.get_entity_stream(entity_type, entity_id, entity_version) as stream:
                return self.xml_parser.get_xml_tree(stream)
        except ValueError:
            if allow_static_datasets:
                for dataset_name, dataset_provider in self.reference_data_providers.items():
                    if dataset_provider.entity_exists(entity_type, entity_id, entity_version):
                        with dataset_provider.get_entity_stream(entity_type, entity_id, entity_version) as stream:
                            return self.xml_parser.get_xml_tree(stream)
        raise ValueError(f"Entity {entity_id} version {entity_version} (type: {entity_type}) does not exist.")

    def _preprocess_path(self, path: XmlPath) -> str:
        if not isinstance(path, str):
            str_path = "/".join(path)
        else:
            str_path = path
        return str_path

    def _get_el(
        self, root: T_ET.Element, path: XmlPath, default_value: T_ET.Element | None = None
    ) -> T_ET.Element | None:
        """Get the element matching the given xpath or `default_value` if no element is found."""
        xpath = self._preprocess_path(path)
        el = self.xml_parser.get_el(root, xpath)
        if el is None:
            return default_value
        return el

    def _get_all_els(self, root: T_ET.Element, path: XmlPath) -> list[T_ET.Element]:
        """Get all elements matching the given xpath."""
        xpath = self._preprocess_path(path)
        return self.xml_parser.get_all_els(root, xpath)

    def _get_text(self, root: T_ET.Element, path: XmlPath, default_value: str | None = None) -> str | None:
        """
        Get the element text.

        :param root: The element to get the text from.
        :return: The text or None if not found.
        """
        xpath = self._preprocess_path(path)
        return self.xml_parser.get_el_text(root, xpath, default_value)

    def _get_date(
        self, root: T_ET.Element, path: XmlPath, default_value: datetime.date | None = None
    ) -> datetime.date | None:
        """
        Get the element value as date.

        :param root: The element to get the text from.
        :return: The text or None if not found.
        """
        text = self._get_text(root, path, None)
        if text is not None:
            try:
                return datetime.date.fromisoformat(text)
            except ValueError:
                return default_value
        return default_value

    def _get_int(self, root: T_ET.Element, path: XmlPath, default_value: int | None = None) -> int | None:
        """Get the element value as integer."""
        text = self._get_text(root, path, None)
        if text is not None:
            try:
                return int(text)
            except ValueError:
                return default_value
        return default_value

    def _get_float(self, root: T_ET.Element, path: XmlPath, default_value: float | None = None) -> float | None:
        """Get the element value as float."""
        text = self._get_text(root, path, None)
        if text is not None:
            try:
                return float(text)
            except ValueError:
                return default_value
        return default_value

    def _get_localized_text(
        self, root: T_ET.Element, path: XmlPath, lang: LangDef, default_value: LocalizedStr | None = None
    ) -> LocalizedStr | None:
        """
        Get the element text for the given language.

        :param root: The element to get the text from.
        :param lang: The language to get the text for.
        :return: The localized text for the given language or None if not found.
        """
        if isinstance(lang, str) or lang is None:
            lang = [lang]
        for x in lang:
            xpath = self._preprocess_path(path)
            xpath += f"[@xml:lang='{x}']" if x is not None else "[1]"
            el = self.xml_parser.get_el(root, xpath)
            if el is not None:
                res = el.text
                if res and el.attrib and el.attrib.get(self._LANG_ATTRIB_NAME):
                    return LocalizedStr(res, el.attrib.get(self._LANG_ATTRIB_NAME))
                return LocalizedStr(res) if res else default_value
            else:
                continue
        return default_value

    def _get_reference(
        self, root: T_ET.Element, path: XmlPath, default_value: IlcdReference | None = None
    ) -> IlcdReference | None:
        xpath = f"{self._preprocess_path(path)}"
        el = self.xml_parser.get_el(root, xpath)
        if el is None or el.attrib is None:
            return default_value
        ref_id = el.attrib.get("refObjectId", None)
        ref_type = el.attrib.get("type", None)
        if ref_id is None or ref_type is None:
            return default_value
        try:
            ref_type = IlcdDatasetType(ref_type)
        except ValueError:
            pass
        return IlcdReference(ref_type, ref_id, entity_version=None)

    def _get_external_tree(self, root: T_ET.Element, path: XmlPath) -> T_ET.Element | None:
        ref = self._get_reference(root, path)
        if ref is None:
            return None
        return self.get_xml_tree(ref.entity_type, ref.entity_id, ref.entity_version, allow_static_datasets=True)

    def _get_external_binary(self, root: T_ET.Element, path: XmlPath) -> IO[bytes] | None:
        ref = self._get_reference(root, path)
        if ref is None:
            return None
        return self.data_provider.get_entity_stream(ref.entity_type, ref.entity_id, ref.entity_version, binary=True)


class OpenEpdContactSupportReader(metaclass=abc.ABCMeta):
    """Base class for adding OpenEPD export support."""

    @abc.abstractmethod
    def to_openepd_org(self, lang: LangDef, base_url: str | None = None) -> Org:
        """Read as openEPD Org object."""
        pass


class OpenEpdPcrSupportReader(metaclass=abc.ABCMeta):
    """Base class for adding openEPD export support."""

    @abc.abstractmethod
    def to_openepd_pcr(self, lang: LangDef, base_url: str | None = None) -> Pcr:
        """Read as openEPD Pcr object."""
        pass


class OpenEpdEdpSupportReader(metaclass=abc.ABCMeta):
    """Base class for adding openEPD export support to EPD documents."""

    @abc.abstractmethod
    def to_openepd_epd(self, lang: LangDef, base_url: str | None = None) -> Epd:
        """Read as OpenEPD EPD object."""
        pass


class OpenEpdImpactSetSupportReader(metaclass=abc.ABCMeta):
    """Base class for adding openEPD export support to LCIAResults."""

    @abc.abstractmethod
    def to_openepd_impact_set(self, lang: LangDef, base_url: str | None = None) -> ImpactSet:
        """Read as openEPD ImpactSet object."""
        pass
