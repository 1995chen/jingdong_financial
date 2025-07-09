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

from api_server.resources import APIDefaultRouter, APIV1Router
from celery_tasks.schedule_tasks.music_task import sync_play_list

v1_router = APIV1Router(
    name="music",
    tags=["music"],
)
logger = logging.getLogger(__name__)

__all__ = ["get_routers"]


def sync_playlist() -> Dict[str, Any]:
    """
    立即同步播放列表
    """
    sync_play_list.apply_async()
    return {"result": True, "state": "success"}


def get_routers() -> List[APIDefaultRouter]:
    """
    get routers
    bind url route to handler method
    :return: router list
    """
    v1_router.get("/sync/")(sync_playlist)
    return [
        v1_router,
    ]
