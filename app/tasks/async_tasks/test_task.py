# -*- coding: utf-8 -*-


import inject
import template_logging
from celery import Celery

from app.dependencies import Config

logger = template_logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)


@celery_app.task(ignore_result=True, time_limit=600)
def do_test():
    config: Config = inject.instance(Config)
    logger.info(f'run do_test done, config is {config}')
