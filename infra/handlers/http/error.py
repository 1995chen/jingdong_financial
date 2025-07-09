# -*- coding: utf-8 -*-

"""
handlers: web api global exception error handler
"""

import logging
from typing import Any, Dict, List, Optional

import inject
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse

from infra.dependencies import Auth, RequestStore
from infra.enums import StatusCode
from infra.exceptions import (
    AppException,
    AuthenticationFailed,
    HTTPException,
    PermissionDenied,
    WebAppException,
)
from infra.utils import make_json_response

__all__ = ["bind_app_exception_handler"]

logger = logging.getLogger(__name__)


# pylint: disable=W9019
async def record_request_log(_request: Optional[Request]) -> None:
    """
    :param _request: request object
    record request log
    """
    auth: Auth = inject.instance(Auth)
    request_store: RequestStore = auth.get_request() or RequestStore()
    logger.warning(
        f"request_url: {request_store.url}, method: {request_store.method}, "
        f"header: {request_store.header}, "
        f"args: {dict(request_store.query_params)}, "
        f"body: {request_store.body}",  # type: ignore[str-bytes-safe]
        exc_info=True,
    )


async def handler_pydantic_error(
    request: Optional[Request], exception: RequestValidationError
) -> ORJSONResponse:
    """
    deal with pydantic error
    :param request: request object
    :param exception: exception object
    :return: ORJSONResponse fastapi response
    """
    # record request log
    await record_request_log(request)
    # formate error
    errors: List[Dict] = exception.errors()
    msg: List[Dict[str, Any]] = []
    for _e in errors:
        msg.append(
            {
                "location": _e["loc"][0],
                "params": _e["loc"][1:],
                "detail": _e["msg"],
            }
        )

    return ORJSONResponse(
        status_code=400,
        content=make_json_response(StatusCode.APP_PYDANTIC_ERROR, None, msg),
    )


async def handler_http_error(
    request: Optional[Request], exception: HTTPException
) -> ORJSONResponse:
    """
    deal with http error
    :param request: request object
    :param exception: exception object
    :return: ORJSONResponse fastapi response
    """
    # record request log
    await record_request_log(request)
    return ORJSONResponse(
        status_code=exception.status_code,
        content=make_json_response(StatusCode.WEB_APP_ERROR, None, exception.detail),
    )


async def handler_web_app_exception_error(
    request: Optional[Request], exception: WebAppException
) -> ORJSONResponse:
    """
    handler web app based exception
    :param request: request object
    :param exception: exception object
    :return: ORJSONResponse fastapi response
    """
    # record request log
    await record_request_log(request)
    # deal with authentication exception
    if isinstance(exception, AuthenticationFailed):
        return ORJSONResponse(
            status_code=401,
            content=make_json_response(
                StatusCode.WEB_APP_AUTHENTICATION_FAILED, None, exception.errors()
            ),
        )
    # deal with permission denied
    if isinstance(exception, PermissionDenied):
        return ORJSONResponse(
            status_code=401,
            content=make_json_response(
                StatusCode.WEB_APP_PERMISSION_DENIED, None, exception.errors()
            ),
        )
    return ORJSONResponse(
        status_code=400,
        content=make_json_response(StatusCode.WEB_APP_ERROR, None, exception.errors()),
    )


async def handler_app_exception_error(
    request: Optional[Request], exception: AppException
) -> ORJSONResponse:
    """
    handler web app based exception
    :param request: request object
    :param exception: exception object
    :return: ORJSONResponse fastapi response
    """
    # record request log
    await record_request_log(request)

    return ORJSONResponse(
        status_code=400,
        content=make_json_response(exception.code, None, exception.errors()),
    )


def bind_app_exception_handler(application: FastAPI) -> None:
    """
    bind exception handler to fastapi app
    :param application: the instance of FastAPI
    """
    # bind pydantic error
    application.add_exception_handler(RequestValidationError, handler_pydantic_error)
    # handler WebAppException
    application.add_exception_handler(WebAppException, handler_web_app_exception_error)
    # handler AppException
    application.add_exception_handler(AppException, handler_app_exception_error)
    # bind http error
    application.add_exception_handler(HTTPException, handler_http_error)
