# -*- coding: utf-8 -*-


import inject
import template_logging
from celery import Celery

from app.dependencies import Config
from app.services.music.youtube import YouTubeMusic

logger = template_logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)


@celery_app.task(ignore_result=True, time_limit=600)
def sync_play_list():
    """
    黄金价格上涨提醒
    """
    logger.info(f'start run sync_play_list....')
    # 获取配置
    config: Config = inject.instance(Config)
    YouTubeMusic().download_playlist(config.YOUTUBE_PLAY_LIST)
    logger.info(f'run sync_play_list done')
