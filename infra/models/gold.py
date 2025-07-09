# -*- coding: utf-8 -*-


"""
model: gold model
"""

from sqlalchemy import FLOAT, BigInteger, Boolean, Column, String

from infra.models.base import BaseModel


class GoldPrice(BaseModel):
    """
    gold price
    """

    __tablename__ = "gold_price"

    product_sku = Column(String(64), nullable=False, default="", comment="Product inventory unit")
    demode = Column(Boolean, nullable=False, default=False, comment="Downgrade")
    price_num = Column(String(256), nullable=False, default="", comment="price code")
    price = Column(FLOAT, nullable=False, default=0, comment="price")
    yesterday_price = Column(FLOAT, nullable=False, default=0, comment="Yesterday's closing price")
    time = Column(BigInteger, nullable=False, default=0, comment="milliseconds")
