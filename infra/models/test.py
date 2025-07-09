# -*- coding: utf-8 -*-


"""
model: test model
"""

from sqlalchemy import Column, String

from infra.models.base import BaseModel


class Test(BaseModel):
    """
    test
    """

    __tablename__ = "test"
    title = Column(String(64), nullable=False, unique=True, default="")
