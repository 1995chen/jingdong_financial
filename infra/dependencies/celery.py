# -*- coding: utf-8 -*-

"""
dependencies: celery component
"""

import importlib
import json
import logging
import pkgutil
from dataclasses import dataclass
from types import ModuleType
from typing import List

from celery import Celery
from kombu import Exchange, Queue
from kombu.serialization import register
from orjson import dumps, loads

from infra.enums.common import RuntimeEnv
from infra.handlers.json import JSONEncoderHandler

# Export dependencies. All subsequent dependencies are exported from common.dependencies
__all__ = [
    "Celery",
    "get_celery_by_config",
    "CeleryConfig",
]

logger = logging.getLogger(__name__)
# Register a new encoder/decoder
register("orjson", dumps, loads, content_type="application/json", content_encoding="utf-8")


# do not check snake_case naming style
# pylint: disable=C0103,R0902
@dataclass
class CeleryConfig:
    """
    celery config
    """

    CELERY_BROKER: str = ""
    CELERY_BACKEND: str = ""
    # celery redbeat redis url is used to prevent multiple celery beats
    # from running simultaneously under multiple copies
    CELERY_REDBEAT: str = ""
    # celery beat lock timeout
    REDBEAT_LOCK_TIMEOUT: int = 10
    # Number of concurrent scheduled task processes
    BEAT_WORKER_NUM: int = 2
    # Number of concurrent worker processes
    WORKER_NUM: int = 2
    # The maximum number of tasks that can be executed by each worker process
    MAX_TASKS_PER_CHILD: int = 20


def get_celery_by_config(app_name: str, config: CeleryConfig, env: RuntimeEnv) -> Celery:
    """
    Celery init function
    :param app_name: app name
    :param config: CeleryConfig instance
    :param env: RuntimeEnv
    :return: Celery instance
    """

    def get_sub_modules(_modules: List[str]) -> List[str]:
        """
        Get a list of all submodules under a module
        _modules: List of modules to be retrieved
        """
        _sub_modules: List[str] = []
        # Retrieve all modules in the directory
        for _pkg in _modules:
            _module: ModuleType = importlib.import_module(_pkg)
            for _, _sub_module_name, _ in pkgutil.iter_modules(_module.__path__):
                _sub_modules.append(f"{_pkg}.{_sub_module_name}")
        return _sub_modules

    # Asynchronous task root directory
    async_task_root: str = "celery_tasks.async_tasks"
    # Scheduled task root directory
    schedule_task_root: str = "celery_tasks.schedule_tasks"

    _celery = Celery(
        app_name,
        include=get_sub_modules([async_task_root, schedule_task_root]),
    )

    # scheduled tasks
    beat_schedule = {
        # 同步黄金价格
        f"{schedule_task_root}.gold_task.sync_gold_price": {
            "task": f"{schedule_task_root}.gold_task.sync_gold_price",
            "args": (),
            "schedule": 5,
            "options": {"queue": f"{app_name}-{env.value}-beat-queue"},
        },
        # 黄金通知
        f"{schedule_task_root}.gold_task.gold_price_remind": {
            "task": f"{schedule_task_root}.gold_task.gold_price_remind",
            "args": (),
            "schedule": 5,
            "options": {"queue": f"{app_name}-{env.value}-beat-queue"},
        },
        # 医院预约挂号
        f"{schedule_task_root}.hospital_reserve_task.reserve_notify_task": {
            "task": f"{schedule_task_root}.hospital_reserve_task.reserve_notify_task",
            "args": (),
            "schedule": 600,
            "options": {"queue": f"{app_name}-{env.value}-beat-queue"},
        },
        # 同步播放列表
        f"{schedule_task_root}.music_task.sync_play_list": {
            "task": f"{schedule_task_root}.music_task.sync_play_list",
            "args": (),
            "schedule": 600,
            "options": {"queue": f"{app_name}-{env.value}-beat-queue"},
        },
    }

    logger.info(
        "\n*********************************Scheduled Tasks*********************************\n"
        "%s"
        "\n*********************************Scheduled Tasks*********************************\n",
        json.dumps(beat_schedule, indent=4, cls=JSONEncoderHandler),
    )
    _celery.conf.update(
        beat_schedule=beat_schedule,
        # Define queues [If additional queues are needed, define them here]
        task_queues=[
            # The default queue does not need to be defined. Here it is defined as an example
            Queue(
                f"{app_name}-{env.value}-queue",
                # Exchange persistence
                Exchange(
                    f"{app_name}-{env.value}-exchange",
                    durable=True,
                    delivery_mode=2,
                ),
                routing_key=f"{app_name}-{env.value}-routing",
                # Queue persistence
                durable=True,
            ),
            # Define a scheduled task queue
            Queue(
                f"{app_name}-{env.value}-beat-queue",
                Exchange(
                    f"{app_name}-{env.value}-exchange",
                    durable=True,
                    delivery_mode=2,
                ),
                routing_key=f"{app_name}-{env.value}-beat-routing",
                # Queue persistence
                durable=True,
            ),
        ],
        # Define routes [some tasks require separate queue processing for speed-up, defined here]
        task_routes={
            # This task does not need to be defined, and is defined here as an example
            f"{async_task_root}.test_task.do_test": {
                "queue": f"{app_name}-queue",
                "routing_key": f"{app_name}-{env.value}-routing",
            },
        },
        # Default Queue
        task_default_queue=f"{app_name}-{env.value}-queue",
        # Default Exchange
        task_default_exchange=f"{app_name}-{env.value}-exchange",
        # Default Router
        task_default_routing_key=f"{app_name}-{env.value}-routing",
        task_default_exchange_type="direct",
        # Tasks persistence
        task_default_delivery_mode="persistent",
        broker_url=config.CELERY_BROKER,
        result_backend=config.CELERY_BACKEND,
        # task timeout
        task_time_limit=300,
        task_acks_late=True,
        result_persistent=False,
        # ignore task result
        task_ignore_result=True,
        task_remote_tracebacks=True,
        task_store_errors_even_if_ignored=True,
        worker_send_task_events=True,
        worker_max_memory_per_child=131072,
        result_expires=600,
        # The data format that Celery allows to receive
        accept_content=["pickle", "json"],
        # Serializer for asynchronous tasks, can also be json, pickle
        task_serializer="orjson",
        # The data format of the task result can also be json, pickle
        result_serializer="orjson",
        # event serializer
        event_serializer="orjson",
        timezone="Asia/Shanghai",
        enable_utc=True,
        broker_connection_timeout=10,
        # Intercept root log configuration
        worker_hijack_root_logger=False,
        worker_log_format=(
            "[%(name)s]:%(asctime)s:%(filename)s:%(lineno)d"
            " %(levelname)s/%(processName)s %(message)s"
        ),
        # REDBEAT_REDIS_URL Multiple instances allow celery beat
        redbeat_redis_url=config.CELERY_REDBEAT or config.CELERY_BROKER,
        # Lock prefix
        redbeat_key_prefix=f"{app_name}-{env.value}-redbeat",
        # Lock timeout
        redbeat_lock_timeout=config.REDBEAT_LOCK_TIMEOUT,
        # Retry
        broker_transport_options={
            "max_retries": 3,  # max retry times
            "interval_start": 0,  # Start retry time
            "interval_step": 0.2,  # Each retry interval
            "interval_max": 0.2,  # maximum interval time
        },
    )
    return _celery
