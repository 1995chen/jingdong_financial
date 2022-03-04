# -*- coding: utf-8 -*-


from sqlalchemy import Column, String, Boolean, FLOAT, BigInteger

from app.models.base import BaseModel


class GoldPrice(BaseModel):
    """
    黄金价格表
    """
    __tablename__ = 'gold_price'

    product_sku = Column(String(64), nullable=False, default='', comment='产品库存量单位')
    demode = Column(Boolean, nullable=False, default=False, comment='降级')
    price_num = Column(String(256), nullable=False, default='', comment='价格编码')
    price = Column(FLOAT, nullable=False, default=0, comment='价格')
    yesterday_price = Column(FLOAT, nullable=False, default=0, comment='昨日收盘价格')
    time = Column(BigInteger, nullable=False, default=0, comment='时间毫秒')
