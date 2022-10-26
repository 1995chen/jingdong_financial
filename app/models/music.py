# -*- coding: utf-8 -*-


from sqlalchemy import Column, String, Boolean, FLOAT, BigInteger

from app.models.base import BaseModel


class Music(BaseModel):
    """
    音乐表
    """
    __tablename__ = 'music'

    name = Column(String(64), nullable=False, default='', comment='音乐名称')
    album = Column(String(64), nullable=False, default='', comment='降级')
    player_name = Column(String(64), nullable=False, default='', comment='价格编码')
    play_list_name = Column(String(64), nullable=False, default='', comment='歌单')
    artwork_url = Column(String(256), nullable=False, default='', comment='封面')
    file_name = Column(String(64), nullable=False, default='', comment='文件名')
