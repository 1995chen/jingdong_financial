# -*- coding: utf-8 -*-


"""
manager all 3rd part dependency
"""

import logging

from inject import Binder, autoparams
from work_wechat import WorkWeChat

from infra.dependencies.auth import Auth, AuthStore, RequestStore, get_auth_by_config
from infra.dependencies.celery import Celery, get_celery_by_config
from infra.dependencies.config import (
    ClashConfig,
    ClashSubscribeIetm,
    Config,
    HospitalReserveConfig,
    YouTubeSubscribeConfig,
    bind_config,
)
from infra.dependencies.migration import Migration, get_migration_instance
from infra.dependencies.rdb import MainRDB, get_main_rdb_by_config
from infra.dependencies.redis_client import MainRedis, Redis, get_main_redis_by_config
from infra.dependencies.registry import Registry, bind_registry
from infra.enums import RuntimeEnv

__all__ = (
    "instances_bind",
    "Config",
    "ClashSubscribeIetm",
    "ClashConfig",
    "HospitalReserveConfig",
    "YouTubeSubscribeConfig",
    "Celery",
    "MainRDB",
    "MainRedis",
    "Redis",
    "Auth",
    "RequestStore",
    "AuthStore",
    "Registry",
    "Migration",
)

logger = logging.getLogger(__name__)


@autoparams()
def bind_celery(_config: Config) -> Celery:
    """
    :return: Celery instance
    """
    return get_celery_by_config(_config.PROJECT_NAME, _config.CELERY_CONFIG, _config.ENV)


@autoparams()
def bind_main_rdb(_config: Config) -> MainRDB:
    """
    :return: RdbConnectionFactory instance
    """
    return get_main_rdb_by_config(_config.MYSQL_DATASOURCE_CONFIG)


@autoparams()
def bind_main_redis(_config: Config) -> MainRedis:
    """
    :return: MainRedis instance
    """
    return get_main_redis_by_config(_config.REDIS_DATASOURCE_CONFIG)


@autoparams()
def bind_migration(_config: Config, _main_rdb: MainRDB) -> Migration:
    """
    :return: Migration instance
    """
    return get_migration_instance(_main_rdb, _config.PROJECT_NAME, _config.PROJECT_PATH)


@autoparams()
def bind_auth(_config: Config) -> Auth:
    """
    :return: Auth instance
    """
    return get_auth_by_config(_config.AUTH_CONFIG, auth_role=_config.ENV != RuntimeEnv.DEVELOPMENT)


@autoparams()
def init_work_wechat(_config: Config) -> WorkWeChat:
    """
    :return: WorkWeChat instance
    """
    return WorkWeChat(
        corpid=_config.WECHAT_WORK_CONFIG.CORP_ID, corpsecret=_config.WECHAT_WORK_CONFIG.CORP_SECRET
    )


def instances_bind(binder: Binder) -> None:
    """
    inject bind function
    :param binder:
    """
    logger.info("start bind dependencies...")
    binder.bind_to_constructor(Config, bind_config)
    binder.bind_to_constructor(Celery, bind_celery)
    binder.bind_to_constructor(MainRDB, bind_main_rdb)
    binder.bind_to_constructor(MainRedis, bind_main_redis)
    binder.bind_to_constructor(Migration, bind_migration)
    binder.bind_to_constructor(Auth, bind_auth)
    binder.bind_to_constructor(Registry, bind_registry)
    binder.bind_to_constructor(WorkWeChat, init_work_wechat)
    logger.info("bind dependencies done!")
