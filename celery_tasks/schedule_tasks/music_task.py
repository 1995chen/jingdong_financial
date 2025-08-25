# -*- coding: utf-8 -*-


"""
music task
"""

import logging
import socket

import inject
from celery import Celery

from infra.dependencies import Config
from infra.services.music.youtube import YouTubeMusic

logger = logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)


def check_port_open(ip: str, port: int, timeout: int = 3) -> bool:
    """
    check port is open
    :param ip: ip
    :param port: port
    :param timeout: connection timeout
    :return: is connection
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        s.close()
        return True
    except (socket.timeout, socket.error):
        return False


@celery_app.task(ignore_result=True, time_limit=600)
def sync_play_list() -> None:
    """
    黄金价格上涨提醒
    """
    logger.info("start run sync_play_list....")
    # 获取配置
    config: Config = inject.instance(Config)
    # 判断群晖是否开机
    if not check_port_open(
        config.SYNOLOGY_CONFIG.SYNOLOGY_HOST, config.SYNOLOGY_CONFIG.SYNOLOGY_PORT
    ):
        logger.info("synology is shutdown, skip task.")
        return
    for subscribe_config in config.YOUTUBE_SUBSCRIBE_LIST:
        YouTubeMusic().download_playlist(subscribe_config)
    logger.info("run sync_play_list done")
