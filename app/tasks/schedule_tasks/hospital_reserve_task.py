# -*- coding: utf-8 -*-


import inject
import template_logging
from celery import Celery

from app.services.hospital import reserve_notify

logger = template_logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)


@celery_app.task(ignore_result=True, time_limit=600)
def reserve_notify_task():
    """
    预约挂号提醒
    """
    logger.info(f"start run reserve_notify_task....")
    reserve_notify()
    logger.info(f"run reserve_notify_task done")
