# -*- coding: utf-8 -*-


import re
import importlib
import json

import inject
import template_logging
from sqlalchemy import create_engine
from template_json_encoder import TemplateJSONEncoder

from app.models.base import Base
from app.dependencies import Config

json_encoder: TemplateJSONEncoder = inject.instance(TemplateJSONEncoder)
logger = template_logging.getLogger(__name__)


def name_convert_to_camel(name: str) -> str:
    """下划线转驼峰"""
    contents = re.findall('_[a-z]+', name)
    for content in set(contents):
        name = name.replace(content, content[1:].title())
    return name


def name_convert_to_snake(name: str) -> str:
    """驼峰转下划线"""
    if re.search(r'[^_][A-Z]', name):
        name = re.sub(r'([^_])([A-Z][a-z]+)', r'\1_\2', name)
        return name_convert_to_snake(name)
    return name.lower()


def generate_table() -> None:
    """
    创建表
    :return:
    """
    config: Config = inject.instance(Config)
    # 导入待新建的表
    importlib.import_module('app.models')
    Base.metadata.create_all(bind=create_engine(config.SQLALCHEMY_DATABASE_URI))
    logger.info("generate_table success")


def print_config():
    """
    打印配置
    """
    config: Config = inject.instance(Config)
    logger.info(f"app config is {json.dumps(config, default=json_encoder.default, indent=4)}")
