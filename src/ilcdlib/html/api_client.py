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
#  This software was developed with support from the Skanska USA,
#  Charles Pankow Foundation, Microsoft Sustainability Fund, Interface, MKA Foundation, and others.
#  Find out more at www.BuildingTransparency.org
#
from typing import Any

from bs4 import BeautifulSoup

from ilcdlib.http_common import BaseApiClient


class HTMLPageClient(BaseApiClient):
    """API client for fetching and parsing HTML pages."""

    def __init__(self, base_url: str, **kwargs: Any) -> None:
        """
        Initialize a new HTML page client.

        :param base_url: Base API endpoint should be something like https://your-host.tld/resource
        :param kwargs: all kwargs supported by BaseApiClient
        """
        base_url = base_url.rstrip("/")
        super().__init__(base_url, **kwargs)

    def parse_html_page(self) -> BeautifulSoup:
        """
        Fetch the HTML page and parse it using BeautifulSoup.

        :return: BeautifulSoup object
        """
        response = self._do_request("get", self.base_url, stream=True)
        if not response.text:
            raise ValueError("No content found in the response")

        return BeautifulSoup(response.text, "html.parser")

    def fetch_first_matching_href(self, p_filter_substring: str | None = None) -> str | None:
        """
        Fetch the href attribute of the first hyperlink that matches the optional p filter.

        :param p_filter_substring: p substring to filter the hyperlinks
        :return: the href attribute of the first matching link, or None if no matching link is found
        """
        html_page = self.parse_html_page()
        p_tag = (
            html_page.find("p", string=lambda text: p_filter_substring in text if text else False)
            if p_filter_substring
            else html_page.find("p")
        )
        if not p_tag:
            return None

        parent_div = p_tag.find_parent("div")
        if parent_div:
            link_element = parent_div.find_parent("a")
            if link_element and (href := link_element.get("href")):
                return href[0] if isinstance(href, list) else href
        return None
