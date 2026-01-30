# -*- coding: utf-8 -*-

"""
youtube music module
"""

import copy
import logging
import os
import re
import shutil
import sys
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import ffmpeg
import inject
import requests
import yt_dlp
from downloader_cli.download import Download
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1
from mutagen.mp3 import MP3
from opencc import OpenCC
from synology_api.filestation import FileStation
from work_wechat import MsgType, TextCard, WorkWeChat
from ytmusicapi import YTMusic

from infra.dependencies import Config, YouTubeSubscribeConfig
from infra.models.bo.music import MetaInfo

logger = logging.getLogger(__name__)

ydl_opts = {
    "quiet": True,
    "no_warnings": True,
    "nocheckcertificate": True,
    "source_address": "0.0.0.0",
}
# 繁体转简体的库
opencc_instance = OpenCC("t2s")


class YouTubeMusic:
    """
    YouTubeMusic
    """

    def __init__(self) -> None:
        self.tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")

    @staticmethod
    def progress_handler(d: Dict[str, Any]) -> None:
        """
        进度条
        """
        d_obj = Download("", "")

        if d["status"] == "downloading":
            try:
                length = d_obj._get_terminal_length()  # pylint: disable=W0212
            except Exception:  # pylint: disable=W0718
                length = 120
            f_size_disp, dw_unit = d_obj._format_size(  # pylint: disable=W0212
                d["downloaded_bytes"]
            )

            # Total bytes might not be always passed, sometimes
            # total_bytes_estimate is passed
            try:
                total_bytes = d["total_bytes"]
            except KeyError:
                total_bytes = d["total_bytes_estimate"]

            percent = d["downloaded_bytes"] / total_bytes * 100
            speed, s_unit, time_left, time_unit = d_obj._get_speed_n_time(  # pylint: disable=W0212
                d["downloaded_bytes"], 0, cur_time=d["elapsed"] - 6
            )

            status = f"{round(f_size_disp)} {dw_unit}".ljust(7)
            if d["speed"] is not None:
                speed, s_unit = d_obj._format_speed(d["speed"] / 1000)  # pylint: disable=W0212
                status += f"| {round(speed)} {s_unit}".ljust(6 + len(s_unit))

            status += f"|| ETA: {round(time_left)} {time_unit}".ljust(11 + len(time_unit))

            status = d_obj._get_bar(status, length, percent)  # pylint: disable=W0212
            status += f"{round(percent)}%".ljust(4)

            sys.stdout.write("\r")
            sys.stdout.write(status)
            sys.stdout.flush()

    @staticmethod
    def convert_to_mp3(path: str) -> None:
        """
        Covert to mp3 using the python ffmpeg module.
        :param path: song path
        """
        new_path: str = path[:-4] + "_new.mp3"
        params = {"loglevel": "panic", "ar": 44100, "ac": 2, "ab": "320k", "f": "mp3"}
        try:
            job = ffmpeg.input(path).output(new_path, **params)
            job.run()
        except ffmpeg._run.Error:  # pylint: disable=W0212
            logger.warning("no need to convert mp3")
        finally:
            if os.path.exists(path):
                os.remove(path)
            if os.path.exists(new_path):
                shutil.move(new_path, path)

    @staticmethod
    def download_cover(artwork_url: str, dst_path: str) -> Optional[str]:
        """
        下载封面并存入相应目录
        """
        if not artwork_url:
            logger.warning(f"empty artwork_url: {artwork_url}")
            return None
        logger.info(f"prepare download cover: {artwork_url}")
        cover_img: str = os.path.join(dst_path, f"{uuid4()}.jpg")
        try:
            r = requests.get(artwork_url, timeout=60)
            # save file
            with open(cover_img, "wb") as f:
                f.write(r.content)
            return cover_img
        except Exception:  # pylint: disable=W0718
            # 清理目录
            if os.path.exists(cover_img):
                os.remove(cover_img)
            logger.warning(f"failed to download image: {artwork_url}", exc_info=True)
            return None

    @staticmethod
    def set_mp3_meta_data(song_meta: MetaInfo, song_path: str) -> None:
        """
        Set the song meta if the passed data is mp3.
        """
        cover_path: Optional[str] = ""
        try:
            audio = MP3(song_path, ID3=ID3)
            data = ID3(song_path)

            # download the cover image, if failed, pass
            cover_path = YouTubeMusic.download_cover(
                song_meta.artwork_url, os.path.dirname(song_path)
            )
            if cover_path:
                with open(cover_path, "rb") as f:
                    imagedata = f.read()
                data.add(APIC(3, "image/jpeg", 3, "Front cover", imagedata))

            # if tags are not present then add them
            try:
                audio.add_tags()
            except Exception:  # pylint: disable=W0718
                pass

            audio.save()

            logger.info(f"set song({song_meta.name}) meta: ")
            data.add(TIT2(encoding=3, text=song_meta.name))
            data.add(TPE1(encoding=3, text=song_meta.player_name))
            data.add(TALB(encoding=3, text=song_meta.album))

            data.save()

        except Exception:  # pylint: disable=W0718
            logger.warning(f"error set song meta {song_meta}", exc_info=True)
        finally:
            if cover_path and os.path.exists(cover_path):
                # remove the image
                os.remove(cover_path)

    @staticmethod
    def get_mp3_meta_info(video_id: str) -> MetaInfo:
        """
        get song meta by song name
        """
        ytmusic = YTMusic(language="zh_CN")
        details = ytmusic.get_song(videoId=video_id)

        # check if error occured
        if details["playabilityStatus"]["status"] != "OK":
            logger.warning(f"failed to get meta info: {video_id}")
            raise Exception(f"failed to get meta info: {video_id}")  # pylint: disable=W0719
        # 繁体字转换为简体
        return MetaInfo(
            name=opencc_instance.convert(details["videoDetails"]["title"]),
            album="",
            player_name=opencc_instance.convert(details["videoDetails"]["author"]),
            artwork_url=f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
            provider="youtube",
        )

    def download_playlist(self, subscribe_config: YouTubeSubscribeConfig) -> None:
        """
        download playlist
        :param subscribe_config: subscribe_config
        """
        # 获取配置
        config: Config = inject.instance(Config)
        wechat: WorkWeChat = inject.instance(WorkWeChat)
        file_station: FileStation = FileStation(
            ip_address=config.SYNOLOGY_CONFIG.SYNOLOGY_HOST,
            port=config.SYNOLOGY_CONFIG.SYNOLOGY_PORT,
            username=config.SYNOLOGY_CONFIG.SYNOLOGY_USERNAME,
            password=config.SYNOLOGY_CONFIG.SYNOLOGY_PASSWORD,
            secure=config.SYNOLOGY_CONFIG.SYNOLOGY_USE_SSL,
            cert_verify=config.SYNOLOGY_CONFIG.SYNOLOGY_CERT_VERIFY,
            dsm_version=config.SYNOLOGY_CONFIG.SYNOLOGY_DSM_VERSION,
        )
        try:
            # 获得播放列表
            ydl_opts_cp = copy.deepcopy(ydl_opts)
            ydl_opts_cp.update(
                {
                    "format": "bestaudio/best",
                    "dump_single_json": True,
                    "extract_flat": True,
                }
            )
            # extract the info now
            rsp = yt_dlp.YoutubeDL(ydl_opts_cp).extract_info(subscribe_config.PLAYLIST, False)
            playlist_name: str = rsp["title"]
            for _i in rsp["entries"]:
                try:
                    song_url: str = _i["url"].split("&")[0]
                    video_id: str = parse_qs(urlparse(url=song_url).query)["v"][0]
                    song_meta: MetaInfo = self.get_mp3_meta_info(video_id)
                    # 优化歌曲文件名[替换目录中不允许出现的字符]
                    rename_music_name: str = re.sub(r"[\/\\\:\*\?\"\<\>\|]", "_", song_meta.name)
                    # 检查文件是否存在
                    dst_file: str = os.path.join(subscribe_config.PATH, f"{rename_music_name}.mp3")
                    file_info = file_station.get_file_info(dst_file)
                    if file_info["data"]["files"][0].get("additional") and file_info["data"][
                        "files"
                    ][0]["additional"].get("real_path"):
                        logger.info(f"song({rename_music_name}) already exists, skip")
                        continue
                    logger.info(f"start download song: {song_meta.name}")
                    download_path: str = self.download_song(song_url, song_meta)
                    # 重命名文件
                    song_path: str = os.path.join(
                        os.path.dirname(download_path), f"{rename_music_name}.mp3"
                    )
                    shutil.move(download_path, song_path)
                    logger.info(f"finished download song: {song_meta.name}")
                    # 上传文件到群晖
                    upload_result = file_station.upload_file(subscribe_config.PATH, song_path)
                    if upload_result == "Upload Complete":
                        wechat.message_send(
                            agentid=config.WECHAT_WORK_CONFIG.MUSIC_AGENT_ID,
                            msgtype=MsgType.TEXTCARD,
                            touser=("@all",),
                            textcard=TextCard(
                                title="歌曲同步成功",
                                description=(
                                    f'播放列表: <div class="highlight">{playlist_name}</div>'
                                    f"歌曲名称: {song_meta.name}"
                                ),
                                url=song_url,
                            ),
                        )
                except Exception:  # pylint: disable=W0718
                    logger.warning(
                        f"failed to download song: {_i['title']}, url: {song_url}", exc_info=True
                    )
                finally:
                    # clean music cache dir
                    music_tmp: str = os.path.join(
                        self.tmp_dir,
                        "music",
                    )
                    shutil.rmtree(music_tmp, ignore_errors=True)
        except Exception:  # pylint: disable=W0718
            logger.error("download playlist error", exc_info=True)
        finally:
            # 注销登录
            file_station.logout()

    def download_song(self, url: str, song_meta: MetaInfo) -> str:
        """
        download song
        :param url: song url
        :param song_meta: song meta
        :return: song path
        """
        _song_name: str = str(uuid4()) + "." + "mp3"

        # The directory where we will download to.
        download_dir = os.path.join(self.tmp_dir, "music")
        logger.info(f"saving the files to: {download_dir}")

        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # name of the temp file
        _path = os.path.join(download_dir, _song_name)

        # start downloading the song
        ydl_opts_cp = copy.deepcopy(ydl_opts)
        ydl_opts_cp["outtmpl"] = _path
        ydl_opts_cp["format"] = "bestaudio/best"
        ydl_opts_cp["progress_hooks"] = [YouTubeMusic.progress_handler]
        ydl = yt_dlp.YoutubeDL(ydl_opts_cp)
        ydl.download([url])
        logger.info("Downloaded!")
        # convert to mp3
        YouTubeMusic.convert_to_mp3(_path)
        # set song meta
        YouTubeMusic.set_mp3_meta_data(song_meta, _path)
        return _path
