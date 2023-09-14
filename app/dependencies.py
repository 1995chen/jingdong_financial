# -*- coding: utf-8 -*-


import json
import sys
import os
from typing import Dict, Any, List, Type
from dataclasses import dataclass, Field, field

import template_logging
from dacite import from_dict
from dacite.dataclasses import get_fields, T
from inject import autoparams
from redis import StrictRedis
from celery import Celery
from sqlalchemy.orm import scoped_session, Session
from template_cache import Cache
from template_babel.babel import TemplateBabel
from template_rbac import OAuth2SSO, Auth
from template_pagination import Pagination
from template_migration import Migration
from template_json_encoder import TemplateJSONEncoder
from template_apollo import ApolloClient
from work_wechat import WorkWeChat
from dynaconf import Dynaconf

from app.constants.enum import SysCMD

logger = template_logging.getLogger(__name__)


@dataclass
class ConfigItem:
    """
    所有子配置的基类
    """


@dataclass
class Config:
    PORT: int = os.getenv('PORT', 8080)
    CMD: SysCMD = field(default_factory=lambda: SysCMD[sys.argv[1].replace('-', '_').upper()])
    # 服务内部调用UUID
    INNER_CALL_UID: str = '6401e2c6-9b85-11ec-b3c0-1e00621ab048'
    # 项目名称
    PROJECT_NAME: str = 'jingdong_financial'
    # 项目路径
    PROJECT_PATH: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FRONTEND_PATH: str = os.path.join(PROJECT_PATH, 'static', 'release')
    API_PREFIX: str = '/api'
    # 中间件配置
    REDIS_URL: str = None
    SQLALCHEMY_DATABASE_URI: str = None
    CELERY_BROKER: str = None
    CELERY_BACKEND: str = None
    REDBEAT_REDIS_URL: str = None
    # celery beat 锁超时时间
    REDBEAT_LOCK_TIMEOUT: int = 600
    # 定时任务并发进程数
    BEAT_WORKER_NUM: int = 2
    # worker并发进程数
    WORKER_NUM: int = 2
    # 每个worker进程最大执行任务数
    MAX_TASKS_PER_CHILD: int = 20
    # OAuth2 SSO配置
    OAUTH2_CLIENT_ID: str = ''
    OAUTH2_CLIENT_SECRET: str = ''
    OAUTH2_AUTHORIZATION_ENDPOINT: str = ''
    OAUTH2_TOKEN_ENDPOINT: str = ''
    OAUTH2_USERINFO_ENDPOINT: str = ''
    # 应用后端地址
    APP_ROOT_URI: str = 'http://127.0.0.1:8000/'
    # 应用前端地址
    APP_FRONTEND_URI: str = 'http://127.0.0.1:3000/'
    APP_AUTH_PATH: str = '/api/login'
    APP_LOGOUT_PATH: str = '/api/logout'
    # jwt token 超时时间
    JWT_EXPIRE_TIME: int = 86400
    # jwt token secret key
    JWT_SECRET_KEY: str = ''
    RUNTIME_ENV: str = os.getenv('RUNTIME_ENV', 'DEV')
    # 是否是测试环境
    IS_DEV: bool = False if RUNTIME_ENV == 'PROD' else True
    # 阿波罗配置
    APOLLO_APP_ID: str = 'jingdong_financial'
    APOLLO_CONFIG_SERVER_URL: str = 'http://apollo.local.domain:13043'
    # 企业微信 CORP_ID
    CORP_ID: str = ''
    # 企业微信 CORP_SECRET
    CORP_SECRET: str = ''
    # 企业微信应用 AGENT_ID
    AGENT_ID: int = ''
    # 京东金融API配置
    JD_FINANCE_API_URL: str = "https://ms.jr.jd.com/gw/generic/hj/h5/m/latestPrice"
    # header信息
    JD_FINANCE_API_HEADERS: str = json.dumps(
        {
            "referer": "https://m.jdjygold.com/finance-gold/msjgold/homepage?orderSource=7",
            "host": "ms.jr.jd.com"
        }
    )
    # params信息
    JD_FINANCE_API_PARAMS: str = json.dumps({})
    # 样本数量[用于计算上涨下跌幅度]
    SAMPLE_COUNT: int = 20
    # 上涨幅度超过该值通知[金额]
    TARGET_RISE_PRICE: float = 2.0
    # 下跌幅度超过该值通知[金额]
    TARGET_FALL_PRICE: float = 2.0
    # 金价高于该值通知[具体价格]
    RISE_TO_TARGET_PRICE: float = 400.0
    # 金价低于该值通知[具体价格]
    FALL_TO_TARGET_PRICE: float = 365.0
    # 设置同类型通知在多长时间范围内限制重复推送次数[秒]
    DUPLICATE_NOTIFY_TIME_LIMIT: int = 90
    # 设置同类型通知重复推送多少次
    DUPLICATE_NOTIFY_TIMES: int = 3
    # youtube music download
    YOUTUBE_PLAY_LIST: str = ""
    # synology
    SYNOLOGY_HOST: str = ""
    SYNOLOGY_PORT: int = 5000
    SYNOLOGY_USERNAME: str = ""
    SYNOLOGY_PASSWORD: str = ""
    SYNOLOGY_USE_SSL: bool = False
    SYNOLOGY_CERT_VERIFY: bool = False
    SYNOLOGY_DSM_VERSION: int = 7
    SYNOLOGY_MUSIC_DIR: str = "/music"


class MainDBSession(scoped_session, Session):
    pass


class CacheRedis(StrictRedis):
    pass


@autoparams()
def init_oauth2_sso(config: Config) -> OAuth2SSO:
    # 初始化
    oauth2_sso_instance: OAuth2SSO = OAuth2SSO(
        # OAuth2服务配置
        client_id=config.OAUTH2_CLIENT_ID,
        client_secret=config.OAUTH2_CLIENT_SECRET,
        authorization_endpoint=config.OAUTH2_AUTHORIZATION_ENDPOINT,
        token_endpoint=config.OAUTH2_TOKEN_ENDPOINT,
        userinfo_endpoint=config.OAUTH2_USERINFO_ENDPOINT,
        # 后端服务地址
        app_root_url=config.APP_ROOT_URI,
        # 认证成功后跳转该地址并带上token
        after_login_redirect_url=config.APP_FRONTEND_URI,
        # 后端服务认证地址
        api_auth_path=config.APP_AUTH_PATH,
        # 后端服务登出地址
        api_logout_path=config.APP_LOGOUT_PATH,
        jwt_secret=config.JWT_SECRET_KEY,
        token_timeout=config.JWT_EXPIRE_TIME,
        debug_mode=config.IS_DEV
    )
    # sso绑定handler
    from app.handlers.oauth2_sso import (
        before_redirect_handler, oauth2_sso_generate_token_info_handler, oauth2_sso_logout_handler
    )
    oauth2_sso_instance.set_generate_token_info_handler(oauth2_sso_generate_token_info_handler)
    oauth2_sso_instance.set_before_redirect_handler(before_redirect_handler)
    oauth2_sso_instance.set_logout_handler(oauth2_sso_logout_handler)
    return oauth2_sso_instance


@autoparams()
def init_auth(config: Config) -> Auth:
    # 初始化
    auth: Auth = Auth(config.JWT_SECRET_KEY, not config.IS_DEV)
    # 绑定handler
    from app.handlers.auth import get_user_roles_handler, get_user_info_handler, user_define_validator_handler
    auth.set_get_user_info_handler(get_user_info_handler)
    auth.set_get_user_roles_handler(get_user_roles_handler)
    auth.set_user_define_validator_handler(user_define_validator_handler)
    return auth


@autoparams()
def init_cache(_config: Config) -> Cache:
    from app.handlers.cache import get_cache_handler, store_cache_handler, generate_cache_key_handler
    # 初始化
    cache_instance: Cache = Cache()
    # 设置handler
    cache_instance.set_get_cache_handler(get_cache_handler)
    cache_instance.set_store_cache_handler(store_cache_handler)
    cache_instance.set_generate_cache_key_handler(generate_cache_key_handler)
    return cache_instance


@autoparams()
def init_migrate(_config: Config) -> Migration:
    from app.handlers.migrate import init_data_handler
    # 初始化
    migration_instance: Migration = Migration(
        database_uri=_config.SQLALCHEMY_DATABASE_URI, project=_config.PROJECT_NAME, workspace=_config.PROJECT_PATH
    )
    # 设置handler
    migration_instance.set_do_init_data_handler(init_data_handler)
    return migration_instance


def init_json_encoder() -> TemplateJSONEncoder:
    return TemplateJSONEncoder()


def init_i18n() -> TemplateBabel:
    # 获得翻译文件路径
    translate_cfg_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "translations")
    return TemplateBabel("messages", translate_cfg_root)


def init_pagination() -> Pagination:
    pagination: Pagination = Pagination()
    # 绑定handler
    from app.handlers.pagination import get_page_paginate_params_handler, do_after_paginate_handler
    pagination.set_get_page_paginate_params_handler(get_page_paginate_params_handler)
    pagination.set_do_after_paginate_handler(do_after_paginate_handler)
    return pagination


def init_apollo_client() -> ApolloClient:
    from app.handlers.apollo import config_changed_handler

    # 获取阿波罗配置中心的环境变量
    apollo_config: ApolloClient = ApolloClient(
        app_id=Config.APOLLO_APP_ID,
        config_server_url=Config.APOLLO_CONFIG_SERVER_URL
    )
    apollo_config.set_config_changed_handler(config_changed_handler)
    return apollo_config


@autoparams()
def init_main_db_session(config: Config):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import (
        sessionmaker,
        scoped_session
    )
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI, pool_recycle=3600, isolation_level='READ COMMITTED')
    return scoped_session(sessionmaker(engine))


@autoparams()
def init_redis_session(config: Config) -> CacheRedis:
    r: CacheRedis = StrictRedis.from_url(config.REDIS_URL)
    return r


@autoparams()
def bind_config_from_apollo(apollo_config: ApolloClient) -> Config:
    _fields: List[Field] = get_fields(Config)
    config_dict: Dict[str, Any] = dict()
    for _field in _fields:
        _v: Any = apollo_config.get_value(_field.name)
        if _v is not None:
            # 处理bool
            if _field.type == bool:
                config_dict[_field.name] = _field.type(json.loads(str(_v).lower()))
                continue
            # 类型转换
            config_dict[_field.name] = _field.type(_v)
    _config = from_dict(Config, config_dict)
    return _config


def bind_config_from_file(config_cls: Type[T] = Config) -> T:
    # 获取配置路径[在测试得时候可以覆盖该环境变量指定配置文件路径]
    config_dir: str = os.getenv("CONFIG_PATH", os.path.join(Config.PROJECT_PATH, "configs"))
    config_file: str = os.path.join(config_dir, "settings.yaml")
    # 加载配置
    settings = Dynaconf(
        settings_files=[
            config_file,
        ],
        environments=True,
        load_dotenv=True,
    )
    _fields: List[Field] = get_fields(config_cls)
    config_dict: Dict[str, Any] = {}
    for _field in _fields:
        # 配置不存在, 则忽略
        _v: Any = settings.get(_field.name.upper())
        if _v is not None:
            # 子配置转换
            if not isinstance(_field.type, type) or issubclass(_field.type, ConfigItem):
                config_dict[_field.name] = _v
                continue
            # 类型转换
            if isinstance(_field.type, type):
                config_dict[_field.name] = _field.type(_v)

    _config: T = from_dict(config_cls, config_dict)
    return _config


@autoparams()
def init_work_wechat(config: Config) -> WorkWeChat:
    return WorkWeChat(corpid=config.CORP_ID, corpsecret=config.CORP_SECRET)


def bind(binder):
    from app.tasks import init_celery
    # 初始化apollo
    # binder.bind_to_constructor(ApolloClient, init_apollo_client)
    # 初始化配置
    # binder.bind_to_constructor(Config, bind_config_from_apollo)
    binder.bind_to_constructor(Config, bind_config_from_file)
    # 初始化celery
    binder.bind_to_constructor(Celery, init_celery)
    # 初始化主库
    binder.bind_to_constructor(MainDBSession, init_main_db_session)
    # 初始化redis
    binder.bind_to_constructor(CacheRedis, init_redis_session)
    # 初始化国际化
    binder.bind_to_constructor(TemplateBabel, init_i18n)
    # 增加idc认证
    binder.bind_to_constructor(OAuth2SSO, init_oauth2_sso)
    # 增加角色认证插件
    binder.bind_to_constructor(Auth, init_auth)
    # 增加分页插件
    binder.bind_to_constructor(Pagination, init_pagination)
    # 增加缓存插件
    binder.bind_to_constructor(Cache, init_cache)
    # 增加数据迁移插件
    binder.bind_to_constructor(Migration, init_migrate)
    # 增加Json序列化Encoder
    binder.bind_to_constructor(TemplateJSONEncoder, init_json_encoder)
    # 初始化企业微信
    binder.bind_to_constructor(WorkWeChat, init_work_wechat)
