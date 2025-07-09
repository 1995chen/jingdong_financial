# -*- coding: utf-8 -*-


"""
gold service
"""

import logging
from typing import Any, Dict, List, Optional

import inject
from sqlalchemy import desc

from infra.dependencies import MainRDB
from infra.models import GoldPrice

logger = logging.getLogger(__name__)


def get_current_price() -> Optional[Dict[str, Any]]:
    """
    获得当前金价
    """
    with inject.instance(MainRDB).get_session() as session:
        gold_info: Optional[GoldPrice] = (
            session.query(GoldPrice).order_by(desc(GoldPrice.time)).first()
        )
        return gold_info.model_to_dict() if gold_info else {}


def get_latest_price() -> List[Dict[str, Any]]:
    """
    获得最近一段时间的黄金价格
    """

    with inject.instance(MainRDB).get_session() as session:
        return [
            _i.model_to_dict()
            for _i in session.query(GoldPrice).order_by(desc(GoldPrice.time)).limit(10)
        ]
