# -*- coding: utf-8 -*-


import os
import importlib
from typing import Any

import click
import inject
from redis_lock import Lock
from celery import Celery
from template_migration import Migration
from template_apollo import ApolloClient

from app.dependencies import Config, CacheRedis
from app.constants.enum import SysCMD
from app.utils.common import generate_table, print_config

# 加载日志模块
template_logging: Any = importlib.import_module('template_logging')

# 初始化日志
template_logging.init_logger()
# 获取Logger
logger = template_logging.getLogger(__name__)


@click.group()
def cli():
    logger.info('Init app...')
    # 生成数据库表
    generate_table()
    print_config()
    # 获取配置
    config: Config = inject.instance(Config)
    # 启动apollo后台监听线程
    if config.CMD in (
            SysCMD.RUN_API_SERVER, SysCMD.RUN_TEST_SERVER, SysCMD.RUN_BEAT,
            SysCMD.RUN_BEAT_WORKER, SysCMD.RUN_CUSTOM_WORKER
    ):
        # 暂时关闭apollo
        # apollo_client: ApolloClient = inject.instance(ApolloClient)
        # apollo_client.start()
        pass
    # 加🔒, 执行migrate脚本,只执行一次
    lock_key: str = f"migrate-lock:{config.PROJECT_NAME}-{config.RUNTIME_ENV}"
    # 获取redis
    redis_cache: CacheRedis = inject.instance(CacheRedis)
    lock = Lock(redis_cache, lock_key)
    if lock.acquire(blocking=True, timeout=1800):
        try:
            migration_instance: Migration = inject.instance(Migration)
            migration_instance.do_migrate()
        except Exception as e:
            logger.error(f"failed to do migrate", exc_info=True)
            raise e
        finally:
            # 释放🔒
            lock.release()


@cli.command()
def run_print_config():
    """
    打印配置
    """
    click.echo('run_print_config ......')
    print_config()


@cli.command()
def run_api_server():
    """
    启动服务
    """
    from app.gunicorn_app import run_http_server
    from app.flask_app import flask_app

    logger.info(f'Run api server...')
    port: int = os.getenv('PORT', 8080)
    logger.info(f"bind ip is http://0.0.0.0:{port}")
    # 启动 gunicorn server
    run_http_server(flask_app, {
        'bind': f'0.0.0.0:{port}',
        'accesslog': '-',
        'errorlog': '-',
        'max_requests': 8000,
        'timeout': 60,
        'worker_connections': 4000,
        'capture_output': True,
        'reload': False,
        # 使用默认的worker类型
        'worker_class': 'gthread',
        'limit_request_line': 8000,
    })


@cli.command()
def run_test_server():
    """
    启动服务
    """
    from app.flask_app import flask_app
    logger.info(f"Run test server")
    logger.info("bind ip is http://0.0.0.0:8080")
    flask_app.run('0.0.0.0', 8080, debug=True)


@cli.command()
def run_beat():
    """
    启动celery定时任务
    """
    celery_app = inject.instance(Celery)
    celery_app.start(
        argv=['celery', 'beat', '-S', 'redbeat.RedBeatScheduler', '-l', 'INFO', '--pidfile=']
    )


@cli.command()
def run_beat_worker():
    """
    该worker仅消费默认定时任务队列消息
    """
    # 获取配置
    config: Config = inject.instance(Config)
    celery_app = inject.instance(Celery)
    celery_app.start(
        argv=['celery', 'worker', '-l', 'INFO', '-n',
              f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-run_beat_worker@%h',
              '-c', f'{config.WORKER_NUM}', '-Q', f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-beat-queue',
              '--max-tasks-per-child', f'{config.MAX_TASKS_PER_CHILD}',
              ]
    )


@cli.command()
def run_custom_worker():
    """
    执行业务中异步任务
    该worker仅消费默认队列消息
    """
    # 获取配置
    config: Config = inject.instance(Config)
    celery_app = inject.instance(Celery)
    celery_app.start(
        argv=['celery', 'worker', '-l', 'INFO', '-n',
              f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-run_custom_worker@%h',
              '-c', f'{config.WORKER_NUM}', '-Q', f'{config.PROJECT_NAME}-{config.RUNTIME_ENV}-queue',
              '--max-tasks-per-child', f'{config.MAX_TASKS_PER_CHILD}',
              ]
    )


@cli.command()
def test():
    """
    单元测试
    """
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@cli.command()
def migrate():
    """
    数据库migrate
    如果没有migrate记录则要初始化数据
    """
    from template_migration import Migration
    migration_instance: Migration = inject.instance(Migration)
    migration_instance.do_migrate()


if __name__ == '__main__':
    cli()
