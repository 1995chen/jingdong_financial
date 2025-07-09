# -*- coding: utf-8 -*-


"""
Test the fastapi basic api
Includes the following apis:
    /
    /health
"""

import logging
from urllib.parse import urljoin

import inject
from fastapi.testclient import TestClient

from api_server.fastapi_app import app
from infra.dependencies import Config
from infra.enums import StatusCode

client = TestClient(app)
config: Config = inject.instance(Config)
logger = logging.getLogger(__name__)


def test_app_info() -> None:
    """
    test api /
    """
    response = client.get(urljoin(f"{config.API_PREFIX}/v1/", ""))
    assert response.status_code == 200
    assert response.json()["PROJECT_NAME"] == config.PROJECT_NAME
    assert response.json()["SERVER_WORKER"] == config.SERVER_WORKER
    assert response.json()["SERVER_WORKER_THREAD"] == config.SERVER_WORKER_THREAD
    assert response.json()["API_PREFIX"] == config.API_PREFIX


def test_health_check_endpoint() -> None:
    """
    test api /health
    """
    response = client.get(urljoin(f"{config.API_PREFIX}/v1/", "health"))
    assert response.status_code == 200
    assert response.text == "OK"


def test_for_404() -> None:
    """
    test api 404
    """
    response = client.get("/not_found_api")
    assert response.status_code == 404
    assert response.json() == {
        "code": StatusCode.WEB_APP_ERROR.value,
        "data": [],
        "msg": "Not Found",
    }
