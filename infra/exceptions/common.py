# -*- coding: utf-8 -*-

"""
exceptions: common exceptions module
"""

from infra.constant import CODE_MAP
from infra.enums import StatusCode
from infra.exceptions.base import AppException, BloomFilterException

__all__ = [
    "ConfigLoadException",
    "InvalidTypeException",
    "NotFoundException",
    "HandlerNotCallableException",
    "NotImplementedException",
    "BloomFilterException",
]


class ConfigLoadException(AppException):
    """
    failed to load config
    """

    def __init__(self, msg: str = CODE_MAP[StatusCode.APP_CONFIG_LOAD_ERROR]) -> None:
        super().__init__(StatusCode.APP_CONFIG_LOAD_ERROR, msg)


class InvalidTypeException(AppException):
    """
    invalid type exception
    """

    def __init__(self, msg: str = CODE_MAP[StatusCode.APP_INVALID_TYPE]) -> None:
        super().__init__(StatusCode.APP_INVALID_TYPE, msg)


class NotFoundException(AppException):
    """
    not found exception
    """

    def __init__(self, msg: str = CODE_MAP[StatusCode.APP_NOT_FOUND]) -> None:
        super().__init__(StatusCode.APP_NOT_FOUND, msg)


class HandlerNotCallableException(AppException):
    """
    handler not callable exception
    """

    def __init__(self, msg: str = CODE_MAP[StatusCode.APP_HANDLER_NOT_CALLABLE]) -> None:
        super().__init__(StatusCode.APP_HANDLER_NOT_CALLABLE, msg)


class NotImplementedException(AppException):
    """
    not implemented exception
    """

    def __init__(self, msg: str = CODE_MAP[StatusCode.APP_NOT_IMPLEMENTED]) -> None:
        super().__init__(StatusCode.APP_NOT_IMPLEMENTED, msg)
