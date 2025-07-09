# -*- coding: utf-8 -*-


"""
create & configure fastapi_app instance
"""

import logging
import os
from typing import Optional
from urllib.parse import urljoin

import inject
import psutil
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from api_server import resources as resources_api
from infra.dependencies import Config
from infra.enums import Switch
from infra.handlers.http.error import bind_app_exception_handler
from infra.middlewares import user_define_http_middleware

logger = logging.getLogger(__name__)
config: Config = inject.instance(Config)


def bind_middleware(application: FastAPI) -> None:
    """
    bind middleware
    :param application: FastAPI instance
    """

    # Cross-domain [When cross-domain is configured
    # in external nginx, the application side needs to turn off cross-domain]
    application.add_middleware(CORSMiddleware, allow_origins=["*"])
    # Customizing HTTP Middleware
    application.middleware("http")(user_define_http_middleware)


def bind_health_check_endpoint(application: FastAPI) -> None:
    """
    bind health check api
    :param application: FastAPI instance
    """

    @application.get(urljoin(f"{config.API_PREFIX}/v1/", "health"))
    def health_check() -> PlainTextResponse:
        logger.debug("get health_check request.")
        # returns the health status of each component
        return PlainTextResponse(b"OK")


def bind_app_info_endpoint(application: FastAPI) -> None:
    """
    Bind app default api
    :param application: FastAPI instance
    """

    @application.get(urljoin(f"{config.API_PREFIX}/v1/", ""))
    def app_info() -> ORJSONResponse:
        logger.debug("get app_info request.")
        # returns the health status of each component
        return ORJSONResponse(
            {
                "PROJECT_NAME": config.PROJECT_NAME,
                "SERVER_WORKER": config.SERVER_WORKER,
                "SERVER_WORKER_THREAD": config.SERVER_WORKER_THREAD,
                "API_PREFIX": config.API_PREFIX,
                "CPU_COUNT": os.cpu_count(),
                "CPU_PERCENT": psutil.cpu_percent(),
            }
        )


def bind_api(application: FastAPI) -> None:
    """
    bind router
    :param application: FastAPI instance
    """

    # health check endpoint
    bind_health_check_endpoint(application)
    # app info endpoint
    bind_app_info_endpoint(application)
    # bind resources api
    resources_api.bind_router(application)
    application.mount(
        "/static", StaticFiles(directory=config.STATIC_PATH, html=True), name="static"
    )


def create_app() -> FastAPI:
    """
    create app function, return fastapi_app instance
    :return:
    """
    docs_url: Optional[str] = None if config.OPEN_DOC == Switch.Close else "/docs"
    redoc_url: Optional[str] = None if config.OPEN_DOC == Switch.Close else "/redoc"
    _app = FastAPI(docs_url=docs_url, redoc_url=redoc_url)
    bind_middleware(_app)
    bind_api(_app)
    bind_app_exception_handler(_app)
    return _app


app: FastAPI = create_app()
