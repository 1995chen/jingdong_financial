# -*- coding: utf-8 -*-

"""
get meta interface
"""

import logging
from abc import ABCMeta, abstractmethod
from typing import List

import itunespy
import musicbrainzngs
import requests
from spotipy import Spotify, SpotifyClientCredentials

from infra.models.bo.music import MetaInfo

__all__ = [
    "MetaInfo",
]

logger = logging.getLogger(__name__)


class IMetaService(metaclass=ABCMeta):
    """
    meta service interface
    """

    @property
    @abstractmethod
    def provider(self) -> str:
        """
        get provider
        :return: provider
        """

    @abstractmethod
    def get_meta(self, song_name: str) -> List[MetaInfo]:
        """
        get meta
        :param song_name: song name
        :return: provider
        """


class DeezerMetaService(IMetaService):
    """
    DeezerMetaService
    """

    @property
    def provider(self) -> str:
        return "deezer"

    def get_meta(self, song_name: str) -> List[MetaInfo]:
        meta_list: List[MetaInfo] = []
        base_url: str = "https://api.deezer.com/search?q={}"
        url = base_url.format(song_name)
        r = requests.get(url, timeout=60)
        data = r.json()

        for _i in data["data"]:
            meta_list.append(
                MetaInfo(
                    name=_i["title_short"],
                    album=_i["album"]["title"],
                    player_name=_i["artist"]["name"],
                    artwork_url=_i["album"]["cover_medium"],
                    provider=self.provider,
                )
            )
        return meta_list


class GaanaMetaService(IMetaService):
    """
    GaanaMetaService
    """

    @property
    def provider(self) -> str:
        return "gaana"

    def get_meta(self, song_name: str) -> List[MetaInfo]:
        """
        get meta
        :param song_name: song name
        :return: provider
        """
        meta_list: List[MetaInfo] = []
        base_url: str = (
            "http://api.gaana.com/?type=search&subtype=search_song&"
            "key={}&token=b2e6d7fbc136547a940516e9b77e5990&format=JSON"
        )
        url = base_url.format(song_name)
        r = requests.get(url, timeout=60)
        data = r.json()

        for _i in data["tracks"]:
            meta_list.append(
                MetaInfo(
                    name=_i["track_title"],
                    album=_i["album_title"],
                    player_name=_i["artist"][0]["name"],
                    artwork_url=_i["artwork_large"],
                    provider=self.provider,
                )
            )
        return meta_list


class LastFMMetaService(IMetaService):
    """
    LastFMMetaService
    """

    @property
    def provider(self) -> str:
        return "lastfm"

    def get_meta(self, song_name: str) -> List[MetaInfo]:
        meta_list: List[MetaInfo] = []
        headers = {"User-Agent": "ytmdl"}
        payload = {
            "api_key": "865e60e7cf58e028c063cb1230c95e5e",
            "method": "track.search",
            "track": song_name,
            "format": "json",
        }
        url: str = "http://ws.audioscrobbler.com/2.0/"
        r = requests.get(url, headers=headers, params=payload, timeout=60)
        data = r.json()

        for _i in data["results"]["trackmatches"]["track"]:
            meta_list.append(
                MetaInfo(
                    name=_i["name"],
                    album="",
                    player_name=_i["artist"],
                    artwork_url=_i["image"][-1]["#text"],
                    provider=self.provider,
                )
            )
        return meta_list


class ItunesMetaService(IMetaService):
    """
    ItunesMetaService
    """

    @property
    def provider(self) -> str:
        return "itunes"

    def get_meta(self, song_name: str) -> List[MetaInfo]:
        meta_list: List[MetaInfo] = []
        data = itunespy.search_track(song_name, country="US")

        for _i in data:
            meta_list.append(
                MetaInfo(
                    name=_i.trackName,
                    album=_i.collectionName,
                    player_name=_i.artistName,
                    artwork_url=_i.artworkUrl100,
                    provider=self.provider,
                )
            )
        return meta_list


class MusicbrainzMetaService(IMetaService):
    """
    MusicbrainzMetaService
    """

    @property
    def provider(self) -> str:
        return "musicbrainz"

    def get_meta(self, song_name: str) -> List[MetaInfo]:
        meta_list: List[MetaInfo] = []
        musicbrainzngs.set_useragent("ytmdl", "2022.03.16", "https://github.com/deepjyoti30/ytmdl")
        data = musicbrainzngs.search_recordings(song_name)
        for _i in data["recording-list"]:
            meta_list.append(
                MetaInfo(
                    name=_i["title"],
                    album=_i["release-list"][0]["title"],
                    player_name=_i["artist-credit"][0]["name"],
                    artwork_url="",
                    provider=self.provider,
                )
            )
        return meta_list


class SpotifyMetaService(IMetaService):
    """
    SpotifyMetaService
    """

    @property
    def provider(self) -> str:
        return "spotify"

    def get_meta(self, song_name: str) -> List[MetaInfo]:
        meta_list: List[MetaInfo] = []
        spotify = Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id="a166f23a5637429e8bd819df46fa034e",
                client_secret="bbad17df3cde471ab969f081f2ea8bbb",
            )
        )

        data = spotify.search(f"track:{song_name}", limit=25, type="track", market="US")
        for _i in data["tracks"]["items"]:
            meta_list.append(
                MetaInfo(
                    name=_i["name"],
                    album=_i["album"]["name"],
                    player_name=_i["artists"][0]["name"],
                    artwork_url=_i["album"]["images"][0]["url"],
                    provider=self.provider,
                )
            )
        return meta_list
