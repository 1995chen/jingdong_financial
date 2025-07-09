# -*- coding: utf-8 -*-


"""
project entry, support command line
"""

import importlib
import logging
import platform
from types import ModuleType

import click
import inject
import uvicorn
from redis_lock import Lock

from infra.dependencies import Celery, Config, MainRDB, MainRedis, Migration

logger = logging.getLogger(__name__)
config: Config = inject.instance(Config)


@click.group()
def cli() -> None:
    """
    this method will call before each service start
    """
    logger.info("Init app...")
    # Generate database table
    inject.instance(MainRDB).generate_table()
    # Add 🔒, execute the migrate script, only execute once
    lock_key: str = f"migrate-lock:{config.PROJECT_NAME}-{config.ENV.value}"
    redis_client: MainRedis = inject.instance(MainRedis)
    lock = Lock(redis_client, lock_key)
    if lock.acquire(blocking=True, timeout=1800):
        try:
            migration_instance: Migration = inject.instance(Migration)
            migration_instance.do_migrate()
        except Exception as e:
            logger.error("failed to do migrate", exc_info=True)
            raise e
        finally:
            # release🔒
            lock.release()


@cli.command()
def run_api_server() -> None:
    """
    run api server

    doc: https://www.uvicorn.org/#running-with-gunicorn
    uvicorn.run(app, host="0.0.0.0", port=config.PORT, workers=config.SERVER_WORKER)
    """

    uvicorn_config = uvicorn.Config(
        "api_server.fastapi_app:app",
        host="0.0.0.0",
        port=config.PORT,
        log_level="info",
        # local run open access_log
        access_log=True,
    )
    if platform.system().lower() == "linux":
        uvicorn_config.workers = config.SERVER_WORKER
    server = uvicorn.Server(uvicorn_config)
    server.run()


@cli.command()
def run_schedule() -> None:
    """
    send celery schedule tasks
    """
    celery_app = inject.instance(Celery)
    celery_app.start(argv=["beat", "-S", "redbeat.RedBeatScheduler", "-l", "INFO", "--pidfile="])


@cli.command()
def run_schedule_tasks() -> None:
    """
    consumer celery schedule tasks
    """
    celery_app = inject.instance(Celery)
    celery_app.start(
        argv=[
            "worker",
            "-l",
            "INFO",
            "-n",
            f"{config.PROJECT_NAME}-{config.ENV.value}-run_schedule_tasks@%h",
            "-c",
            f"{config.CELERY_CONFIG.WORKER_NUM}",
            "-Q",
            f"{config.PROJECT_NAME}-{config.ENV.value}-beat-queue",
            "--max-tasks-per-child",
            f"{config.CELERY_CONFIG.MAX_TASKS_PER_CHILD}",
        ]
    )


@cli.command()
def run_async_tasks() -> None:
    """
    consumer celery async tasks
    """
    celery_app = inject.instance(Celery)
    celery_app.start(
        argv=[
            "worker",
            "-l",
            "INFO",
            "-n",
            f"{config.PROJECT_NAME}-{config.ENV.value}-run_async_tasks@%h",
            "-c",
            f"{config.CELERY_CONFIG.WORKER_NUM}",
            "-Q",
            f"{config.PROJECT_NAME}-{config.ENV.value}-queue",
            "--max-tasks-per-child",
            f"{config.CELERY_CONFIG.MAX_TASKS_PER_CHILD}",
        ]
    )


@cli.command()
def run_grpc_debug() -> None:
    """
    run grpc for debug
    """
    # Load the grpc_app module [here to avoid loading the grpc module when starting the web service]
    grpc_app_module: ModuleType = importlib.import_module("grpc_server.grpc_app")
    grpc_app_module.run_with_multi_thread(config.PORT)


@cli.command()
def run_grpc_prod() -> None:
    """
    Multi-process startup
    """
    # Load the grpc_app module [here to avoid loading the grpc module when starting the web service]
    grpc_app_module: ModuleType = importlib.import_module("grpc_server.grpc_app")
    grpc_app_module.server_with_multiprocess(config.PORT)


@cli.command()
def check_grpc_health() -> None:
    """
    grpc service check
    """
    # Load the grpc_app module [here to avoid loading the grpc module when starting the web service]
    grpc_check_module: ModuleType = importlib.import_module("grpc_server.health_check")
    grpc_check_module.health_check()


if __name__ == "__main__":
    cli()
