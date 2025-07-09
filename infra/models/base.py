# -*- coding: utf-8 -*-


"""
model: orm base model
"""

from typing import Any, Dict

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase

from infra.models.mixin import ToDictMixin

__all__ = ["Base", "BaseModel"]


class Base(DeclarativeBase):  # type: ignore[misc]
    """ORM Base"""

    def model_to_dict(self) -> Dict[str, Any]:
        """
        orm model to dict
        """
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class BaseModel(Base, ToDictMixin):
    """
    base orm model
    """

    __abstract__ = True

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="primary key")
    create_user = Column(
        String(128), nullable=False, default="system", index=True, comment="create user"
    )
    update_user = Column(
        String(128),
        nullable=False,
        default="system",
        onupdate="system",
        index=True,
        comment="update user",
    )
    create_time = Column(
        DateTime, nullable=False, default=func.now(), comment="create time"  # pylint: disable=E1102
    )
    update_time = Column(
        DateTime,
        nullable=False,
        default=func.now(),  # pylint: disable=E1102
        onupdate=func.now(),  # pylint: disable=E1102
        comment="update time",
    )
    is_disabled = Column(
        Integer,
        nullable=False,
        default="0",
        index=True,
        comment="Is it disabled: Enable 1: Disable",
    )
