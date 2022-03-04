# -*- coding: utf-8 -*-


import inject
import template_logging
from celery import Celery

from app.dependencies import Config, bind

logger = template_logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)


@celery_app.task(ignore_result=True, time_limit=600)
def do_refresh_config():
    # 刷新配置
    inject.clear_and_configure(bind, bind_in_runtime=False)
    config: Config = inject.instance(Config)
    logger.info(f'run do_refresh_config done, config is {config}')
