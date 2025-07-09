# -*- coding: utf-8 -*-

"""
exceptions: base exceptions module
"""

from infra.constant import CODE_MAP
from infra.enums import StatusCode

__all__ = [
    "AppException",
    "WebAppException",
    "BloomFilterException",
]


class RootException(Exception):
    """
    base exception for this project
    """

    def __init__(self, code: StatusCode, msg: str = "") -> None:
        super().__init__()
        self.code = code
        self.msg = msg or CODE_MAP[code]

    def errors(self) -> str:
        """
        return error msg
        """
        return self.msg


class AppException(RootException):
    """
    base exception for app
    """

    def __init__(
        self, code: StatusCode = StatusCode.APP_ERROR, msg: str = CODE_MAP[StatusCode.APP_ERROR]
    ) -> None:
        super().__init__(code, msg)


class WebAppException(AppException):
    """
    base exception for web api
    """

    def __init__(
        self,
        code: StatusCode = StatusCode.WEB_APP_ERROR,
        msg: str = CODE_MAP[StatusCode.WEB_APP_ERROR],
    ) -> None:
        super().__init__(code, msg)


class BloomFilterException(AppException):
    """
    bloom filter exception
    """

    def __init__(
        self,
        code: StatusCode = StatusCode.APP_BLOOM_FILTER_ERROR,
        msg: str = CODE_MAP[StatusCode.APP_BLOOM_FILTER_ERROR],
    ) -> None:
        super().__init__(code, msg)
