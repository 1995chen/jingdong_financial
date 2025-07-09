# -*- coding: utf-8 -*-

"""
This is a demo of API multi-versioning
Here, for example, if an API is bound to the /v1 and
/v2 prefixes, the following two APIs will be generated:
    /v1/hello
    /v2/hello
"""

import logging
from typing import Any, Dict, List

from fastapi.responses import PlainTextResponse

from api_server.resources import APIDefaultRouter, APIV1Router, APIV2Router

__all__ = ["get_routers"]

v1_router = APIV1Router(
    name="demo",
    tags=["demo"],
)
v2_router = APIV2Router(
    name="demo",
    tags=["demo"],
)
logger = logging.getLogger(__name__)


def hello() -> PlainTextResponse:
    """
    A simple hello API
    """
    logger.info("test info log")
    try:
        raise ValueError("test")
    except ValueError:
        logger.warning("test warning exception log", exc_info=True)
    return PlainTextResponse(b"OK")


def pydantic_test(item_id: int) -> Dict[str, Any]:
    """
    do pydantic test
    """

    return {"item_id": item_id}


def get_routers() -> List[APIDefaultRouter]:
    """
    get routers
    bind url route to handler method
    :return: router list
    """
    v1_router.get("/hello/")(hello)
    v2_router.get("/hello/")(hello)
    v1_router.get("/test/pydantic/{item_id}")(pydantic_test)
    return [v1_router, v2_router]
