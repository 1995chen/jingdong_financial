# -*- coding: utf-8 -*-


"""
dependencies: relational database component
"""

import importlib
import logging
from dataclasses import dataclass

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from infra.models.base import Base

logger = logging.getLogger(__name__)

__all__ = [
    "RDBConfig",
    "MainRDB",
    "get_main_rdb_by_config",
]


# do not check snake_case naming style
# pylint: disable=C0103,R0902
@dataclass
class RDBConfig:
    """
    mysql config
    """

    USERNAME: str = ""
    PASSWORD: str = ""
    HOST: str = ""
    DATABASE: str = ""
    PORT: int = 3306


class IDB:
    """
    Database interface
    """

    def __init__(self, engine: Engine):
        self.engine = engine
        self.Session = sessionmaker(bind=engine, class_=Session)

    def get_engine(self) -> Engine:
        """get engine object"""
        return self.engine

    def get_session(self) -> Session:
        """get session object"""
        return self.Session()

    def __call__(self) -> Session:
        """return session object"""
        return self.get_session()

    def generate_table(self) -> None:
        """
        create table
        """
        importlib.import_module("infra.models")
        Base.metadata.create_all(bind=self.engine)
        logger.info("generate_table success")


class MainRDB(IDB):
    """
    main database
    """


def get_main_rdb_by_config(config: RDBConfig) -> MainRDB:
    """
    :param config: RedisConfig instance
    :return: MainRedis instance
    """
    engine = create_engine(
        (
            f"mysql+pymysql://{config.USERNAME}:{config.PASSWORD}@"
            f"{config.HOST}:{config.PORT}/{config.DATABASE}"
        ),
        pool_recycle=3600,
        isolation_level="READ COMMITTED",
    )
    return MainRDB(engine)
