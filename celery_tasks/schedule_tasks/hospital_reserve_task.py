# -*- coding: utf-8 -*-

"""
hospital reserve task
"""

import logging
from uuid import uuid4

import inject
from celery import Celery

from infra.dependencies import Config, Registry
from infra.services.hospital import reserve_notify

logger = logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)


@celery_app.task(ignore_result=True, time_limit=600)
def reserve_notify_task() -> None:
    """
    预约挂号提醒
    """
    registry: Registry = inject.instance(Registry)
    registry.set_trace_id(str(uuid4()))
    logger.info("start run reserve_notify_task....")
    config: Config = inject.instance(Config)
    for r in config.HOSPITAL_RESERVE:
        reserve_notify(r)
    logger.info("run reserve_notify_task done")
