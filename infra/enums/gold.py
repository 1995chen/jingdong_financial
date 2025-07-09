# -*- coding: utf-8 -*-

"""
enums: gold
"""

from enum import Enum


class GoldPriceState(Enum):
    """
    GoldPriceState
    """

    # 金价涨到目标价格
    RISE_TO_TARGET_PRICE = "rise_to_target_price"
    # 金价跌到目标价格
    FALL_TO_TARGET_PRICE = "fall_to_target_price"
    # 金价上涨了目标价格
    REACH_TARGET_RISE_PRICE = "reach_target_rise_price"
    # 金价下跌了目标价格
    REACH_TARGET_FALL_PRICE = "reach_target_fall_price"
