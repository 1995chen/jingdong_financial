# -*- coding: utf-8 -*-


from sqlalchemy import Column, String

from app.models.base import BaseModel


class Test(BaseModel):
    __tablename__ = 'test'
    title = Column(String(64), nullable=False, unique=True, default='')
