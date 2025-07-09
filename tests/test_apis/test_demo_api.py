# -*- coding: utf-8 -*-

"""
Test the fastapi basic api
Includes the following apis:
    /v1/hello
    /v2/hello
"""

import logging
from urllib.parse import urljoin

import inject
from fastapi.testclient import TestClient

from api_server.fastapi_app import app
from infra.dependencies import Config

client = TestClient(app)
config: Config = inject.instance(Config)
logger = logging.getLogger(__name__)


def test_v1_hello() -> None:
    """
    test api /v1/hello
    """
    response = client.get(urljoin(f"{config.API_PREFIX}/", "v1/demo/hello"))
    assert response.status_code == 200
    assert response.text == "OK"


def test_v2_hello() -> None:
    """
    test api /v2/hello
    """
    response = client.get(urljoin(f"{config.API_PREFIX}/", "v2/demo/hello"))
    assert response.status_code == 200
    assert response.text == "OK"


def test_pydantic_test() -> None:
    """
    test api /v1/test/pydantic/{item_id}
    """
    response = client.get(urljoin(f"{config.API_PREFIX}/", "v1/demo/test/pydantic/123"))
    assert response.status_code == 200
    assert response.json() == {"code": 0, "data": {"item_id": 123}, "msg": "success"}
