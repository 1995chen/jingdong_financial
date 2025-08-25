# -*- coding: utf-8 -*-


"""
utils: network utils
"""

import logging
import telnetlib  # pylint: disable=W4901
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

__all__ = [
    "check_port",
    "get_with_retry",
]


def check_port(ip: str, port: int, timeout: int = 3) -> bool:
    """
    check port is open
    :param ip: ip
    :param port: port
    :param timeout: connection timeout
    :return: is connection
    """
    try:
        tn = telnetlib.Telnet(ip, port, timeout)
        tn.close()
        return True
    except Exception:  # pylint: disable=W0718
        return False


def get_with_retry(  # pylint: disable=R0917
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    retry_times: int = 3,
    timeout: int = 30,
    no_retry_codes: Optional[List[int]] = None,
    verify: bool = False,
    **kwargs: Any,
) -> Tuple[bool, Optional[requests.Response]]:
    """
    send get request
    :param url: url
    :param params: params
    :param headers: headers
    :param retry_times: retry_times
    :param timeout: timeout
    :param no_retry_codes: no_retry_codes
    :param verify: verify
    :param kwargs: kwargs
    :return: response
    """
    retry_count: int = 0
    success: bool = False
    response: Optional[requests.Response] = None
    while retry_count <= retry_times:
        # noinspection PyBroadException
        try:
            # send request
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
                verify=verify,
                **kwargs,
            )
            if no_retry_codes and response.status_code in no_retry_codes:
                break
            response.raise_for_status()
            success = True
            break
        except Exception:  # pylint: disable=W0718
            logger.error(
                f"infra: failed to get, url is {url}, retry times({retry_count})",
                exc_info=True,
            )
            retry_count += 1
            time.sleep(retry_count)
    return success, response
