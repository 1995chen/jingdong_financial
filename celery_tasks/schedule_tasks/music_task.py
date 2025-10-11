# -*- coding: utf-8 -*-


"""
music task
"""

import logging
from uuid import uuid4

import inject
from celery import Celery

from infra.dependencies import Config, Registry
from infra.services.music.youtube import YouTubeMusic
from infra.utils.network import check_port

logger = logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)


@celery_app.task(ignore_result=True, time_limit=600)
def sync_play_list() -> None:
    """
    黄金价格上涨提醒
    """
    registry: Registry = inject.instance(Registry)
    registry.set_trace_id(str(uuid4()))
    logger.info("start run sync_play_list....")
    # 获取配置
    config: Config = inject.instance(Config)
    # 判断群晖是否开机
    if not check_port(config.SYNOLOGY_CONFIG.SYNOLOGY_HOST, config.SYNOLOGY_CONFIG.SYNOLOGY_PORT):
        logger.info("synology is shutdown, skip task.")
        return
    for subscribe_config in config.YOUTUBE_SUBSCRIBE_LIST:
        YouTubeMusic().download_playlist(subscribe_config)
    logger.info("run sync_play_list done")
