# -*- coding: utf-8 -*-

"""
hospital reserve task
"""

import logging

import inject
from celery import Celery

from infra.dependencies import Config
from infra.services.hospital import reserve_notify

logger = logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)


@celery_app.task(ignore_result=True, time_limit=600)
def reserve_notify_task() -> None:
    """
    预约挂号提醒
    """
    logger.info("start run reserve_notify_task....")
    config: Config = inject.instance(Config)
    for r in config.HOSPITAL_RESERVE:
        reserve_notify(r)
    logger.info("run reserve_notify_task done")
