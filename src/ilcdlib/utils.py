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
from dataclasses import dataclass
import datetime
import logging
import re
from typing import TYPE_CHECKING, Any, Final, Iterable, Optional, Self, TypeVar
import uuid

from openepd.model.common import Amount
import pytz

from ilcdlib import const
from ilcdlib.sanitizing.domain import domain_from_url

PATTERN_WHITESPACE_SEQUENCE: Final[re.Pattern] = re.compile(r"\s+")
LOGGER = logging.getLogger(__name__)

T = TypeVar("T")

if TYPE_CHECKING:
    from ilcdlib.dto import IlcdReference


def none_throws(optional: T | None, message: str = "Unexpected `None`") -> T:
    """Convert an optional to its value. Raises an `AssertionError` if the value is `None`."""
    if optional is None:
        raise AssertionError(message)
    return optional


def no_trailing_slash(val: str) -> str:
    """Remove all trailing slashes from the given string. Might be useful to normalize URLs."""
    while val.endswith("/"):
        val = val[:-1]
    return val


def create_openepd_attachments(
    reference: Optional["IlcdReference"], base_url: str | None = None
) -> dict[str, str] | None:
    """Create a dictionary of OpenEPD attachments."""
    if reference is None:
        return None
    return {x: reference.to_url(base_url) for x in const.ILCD_IDENTIFICATION}


def provider_domain_name_from_url(url: str | None) -> str:
    """Return provider identifier from the given URL. If the URL is `None`, return the default value."""
    if url:
        return none_throws(domain_from_url(url))
    return const.ILCD_IDENTIFICATION[0]


def create_ext(data: Any) -> dict[str, Any] | None:
    """Create a dictionary of OpenEPD ext field."""
    if data is None:
        return None
    return {x: data for x in const.ILCD_IDENTIFICATION}


def date_to_datetime(date: datetime.date | None, timezone: str = "UTC") -> datetime.datetime | None:
    """Convert a date to a datetime object with the given timezone."""
    if date is None:
        return None
    return datetime.datetime(year=date.year, month=date.month, day=date.day, tzinfo=pytz.timezone(timezone))


def csv_header_to_idx(col_name: str, header: list[str], raise_when_not_found=True) -> int | None:
    """
    Return index of the column in CSV line by given column name (as specified in header line).

    :param col_name: name as per csv header line
    :param header: header line (list of strings)
    :param raise_when_not_found: whether to raise `ValueError` in case when column doesn't exist in header.
    :return: index of the given column or None if it doesn't exist and `raise_when_not_found` == False
    """
    col_name_normalized = col_name.lower()
    for idx, x in enumerate(header):
        if x.strip().lower() == col_name_normalized:
            return idx
    if raise_when_not_found:
        raise ValueError(f"Column {col_name} is not found")
    return None


def normalize_whitespace(row: Iterable[Any]) -> list[Any]:
    """
    Replace multiple spaces with single space in each string object from input data.

    If object is not string - nothing changed. Does not change original data, return new object.
    :param row: row to normalize
    :return: list with same order as input data that contains same as original non-string objects and changed
    string objects
    """
    result_row = []
    for cell_value in row:
        if isinstance(cell_value, str):
            cell_value = PATTERN_WHITESPACE_SEQUENCE.sub(" ", cell_value)
        result_row.append(cell_value)
    return result_row


def parse_float_from_string(value: str, _locale: str | None = None) -> float | None:
    """
    Parse a float from a string. If the string cannot be parsed, return None.

    This function should handle a various representations of floats, including scientific notations.
    """
    if value is None:
        return value
    value = value.strip().replace("\n", " ").replace(" ", "")
    import locale

    original_locale = locale.getlocale(locale.LC_NUMERIC)
    if _locale is None:
        locale_settings = "en_US"
    else:
        locale_settings = _locale
    try:
        try:
            locale.setlocale(locale.LC_NUMERIC, locale_settings)
        except locale.Error as e:
            LOGGER.warning("Unknown number locale: %s. Original error: %s", locale_settings, e)
        try:
            return locale.atof(value)
        except ValueError:
            return None
    finally:
        locale.setlocale(locale.LC_NUMERIC, original_locale)


class MarkdownSectionBuilder:
    """
    A builder for Markdown sections.

    Allows to build a Markdown string from a list of sections (title + content).
    """

    @dataclass(kw_only=True)
    class _MdSection:
        title: str
        level: int = 1
        content: str | None = None

    def __init__(self) -> None:
        self._sections: list[MarkdownSectionBuilder._MdSection] = []

    def add_section(self, title: str, content: str | None = None, level: int = 1) -> Self:
        """Add a new section to the builder."""
        self._sections.append(MarkdownSectionBuilder._MdSection(title=title, content=content, level=level))
        return self

    @staticmethod
    def _build_section(section: _MdSection) -> str:
        return f"{'#' * section.level} {section.title}\n\n{section.content or ''}"

    def build(self) -> str:
        """Build the Markdown string."""
        return "\n\n".join([self._build_section(x) for x in self._sections if x.content is not None])


def is_valid_uuid(value: str) -> bool:
    """Check if the given string is a valid UUID."""

    try:
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj) == value.strip().lower()
    except ValueError:
        return False


_amount_pattern = re.compile(r"^\s*(\d*\.?\d+)\s*([a-zA-Z]+)\s*$")
"""Regular expression pattern to match the numeric value and unit."""


def parse_unit_str(value: str) -> Amount:
    """Parse a string with a numeric value and a unit."""
    match = _amount_pattern.match(value)

    if not match:
        raise ValueError(f"Invalid unit string: {value}")

    numeric_value = float(match.group(1))
    unit = match.group(2)
    return Amount(qty=numeric_value, unit=unit)
