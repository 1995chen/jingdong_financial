# -*- coding: utf-8 -*-


"""
dependencies: Config component
"""

import json
import logging
import os
from dataclasses import Field, dataclass, field, make_dataclass
from typing import Any, Dict, List

from dacite import from_dict
from dacite.dataclasses import get_fields
from dynaconf import Dynaconf

from infra.dependencies.auth import AuthConfig
from infra.dependencies.celery import CeleryConfig
from infra.dependencies.rdb import RDBConfig
from infra.dependencies.redis_client import RedisConfig
from infra.enums import RuntimeEnv, Switch
from infra.handlers.json import JSONEncoderHandler

__all__ = (
    "Config",
    "HospitalReserveConfig",
    "YouTubeSubscribeConfig",
    "bind_config",
)

# cpu count
CPU_COUNT = os.cpu_count() or 8
logger = logging.getLogger(__name__)


# do not check snake_case naming style
# pylint: disable=C0103,R0902
@dataclass
class YouTubeSubscribeConfig:
    """
    YouTube Subscribe Config
    """

    PATH: str
    PLAYLIST: str


# do not check snake_case naming style
# pylint: disable=C0103,R0902
@dataclass
class SynologyConfig:
    """
    Synology Config
    """

    SYNOLOGY_HOST: str = ""
    SYNOLOGY_PORT: int = 5000
    SYNOLOGY_USERNAME: str = ""
    SYNOLOGY_PASSWORD: str = ""
    SYNOLOGY_USE_SSL: bool = False
    SYNOLOGY_CERT_VERIFY: bool = False
    SYNOLOGY_DSM_VERSION: int = 7


# do not check snake_case naming style
# pylint: disable=C0103,R0902
@dataclass
class HospitalReserveConfig:
    """
    Hospital Reserve Config
    """

    RESERVE_APP_ID: int = 501107
    RESERVE_DEPT_CODES: str = ""
    RESERVE_DOCTOR_WORK_NUMS: str = ""
    RESERVE_REGISTER_TYPE: str = "1,2,5,6,7,9,I,J,M,K,W,Y,R,8"
    RESERVE_APPOINTMENT_TYPE: str = "1,2,5,6,7,9,I,J,M,K,W,Y,R,8"
    RESERVE_PRICE_LIMIT: int = 0
    RESERVE_DUPLICATE_NOTIFY_TIMES: int = 1
    RESERVE_DUPLICATE_NOTIFY_TIME_LIMIT: int = 7200


# do not check snake_case naming style
# pylint: disable=C0103,R0902
@dataclass
class WechatWorkConfig:
    """
    WechatWork Config
    """

    # 企业微信 CORP_ID
    CORP_ID: str = ""
    # 企业微信 CORP_SECRET
    CORP_SECRET: str = ""
    # 企业微信应用 AGENT_ID
    AGENT_ID: int = 0


# do not check snake_case naming style
# pylint: disable=C0103,R0902
@dataclass
class GoldConfig:
    """
    Gold Task Config
    """

    # 京东金融API配置
    JD_FINANCE_API_URL: str = "https://ms.jr.jd.com/gw/generic/hj/h5/m/latestPrice"
    # header信息
    JD_FINANCE_API_HEADERS: str = json.dumps(
        {
            "referer": "https://m.jdjygold.com/finance-gold/msjgold/homepage?orderSource=7",
            "host": "ms.jr.jd.com",
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


# do not check snake_case naming style
# pylint: disable=C0103,R0902
@dataclass
class Config:
    """
    Configuration class, when the program starts,
    all configurations in the configuration file
    will be mapped to the configuration class.
    Subsequent program configurations will be
    obtained from the configuration class
    """

    # ============= Service common configuration =============
    # Service Port
    PORT: int = int(os.getenv("PORT", "8080"))
    # Log Level
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    # Documents [Documents are individually controlled]
    OPEN_DOC: Switch = Switch(int(os.getenv("OPEN_DOC", f"{Switch.Open.value}")))
    # Env
    ENV: RuntimeEnv = RuntimeEnv(
        os.getenv("ENV_FOR_DYNACONF", RuntimeEnv.DEVELOPMENT.value).upper()
    )
    # Log configuration
    LOG_CONFIG_PATH: str = os.getenv("LOG_CONFIG_PATH") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "configs",
        "log.ini",
    )
    # worker count
    SERVER_WORKER: int = int(os.getenv("WORKERS", CPU_COUNT))
    # worker thread count
    SERVER_WORKER_THREAD: int = min(32, 2 * SERVER_WORKER)
    # Configure the time for slow API
    SLOW_API_LIMIT_TIME: int = 1
    # Configure remote http timeout
    REMOTE_HTTP_TIMEOUT: int = 10
    # Project name
    PROJECT_NAME: str = "jingdong_financial"
    # Project path
    PROJECT_PATH: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # static path
    STATIC_PATH: str = os.path.join(PROJECT_PATH, "static", "release")
    # auth config
    AUTH_CONFIG: AuthConfig = field(default_factory=lambda: AuthConfig())
    # rdb config
    MYSQL_DATASOURCE_CONFIG: RDBConfig = field(default_factory=lambda: RDBConfig())
    # redis config
    REDIS_DATASOURCE_CONFIG: RedisConfig = field(default_factory=lambda: RedisConfig())
    # celery config
    CELERY_CONFIG: CeleryConfig = field(default_factory=lambda: CeleryConfig())

    # ================================== API Config ==================================
    # API prefix
    API_PREFIX: str = "/api"
    WECHAT_WORK_CONFIG: WechatWorkConfig = field(default_factory=lambda: WechatWorkConfig())
    # 配置群晖
    SYNOLOGY_CONFIG: SynologyConfig = field(default_factory=lambda: SynologyConfig())
    # 黄金配置
    GOLD_CONFIG: GoldConfig = field(default_factory=lambda: GoldConfig())
    # 油管订阅
    YOUTUBE_SUBSCRIBE_LIST: List[YouTubeSubscribeConfig] = field(default_factory=lambda: [])
    # 预约挂号
    HOSPITAL_RESERVE: List[HospitalReserveConfig] = field(default_factory=lambda: [])


def bind_config() -> Config:
    """
    Initialize the configuration class method
    :return: Config instance
    """
    # Get the configuration path [When testing, you can overwrite
    # the environment variable to specify the configuration file path]
    config_dir: str = os.getenv("CONFIG_PATH", os.path.join(Config.PROJECT_PATH, "configs"))
    logger.info(f"config_dir is {config_dir}")
    # Load config
    settings = Dynaconf(
        settings_files=[
            os.path.join(config_dir, "settings.yaml"),
        ],
        environments=True,
        load_dotenv=True,
    )
    _fields: List[Field] = get_fields(Config)
    config_dict: Dict[str, Any] = {}
    for _field in _fields:
        # If the configuration does not exist, it will be ignored.
        _v: Any = settings.get(_field.name.upper())
        _t: Any = _field.type
        if _v is not None:
            # For basic data types, convert
            if _t == bool:
                config_dict[_field.name] = str(_v).lower() == "true"
                continue
            if _t in [int, float, str, list, tuple, dict, set]:
                config_dict[_field.name] = _t(_v)
                continue
            # Subconfiguration transformation
            _target_cls: Any = make_dataclass("TargetCls", [(_field.name, _t)])
            config_dict[_field.name] = getattr(
                from_dict(_target_cls, {_field.name: _v}), _field.name
            )
    _config: Config = from_dict(Config, config_dict)
    logger.info("============================load dynaconf config============================")
    logger.info(json.dumps(config_dict, cls=JSONEncoderHandler, indent=4))
    return _config
