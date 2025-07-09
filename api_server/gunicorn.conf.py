# -*- coding: utf-8 -*-
# pylint: skip-file
# type: ignore

"""
doc: https://docs.gunicorn.org/en/stable/settings.html#reload
"""

import logging
import os
import subprocess
from math import ceil
from pathlib import Path

log_level: str = os.getenv("LOG_LEVEL", "INFO")
gunicorn_error_logger = logging.getLogger("gunicorn.error")
# close uvicorn access log when log level is not debug
if log_level != "DEBUG":
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.disabled = True
    gunicorn_access = logging.getLogger("gunicorn.access")
    gunicorn_access.disabled = True

# SET keepalive to zero or larger value than default to by pass or mitigate the STUCK on the second request
keepalive = 10000

# port
port: int = os.environ.get("PORT", 8080)


def get_worker_number() -> int:
    return min(ceil(os.cpu_count() / 8 * 3), 8)


def get_threads_number() -> int:
    return min(32, 4 * os.cpu_count())


def get_file_system(path: Path) -> str:
    res = subprocess.run(["df", path.as_posix(), "-h"], capture_output=True)
    if not res:
        raise ValueError(f"{path} not support df command")
    return res.stdout.decode("utf-8").split(os.linesep)[1].split()[0]


def is_tmpfs_dir(path: Path) -> bool:
    res = False
    try:
        if get_file_system(path) == "tmpfs":
            return True
    except ValueError:
        gunicorn_error_logger.error(f"get_file_system error", exc_info=True)
    return res


def get_tmpfs_dir():
    # refer https://docs.gunicorn.org/en/stable/faq.html#blocking-os-fchmod
    if os.name == "posix":
        candidate_dirs = [Path("/tmp"), Path("/dev/shm")]
        for candidate_dir in candidate_dirs:
            if is_tmpfs_dir(candidate_dir):
                return candidate_dir.as_posix()
    return None


# ----------------- Server Mechanics Related Config --------------------- #
# Load application code before the worker processes are forked.
preload_app = True
gunicorn_error_logger.error(f"Gunicorn Config: preload_app({preload_app})")
worker_tmp_dir = get_tmpfs_dir()
gunicorn_error_logger.error(f"Gunicorn Config: worker_tmp_dir({worker_tmp_dir})")


# ----------------- Server Socket Related Config --------------------- #
bind = [f"0.0.0.0:{port}"]
gunicorn_error_logger.error(f"Gunicorn Config: bind({bind})")

# ----------------- Worker Process Related Config --------------------- #
workers = get_worker_number()
gunicorn_error_logger.error(f"Gunicorn Config: workers({workers})")

if workers >= 2:
    max_requests = 1000
    gunicorn_error_logger.error(f"Gunicorn Config: max_requests({max_requests})")
    max_requests_jitter = min(ceil(workers / 4), 2)
    gunicorn_error_logger.error(f"Gunicorn Config: max_requests_jitter({max_requests_jitter})")

threads = get_threads_number()
gunicorn_error_logger.error(f"Gunicorn Config: threads({threads})")
# set worker_class
worker_class = "uvicorn.workers.UvicornWorker"

gunicorn_error_logger.error(f"Gunicorn Config: worker_class({worker_class})")
timeout = 300
gunicorn_error_logger.error(f"Gunicorn Config: timeout({timeout})")
