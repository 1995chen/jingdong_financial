# -*- coding: utf-8 -*-

"""
exceptions: http exceptions module
"""

from starlette.exceptions import HTTPException

from infra.constant import CODE_MAP
from infra.enums import StatusCode
from infra.exceptions.base import WebAppException

__all__ = [
    "HTTPException",
    "BadRequest",
    "AuthenticationFailed",
    "PermissionDenied",
    "InvalidToken",
    "AuthorizedFail",
]


class BadRequest(WebAppException):
    """
    exception for 400
    """

    def __init__(
        self,
        msg: str = CODE_MAP[StatusCode.WEB_APP_BAD_REQUEST],
    ) -> None:
        super().__init__(StatusCode.WEB_APP_BAD_REQUEST, msg)


class AuthenticationFailed(WebAppException):
    """
    authentication failed exception for 401
    """

    def __init__(
        self,
        msg: str = CODE_MAP[StatusCode.WEB_APP_AUTHENTICATION_FAILED],
    ) -> None:
        super().__init__(StatusCode.WEB_APP_AUTHENTICATION_FAILED, msg)


class PermissionDenied(WebAppException):
    """
    permission denied exception for 401
    """

    def __init__(
        self,
        msg: str = CODE_MAP[StatusCode.WEB_APP_PERMISSION_DENIED],
    ) -> None:
        super().__init__(StatusCode.WEB_APP_PERMISSION_DENIED, msg)


class InvalidToken(WebAppException):
    """
    invalid token
    """

    def __init__(
        self,
        msg: str = CODE_MAP[StatusCode.WEB_APP_INVALID_TOKEN],
    ) -> None:
        super().__init__(StatusCode.WEB_APP_INVALID_TOKEN, msg)


class AuthorizedFail(WebAppException):
    """
    authorized failed
    """

    def __init__(
        self,
        msg: str = CODE_MAP[StatusCode.WEB_APP_AUTHORIZED_FAIL],
    ) -> None:
        super().__init__(StatusCode.WEB_APP_AUTHORIZED_FAIL, msg)
