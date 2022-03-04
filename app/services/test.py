# -*- coding: utf-8 -*-


from typing import Optional

import inject
import template_logging
from template_cache import Cache
from dataclasses import dataclass
from template_pagination import Pagination
from sqlalchemy.orm import Query
from template_rbac import Auth, AuthStore
from template_transaction import CommitContext

from app.models import Test
from app.dependencies import MainDBSession
from app.tasks.async_tasks.test_task import do_test

logger = template_logging.getLogger(__name__)
pagination: Pagination = inject.instance(Pagination)
cache: Cache = inject.instance(Cache)

"""
Service 中不应该出现Schema
理想情况下所有涉及参数校验均应该在dataclass中的__post_init__方法内完成
"""


@dataclass
class TestDbBO:
    """
    定义业务对象
    """
    position: str
    head: str

    def __post_init__(self):
        # 进行业务校验[比如查询数据库判断资源是否存在]
        pass


@cache.use_cache()
@pagination.with_paginate()
def test_db(bo: TestDbBO) -> Query:
    logger.info(f"bo is {bo}")
    session = inject.instance(MainDBSession)
    auth: Auth = inject.instance(Auth)
    auth_store: Optional[AuthStore] = auth.get_auth_store()
    logger.info(f"auth_store is {auth_store}")

    # 发送异步任务
    do_test.apply_async()
    with CommitContext(session):
        query: Query = session.query(Test)
        return query
