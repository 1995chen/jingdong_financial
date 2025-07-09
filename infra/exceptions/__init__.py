# -*- coding: utf-8 -*-


"""
exceptions: exceptions module
"""

from infra.exceptions.base import AppException, BloomFilterException, WebAppException
from infra.exceptions.common import (
    ConfigLoadException,
    HandlerNotCallableException,
    InvalidTypeException,
    NotFoundException,
    NotImplementedException,
)
from infra.exceptions.http import (
    AuthenticationFailed,
    AuthorizedFail,
    BadRequest,
    HTTPException,
    InvalidToken,
    PermissionDenied,
)

__all__ = [
    # http lib exception
    "HTTPException",
    # Custom exception
    "AppException",
    "WebAppException",
    "BloomFilterException",
    "ConfigLoadException",
    "InvalidTypeException",
    "NotFoundException",
    "NotImplementedException",
    "BadRequest",
    "AuthenticationFailed",
    "PermissionDenied",
    "InvalidToken",
    "AuthorizedFail",
    "HandlerNotCallableException",
]
