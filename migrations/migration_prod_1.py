# -*- coding: UTF-8 -*-

"""
migration script
"""

import logging
import os

import inject

from infra.dependencies import MainRDB

logger = logging.getLogger(__name__)


def init_migrate() -> None:
    """
    具体要进行的操作
    该脚本是一个初始化migrate
    """
    with inject.instance(MainRDB).get_session() as session:
        session.commit()
    logger.info("print_test success")


def do() -> None:
    """
    必须实现的do方法
    """
    logger.info(f"do migration by {os.path.basename(__file__)}")
    init_migrate()
