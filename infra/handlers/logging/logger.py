# -*- coding: utf-8 -*-

"""
handlers: logger handler
"""

import configparser
import logging
from logging.config import fileConfig
from typing import Optional

import inject

from infra.dependencies.registry import Registry

__all__ = [
    "init_logger",
    "TraceIdFormatter",
]


class TraceIdFormatter(logging.Formatter):
    """
    subclass of logging.Formatter
    """

    def format(self, record: logging.LogRecord) -> str:
        # noinspection PyBroadException
        try:
            registry: Registry = inject.instance(Registry)
            # Add trace id to log messages
            record.trace_id = registry.get_trace_id() or ""
        # pylint: disable=W0703
        except Exception:
            record.trace_id = ""
        # Add tags to log messages
        record.tag = getattr(record, "tag", "default")
        # Remove all line breaks
        return super().format(record).replace("\n", " ")


def init_logger(log_config_file: Optional[str] = None) -> None:
    """
    load logger config
    :param log_config_file:
    """
    # pylint: disable=C0415
    from infra.dependencies import Config

    config_cp: configparser.ConfigParser = configparser.ConfigParser()

    if log_config_file:
        fileConfig(log_config_file, disable_existing_loggers=False)
        config_cp.read(log_config_file)
    else:
        fileConfig(Config.LOG_CONFIG_PATH, disable_existing_loggers=False)
        config_cp.read(Config.LOG_CONFIG_PATH)

    # Get loggers
    root_logger = logging.getLogger()
    loggers = [root_logger]
    for i in map(str.strip, config_cp["loggers"]["keys"].split(",")):
        if i == "root":
            continue
        loggers.append(logging.getLogger(i))

    for logger in loggers:
        logger.setLevel(Config.LOG_LEVEL)
