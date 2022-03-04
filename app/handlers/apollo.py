# -*- coding: utf-8 -*-


from typing import Dict, Any

import inject
import requests
import template_logging

from app.constants.enum import SysCMD

logger = template_logging.getLogger(__name__)


def config_changed_handler(entry: Dict[str, Any]) -> Any:
    from app.dependencies import bind, Config
    from app.tasks.async_tasks.refresh_config_task import do_refresh_config

    config: Config = inject.instance(Config)
    logger.info(f"get entry: {entry}")
    # 通知API刷新配置
    # noinspection PyBroadException
    try:
        logger.info(f"config_changed_handler.cmd: {config.CMD}")
        # 通知API刷新配置
        if config.CMD in (SysCMD.RUN_API_SERVER, SysCMD.RUN_TEST_SERVER):
            requests.get(
                f"http://127.0.0.1:{config.PORT}/api/v1/config/refresh?inner_call_uuid={config.INNER_CALL_UID}"
            )
        # 通知定时任务
        if config.CMD == SysCMD.RUN_BEAT_WORKER:
            do_refresh_config.apply_async(queue=f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-beat-queue')
        # 通知异步任务
        if config.CMD == SysCMD.RUN_CUSTOM_WORKER:
            do_refresh_config.apply_async(queue=f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-queue')
        # 重置配置
        inject.clear_and_configure(bind, bind_in_runtime=False)
    except Exception:
        logger.warning(f"failed to refresh config", exc_info=True)
