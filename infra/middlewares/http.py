# -*- coding: utf-8 -*-


"""
middlewares: http middlewares module
"""

import logging
import time
from typing import Callable

import inject
from fastapi import Request, Response
from fastapi.responses import ORJSONResponse
from starlette.types import Message

from infra.dependencies import Auth, Config, RequestStore
from infra.enums import StatusCode
from infra.utils import make_json_response

__all__ = [
    "user_define_http_middleware",
]

logger = logging.getLogger(__name__)
config: Config = inject.instance(Config)


async def _set_body(request: Request, body: bytes) -> None:
    """
    set body
    for fix: https://github.com/tiangolo/fastapi/issues/394
    :param request: request
    :param body: body bytes
    :return: body bytes
    """

    async def receive() -> Message:
        return {"type": "http.request", "body": body}

    # pylint: disable=W0212
    request._receive = receive


async def _get_body(request: Request) -> bytes:
    """
    get body
    for fix: https://github.com/tiangolo/fastapi/issues/394
    :param request: request
    :return: body bytes
    """
    body: bytes = await request.body()
    await _set_body(request, body)
    return body


async def user_define_http_middleware(request: Request, call_next: Callable) -> Response:
    """
    User-defined middleware
    :param request: request object
    :param call_next: next middleware
    :return: Response instance
    """
    # get user ip
    headers_list = request.headers.getlist("X-Forwarded-For")
    client_ip: str = headers_list[0] if headers_list else request.client.host
    auth: Auth = inject.instance(Auth)
    body: bytes = await _get_body(request)
    request_store: RequestStore = RequestStore()
    request_store.client_ip = client_ip
    request_store.base_url = str(request.base_url)
    request_store.url = str(request.url)
    request_store.method = request.method
    request_store.header = str(request.headers)
    request_store.body = body
    request_store.path_params = request.path_params
    request_store.query_params = dict(request.query_params)
    auth.set_request(request_store)
    logger.debug(f"user_define_http_middleware: get request, content is {request_store}")
    # Record request start time
    start_time: float = time.time()
    # noinspection PyBroadException
    try:
        response = await call_next(request)
    # pylint: disable=W0703
    except Exception:
        response = ORJSONResponse(
            status_code=500,
            content=make_json_response(
                code=StatusCode.UNEXPECTED_ERROR,
            ),
        )
        logger.error("unexpected error", exc_info=True)
    finally:
        auth.clear()

    process_time: float = time.time() - start_time
    if process_time > config.SLOW_API_LIMIT_TIME:
        logger.warning(
            f"slow api found, process_time {int(process_time)}s: {request.method} {request.url}"
        )
    return response
