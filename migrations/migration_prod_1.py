# -*- coding: UTF-8 -*-


import os
import inject

import template_logging
from template_transaction import CommitContext

from app.dependencies import MainDBSession

logger = template_logging.getLogger(__name__)


def init_migrate():
    """
    具体要进行的操作
    该脚本是一个初始化migrate
    """
    session = inject.instance(MainDBSession)
    with CommitContext(session):
        pass
    logger.info("print_test success")


def do():
    """
    必须实现的do方法
    """
    logger.info(f"do migration by {os.path.basename(__file__)}")
    init_migrate()
