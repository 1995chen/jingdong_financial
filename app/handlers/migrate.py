# -*- coding: utf-8 -*-


import template_logging

logger = template_logging.getLogger(__name__)


def init_data_handler(*args, **kwargs) -> None:
    """
    初始化数据handler
    """
    logger.info("do init_data_handler done")
