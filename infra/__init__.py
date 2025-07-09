# -*- coding: utf-8 -*-


"""
infra: infra module
"""

import logging

import inject

from infra.dependencies import instances_bind
from infra.handlers.logging import init_logger

init_logger()
logger = logging.getLogger(__name__)
# configure inject
inject.configure(instances_bind, bind_in_runtime=False)
logger.info("init_logger success")
