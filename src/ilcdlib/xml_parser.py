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
from typing import IO
import xml.etree.ElementTree as T_ET

try:
    from lxml import etree as _lxml_ET
except ImportError:
    _lxml_ET = None  # type: ignore

ET = _lxml_ET if _lxml_ET is not None else T_ET


class XmlParser(object):
    """Entry point to Element tree interface + a few utility functions."""

    def __init__(self, ns_map: dict[str, str] | None = None):
        self.__xml_ns = ns_map or {}

    @property
    def xml_ns(self) -> dict[str, str]:
        """Get the XML namespace map."""
        return self.__xml_ns

    def get_xml_tree(self, file_stream_or_str: IO | str | bytes) -> T_ET.Element:
        """Get the XML tree from a file stream or string."""
        if isinstance(file_stream_or_str, (str, bytes)):
            return ET.fromstring(file_stream_or_str)
        else:
            return ET.parse(file_stream_or_str).getroot()

    def get_el_text(self, parent: T_ET.Element, xpath: str, default_val: str | None = None) -> str | None:
        """Get the text of an element."""
        el = parent.find(xpath, self.xml_ns)
        if el is None:
            return default_val
        return el.text

    def get_el(self, parent: T_ET.Element, xpath: str) -> T_ET.Element | None:
        """Get an xml element by xpath."""
        el = parent.find(xpath, self.xml_ns)
        if el is None:
            return None
        return el

    def get_all_els(self, parent: T_ET.Element, xpath: str) -> list[T_ET.Element]:
        """Get all xml elements by xpath."""
        el = parent.findall(xpath, self.xml_ns)
        return el
