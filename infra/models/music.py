# -*- coding: utf-8 -*-


"""
model: music model
"""

from sqlalchemy import Column, String

from infra.models.base import BaseModel


class Music(BaseModel):
    """
    music
    """

    __tablename__ = "music"

    name = Column(String(64), nullable=False, default="", comment="music name")
    album = Column(String(64), nullable=False, default="", comment="album")
    player_name = Column(String(64), nullable=False, default="", comment="player name")
    play_list_name = Column(String(64), nullable=False, default="", comment="playlist name")
    artwork_url = Column(String(256), nullable=False, default="", comment="artwork url")
    file_name = Column(String(64), nullable=False, default="", comment="file name")
