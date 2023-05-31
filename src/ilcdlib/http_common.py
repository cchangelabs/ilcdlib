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
from contextlib import contextmanager
import datetime
from io import BytesIO
import threading
from time import sleep
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from ilcdlib.utils import no_trailing_slash
from ilcdlib.xml_parser import T_ET, XmlParser


class Throttler:
    """Limit the number of calls to the code inside the context manager per second."""

    def __init__(self, rate_per_second: float) -> None:
        """
        Create new Throttler Instance.

        :param float rate_per_second: max number of calls to per second

        """
        super().__init__()

        self.rate: float = rate_per_second

        self.__count_lock = threading.Lock()
        self.__time_lock = threading.Lock()

        self.__count = 0
        self.__start = datetime.datetime.now()
        self.__time_limit = datetime.timedelta(seconds=1)

    @contextmanager
    def throttle(self):
        """Create context manager that limits the number of calls to the code inside the context per second."""
        with self.__count_lock:
            count = self.__count

        with self.__time_lock:
            diff = datetime.datetime.now() - self.__start
            if diff < self.__time_limit and count >= self.rate:
                seconds = (self.__time_limit - diff).total_seconds()
                sleep(seconds)
                self.__start = datetime.datetime.now()
                self.__count = count - self.rate

        with self.__count_lock:
            self.__count += 1

        yield


class BaseApiClient(metaclass=abc.ABCMeta):
    """Base class for API clients."""

    def __init__(
        self,
        base_url: str,
        *,
        xml_parser: XmlParser | None = None,
        user_agent: str | None = None,
        timeout: float | tuple[float, float] | None = None,
        retry_strategy: Retry | None = None,
        requests_per_sec: float = 10,
    ) -> None:
        """
        Create a new instance of the API client.

        :param base_url: common part that all request URLs start with
        :param user_agent: user agent to pass along with a request, if `None` then underlying library decides
                           which one to pass
        :param timeout: how long to wait for the server to send data before giving up,
                        as a float, or a (connect timeout, read timeout) tuple.
        """
        self._base_url = no_trailing_slash(base_url)
        self.user_agent = user_agent
        self.timeout: float | tuple[float, float] | None = timeout
        self._session: requests.Session | None = None
        self._throttler = Throttler(rate_per_second=requests_per_sec)
        self._retry_strategy = retry_strategy or self.create_default_retry_strategy()
        self.xml_parser = xml_parser or XmlParser()

    @classmethod
    def create_default_retry_strategy(cls) -> Retry:
        """
        Create default retry strategy.

        Note: when `backoff_factor` is set, the time between attempts will be exponentially increased according to
        the following formula: `{backoff_factor} * (2 ** ({number_retries} - 1))`. For the factor of 2 the periods
        will be like this: 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, ...
        :return:
        """
        return Retry(
            total=5,
            backoff_factor=2,
            respect_retry_after_header=True,
            status_forcelist=frozenset({413, 429, 500, 502, 503, 504}),
        )

    @property
    def base_url(self):
        """Base URL for all requests."""
        return self._base_url

    @property
    def default_headers(self) -> dict[str, str]:
        """Default headers for requests. Implement if required."""
        headers = {}
        if self.user_agent:
            headers["user-agent"] = self.user_agent
        return headers

    @property
    def _current_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.mount("", HTTPAdapter(max_retries=self._retry_strategy))
        return self._session

    def _on_before_do_request(self):
        """Run some custom logic before `do_request`. Can be overridden to check / refresh access tokens."""
        pass

    def download_by_url(self, url, method="get", **kwargs) -> BytesIO:
        """
        Perform query to the given endpoint and returns response body as bytes.

        The request will be performed in the context of API client, default error handling will be applied.

        :param url: url pointing the target endpoint
        :param method: optional HTTP method
        :param kwargs: any other arguments supported by _do_request. See `BaseApiClient._do_request`.
        :return: response content as bytes
        """
        r = self._do_request(method, url, **kwargs)
        content = r.content
        return BytesIO(content)

    def _get_url_for_request(self, path_or_url: str) -> str:
        """
        Generate url for given input.

        If absolute path is given it will be returned as is, otherwise the base url will be prepended.
        :param path_or_url: Either absolute url or base path.
        :return: absolute url
        """
        return self._base_url + path_or_url if not path_or_url.startswith("http") else path_or_url

    @staticmethod
    def _urlencode(value: str, safe="/") -> str:
        """
        Encode the given value using urllib.quote.

        :param value: value to encode
        :return: encoded value
        """
        return quote(value, safe=safe)

    def _do_request(
        self,
        method: str,
        endpoint: str,
        *,
        params=None,
        data=None,
        json=None,
        files=None,
        headers=None,
        session: requests.Session | None = None,
        raise_for_status: bool = True,
        **kwargs,
    ) -> requests.Response:
        headers = headers or self.default_headers

        self._on_before_do_request()

        url = self._get_url_for_request(endpoint)

        request_kwargs = dict(params=params, data=data, json=json, files=files, headers=headers, timeout=self.timeout)
        request_kwargs.update(kwargs)

        s = session or self._current_session

        with self._throttler.throttle():
            response = s.request(method, url, **request_kwargs)

        if response.ok:
            return response

        if response.ok or not raise_for_status:
            return response

        response.raise_for_status()
        raise RuntimeError("This line should never be reached")

    def _do_xml_request(self, method: str, endpoint: str, **kwargs) -> T_ET.Element:
        response = self._do_request(method, endpoint, **kwargs)
        return self.xml_parser.get_xml_tree(response.content)
