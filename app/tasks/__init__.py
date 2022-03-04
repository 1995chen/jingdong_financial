# -*- coding: utf-8 -*-


import json
import pkgutil
import importlib
from typing import List
from types import ModuleType

import inject
import template_logging
from celery.signals import task_postrun, task_prerun
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

from app.dependencies import Config

logger = template_logging.getLogger(__name__)


class CrontabEncoder(json.JSONEncoder):
    """
    定义一个crontab的encoder
    """

    def default(self, obj):
        if isinstance(obj, crontab):
            return str(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


def get_sub_modules(_modules: List[str]) -> List[str]:
    """
    获得模块下所有子模块列表
    _modules: 待检索模块列表
    """
    _sub_modules: List[str] = list()
    # 检索目录下所有模块
    for _pkg in _modules:
        _module: ModuleType = importlib.import_module(_pkg)
        for _, _sub_module_name, _ in pkgutil.iter_modules(_module.__path__):
            _sub_modules.append(f"{_pkg}.{_sub_module_name}")
    return _sub_modules


@inject.autoparams()
def init_celery(config: Config):
    # 异步任务根目录
    async_task_root: str = 'app.tasks.async_tasks'
    # 定时任务根目录
    schedule_task_root: str = 'app.tasks.schedule_tasks'

    _celery = Celery(
        config.PROJECT_NAME,
        include=get_sub_modules([async_task_root, schedule_task_root])
    )

    # 定时任务
    beat_schedule = {
        f'{schedule_task_root}.daily_do_task.test_scheduler': {
            'task': f'{schedule_task_root}.daily_do_task.test_scheduler',
            'args': (),
            'schedule': 60,
            'options': {
                # 该定时任务会被调度到这个队列
                'queue': f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-beat-queue'
            }
        },
        # 同步黄金价格
        f'{schedule_task_root}.gold_task.sync_gold_price': {
            'task': f'{schedule_task_root}.gold_task.sync_gold_price',
            'args': (),
            'schedule': 5,
            'options': {
                # 该定时任务会被调度到这个队列
                'queue': f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-beat-queue'
            }
        },
        # 黄金通知
        f'{schedule_task_root}.gold_task.gold_price_remind': {
            'task': f'{schedule_task_root}.gold_task.gold_price_remind',
            'args': (),
            'schedule': 5,
            'options': {
                # 该定时任务会被调度到这个队列
                'queue': f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-beat-queue'
            }
        },
    }

    logger.info(
        f'\n*********************************Scheduled tasks*********************************\n'
        f'{json.dumps(beat_schedule, indent=4, cls=CrontabEncoder)}\n'
        f'*********************************Scheduled tasks*********************************\n'
    )
    _celery.conf.update(
        CELERYBEAT_SCHEDULE=beat_schedule,
        # 定义队列[如果需要额外的队列,定义在这里]
        CELERY_QUEUES=[
            # 该默认队列可以不用定义,这里定义作为Example
            Queue(
                f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-queue',
                # 交换机持久化
                Exchange(f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-exchange', durable=True, delivery_mode=2),
                routing_key=f'{config.PROJECT_NAME}-routing',
                # 队列持久化
                durable=True
            ),
            # 定义定时任务队列
            Queue(
                f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-beat-queue',
                Exchange(f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-exchange', durable=True, delivery_mode=2),
                routing_key=f'{config.PROJECT_NAME}-beat-routing',
                # 队列持久化
                durable=True
            ),
        ],
        # 定义路由[部分任务需要单独的队列处理用于提速,定义在这里]
        CELERY_ROUTES={
            # 该任务可以不用定义,这里定义作为Example
            f'{async_task_root}.test_task.do_test': {
                'queue': f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-queue',
                'routing_key': f'{config.PROJECT_NAME}-routing'
            },
        },
        # 默认队列
        CELERY_DEFAULT_QUEUE=f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-queue',
        # 默认交换机
        CELERY_DEFAULT_EXCHANGE=f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-exchange',
        # 默认路由
        CELERY_DEFAULT_ROUTING_KEY=f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-routing',
        CELERY_DEFAULT_EXCHANGE_TYPE='direct',
        # 任务持久化
        CELERY_DEFAULT_DELIVERY_MODE="persistent",

        BROKER_URL=config.CELERY_BROKER,
        CELERY_RESULT_BACKEND=config.CELERY_BACKEND,
        # 任务的硬超时时间
        CELERYD_TASK_TIME_LIMIT=300,
        CELERY_ACKS_LATE=True,
        CELERY_RESULT_PERSISTENT=False,
        # 默认忽略结果, 需要保存结果的任务需要手动定义ignore_result=True
        CELERY_IGNORE_RESULT=True,
        CELERY_TASK_RESULT_EXPIRES=86400,
        # celery允许接收的数据格式
        CELERY_ACCEPT_CONTENT=['pickle', 'json'],
        # 异步任务的序列化器，也可以是json
        CELERY_TASK_SERIALIZER='pickle',
        # 任务结果的数据格式，也可以是json
        CELERY_RESULT_SERIALIZER='pickle',
        CELERY_TIMEZONE='Asia/Shanghai',
        CELERY_ENABLE_UTC=True,
        BROKER_CONNECTION_TIMEOUT=10,
        # 拦截根日志配置
        CELERYD_HIJACK_ROOT_LOGGER=False,
        CELERYD_LOG_FORMAT='[%(name)s]:%(asctime)s:%(filename)s:%(lineno)d %(levelname)s/%(processName)s %(message)s',
        # REDBEAT_REDIS_URL 多实例允许celery beat
        redbeat_redis_url=config.REDBEAT_REDIS_URL or config.CELERY_BROKER,
        # 锁前缀
        redbeat_key_prefix=f"{config.PROJECT_NAME}-{config.RUNTIME_ENV}-redbeat",
        # 锁超时时间
        redbeat_lock_timeout=config.REDBEAT_LOCK_TIMEOUT
    )
    return _celery


@task_prerun.connect()
def task_prerun_handler(task_id, task, *args, **kwargs):
    config: Config = inject.instance(Config)
    logger.info(f'task_prerun_handler, config is {config}')


@task_postrun.connect()
def task_postrun_handler(*args, **kwargs):
    from app.dependencies import MainDBSession
    inject.instance(MainDBSession).remove()
