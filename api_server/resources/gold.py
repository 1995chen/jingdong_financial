# -*- coding: utf-8 -*-


"""
This is a demo of API multi-versioning
Here, for example, if an API is bound to the /v1 and
/v2 prefixes, the following two APIs will be generated:
    /v1/hello
    /v2/hello
"""


import logging
from typing import List

from api_server.resources import APIDefaultRouter, APIV1Router
from infra.services.gold import get_current_price, get_latest_price

v1_router = APIV1Router(
    name="gold_price",
    tags=["gold_price"],
)
logger = logging.getLogger(__name__)

__all__ = ["get_routers"]


def get_routers() -> List[APIDefaultRouter]:
    """
    get routers
    bind url route to handler method
    :return: router list
    """
    v1_router.get("/list/")(get_latest_price)
    v1_router.get("/latest/")(get_current_price)
    return [
        v1_router,
    ]
