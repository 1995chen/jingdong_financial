# -*- coding: utf-8 -*-

"""
enums: status code
"""

from enum import Enum

__all__ = [
    "StatusCode",
]


class StatusCode(Enum):
    """
    global status code
    """

    # unexpected error
    UNEXPECTED_ERROR = -1
    # application error
    APP_ERROR = 5000
    # config load error
    APP_CONFIG_LOAD_ERROR = 5001
    # invalid type
    APP_INVALID_TYPE = 5002
    # not found
    APP_NOT_FOUND = 5003
    # pydantic valid error
    APP_PYDANTIC_ERROR = 5004
    # handler not callable
    APP_HANDLER_NOT_CALLABLE = 5005
    # not implemented
    APP_NOT_IMPLEMENTED = 5006
    # gRPC error
    APP_RPC_ERROR = 5007
    # bloom filter error
    APP_BLOOM_FILTER_ERROR = 5200

    # web application error
    WEB_APP_ERROR = 4000
    # web app bad request
    WEB_APP_BAD_REQUEST = 4001
    WEB_APP_AUTHENTICATION_FAILED = 4002
    WEB_APP_PERMISSION_DENIED = 4003
    WEB_APP_INVALID_TOKEN = 4004
    WEB_APP_AUTHORIZED_FAIL = 4005

    # success
    SUCCESS = 0
