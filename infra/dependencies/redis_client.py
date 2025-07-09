# -*- coding: utf-8 -*-

"""
dependency: redis component
"""

import logging
from dataclasses import dataclass

from redis import Redis

__all__ = [
    "get_main_redis_by_config",
    "MainRedis",
    "Redis",
    "RedisConfig",
]

logger = logging.getLogger(__name__)


# do not check snake_case naming style
# pylint: disable=C0103,R0902
@dataclass
class RedisConfig:
    """
    redis config
    """

    PASSWORD: str = ""
    HOST: str = ""
    DATABASE: int = 0
    PORT: int = 6379
    decode_responses: bool = True


class MainRedis(Redis):  # type: ignore[misc] # pylint: disable=R0901,W0223
    """
    redis connect factory
    """


def get_main_redis_by_config(config: RedisConfig) -> MainRedis:
    """
    :param config: RedisConfig instance
    :return: MainRedis instance
    """
    instance: MainRedis = MainRedis(
        host=config.HOST,
        port=config.PORT,
        db=config.DATABASE,
        password=config.PASSWORD,
        **{
            "decode_responses": config.decode_responses,
        },
    )
    return instance
