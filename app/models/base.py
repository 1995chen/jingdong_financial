# -*- coding: utf-8 -*-


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import func, Column, Integer, String, DateTime, BigInteger

from app.models.mixin import ToDictMixin

# 创建对象的基类:
Base = declarative_base()


class BaseModel(Base, ToDictMixin):
    __abstract__ = True

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键')
    create_user = Column(String(128), nullable=False, default='system', index=True, comment='创建用户')
    update_user = Column(String(128), nullable=False, default='system', onupdate='system', index=True, comment='更新用户')
    create_time = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')
    update_time = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment='修改时间')
    is_disabled = Column(Integer, nullable=False, default='0', index=True, comment='是否被禁用：启用 1：禁用')
