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
from urllib.parse import urlparse


def domain_from_url(url: str | None) -> str | None:
    """Try to extract the domain name (excluding `www` subdomain) from the given URL."""
    if url is None:
        return None
    if url.startswith("http"):
        try:
            netloc = urlparse(url).netloc
            if ":" in netloc:
                return netloc.split(":")[0]
            return netloc.removeprefix("www.")
        except ValueError:
            return None
    else:
        return url.removeprefix("www.")


def cleanup_website(website: str | None) -> str | None:
    """
    Try to perform cleanup of the given website address.

    If just domain name is given, add https:// and trailing slash. If there is a space, remove everything after it.
    """
    if website is None:
        return None
    # Trim whitespace and remove any part after the first space
    website = website.strip().partition(" ")[0]
    if not website.startswith("http"):
        return "https://" + website + "/"
    return website
