# -*- coding: utf-8 -*-


from typing import Optional

import inject
import template_logging
from template_pagination import Pagination
from sqlalchemy.orm import Query
from sqlalchemy import desc
from template_transaction import CommitContext

from app.models import GoldPrice
from app.dependencies import MainDBSession

logger = template_logging.getLogger(__name__)
pagination: Pagination = inject.instance(Pagination)

"""
Service 中不应该出现Schema
理想情况下所有涉及参数校验均应该在dataclass中的__post_init__方法内完成
"""


def get_current_price() -> Optional[GoldPrice]:
    """
    获得当前金价
    """
    session = inject.instance(MainDBSession)

    with CommitContext(session):
        gold_info: Optional[GoldPrice] = session.query(GoldPrice).order_by(desc(GoldPrice.time)).first()
        return gold_info


@pagination.with_paginate()
def get_latest_price() -> Query:
    """
    获得最近一段时间的黄金价格
    """
    session = inject.instance(MainDBSession)

    with CommitContext(session):
        query: Query = session.query(GoldPrice)
        return query
