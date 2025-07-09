# -*- coding: utf-8 -*-


"""
youtube music bo
"""

from dataclasses import dataclass


__all__ = [
    "MetaInfo"
]


@dataclass
class MetaInfo:
    """
    meta info
    暂时不从IMetaService获取meta信息，因为不准，所以直接从youtube获取
    """

    # 歌曲名称
    name: str
    # 专辑
    album: str
    # 歌手
    player_name: str
    # 封面
    artwork_url: str
    # meta信息供应商
    provider: str
