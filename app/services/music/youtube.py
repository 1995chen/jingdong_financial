# -*- coding: utf-8 -*-

"""
youtube music module
"""

import glob
import sys
import os
import copy
import shutil
from typing import Optional
from uuid import uuid4
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

import inject
import requests
import yt_dlp
import ffmpeg
from opencc import OpenCC
from mutagen.id3 import (
    ID3,
    APIC,
    TIT2,
    TPE1,
    TALB,
)
from mutagen.mp3 import MP3
from ytmusicapi import YTMusic
from downloader_cli.download import Download
from work_wechat import WorkWeChat, MsgType, TextCard
from synology_api.filestation import FileStation

import template_logging

from app.dependencies import Config

logger = template_logging.getLogger(__name__)

ydl_opts = {
    "quiet": True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'source_address': '0.0.0.0',
}
# 繁体转简体的库
opencc_instance = OpenCC('t2s')


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


class YouTubeMusic(object):

    def __init__(self):
        self.tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')

    @staticmethod
    def progress_handler(d):
        """
        进度条
        """
        d_obj = Download('', '')

        if d['status'] == 'downloading':
            try:
                length = d_obj._get_terminal_length()
            except Exception:
                length = 120
            f_size_disp, dw_unit = d_obj._format_size(d['downloaded_bytes'])

            # Total bytes might not be always passed, sometimes
            # total_bytes_estimate is passed
            try:
                total_bytes = d['total_bytes']
            except KeyError:
                total_bytes = d['total_bytes_estimate']

            percent = d['downloaded_bytes'] / total_bytes * 100
            speed, s_unit, time_left, time_unit = d_obj._get_speed_n_time(
                d['downloaded_bytes'],
                0,
                cur_time=d['elapsed'] - 6
            )

            status = r"%-7s" % ("%s %s" % (round(f_size_disp), dw_unit))
            if d['speed'] is not None:
                speed, s_unit = d_obj._format_speed(d['speed'] / 1000)
                status += r"| %-3s " % ("%s %s" % (round(speed), s_unit))

            status += r"|| ETA: %-4s " % (
                    "%s %s" %
                    (round(time_left), time_unit))

            status = d_obj._get_bar(status, length, percent)
            status += r" %-4s" % ("{}%".format(round(percent)))

            sys.stdout.write('\r')
            sys.stdout.write(status)
            sys.stdout.flush()

    @staticmethod
    def convert_to_mp3(path: str) -> None:
        """
        Covert to mp3 using the python ffmpeg module.
        :param path: song path
        """
        new_path: str = path[:-4] + '_new.mp3'
        params = {
            "loglevel": "panic",
            "ar": 44100,
            "ac": 2,
            "ab": '320k',
            "f": "mp3"
        }
        try:
            job = ffmpeg.input(path).output(
                new_path,
                **params
            )
            job.run()
        except ffmpeg._run.Error:
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
            raise Exception("empty artwork_url")
        logger.info(f"prepare download cover: {artwork_url}")
        cover_img: str = os.path.join(dst_path, f"{uuid4()}.jpg")
        try:
            r = requests.get(artwork_url)
            # save file
            with open(cover_img, 'wb') as f:
                f.write(r.content)
            return cover_img
        except Exception as e:
            # 清理目录
            if os.path.exists(cover_img):
                os.remove(cover_img)
            logger.warning(f"failed to download image: {artwork_url}", exc_info=True)
            raise e

    @staticmethod
    def set_mp3_meta_data(song_meta: MetaInfo, song_path: str) -> None:
        """
        Set the song meta if the passed data is mp3.
        """
        cover_path: str = ""
        try:
            audio = MP3(song_path, ID3=ID3)
            data = ID3(song_path)

            # download the cover image, if failed, pass
            cover_path = YouTubeMusic.download_cover(song_meta.artwork_url, os.path.dirname(song_path))
            if cover_path:
                imagedata = open(cover_path, 'rb').read()
                data.add(APIC(3, 'image/jpeg', 3, 'Front cover', imagedata))

            # if tags are not present then add them
            try:
                audio.add_tags()
            except Exception:
                pass

            audio.save()

            logger.info(f"set song({song_meta.name}) meta: ")
            data.add(TIT2(encoding=3, text=song_meta.name))
            data.add(TPE1(encoding=3, text=song_meta.player_name))
            data.add(TALB(encoding=3, text=song_meta.album))

            data.save()

        except Exception:
            logger.error(f"error set song meta {song_meta}", exc_info=True)
        finally:
            if cover_path and os.path.exists(cover_path):
                # remove the image
                os.remove(cover_path)

    @staticmethod
    def get_mp3_meta_info(video_id: str) -> MetaInfo:
        """
        get song meta by song name
        """
        ytmusic = YTMusic(language='zh_CN')
        details = ytmusic.get_song(videoId=video_id)

        # check if error occured
        if details["playabilityStatus"]["status"] != "OK":
            logger.warning(f"failed to get meta info: {video_id}")
            raise Exception(f"failed to get meta info: {video_id}")
        # 繁体字转换为简体
        return MetaInfo(
            name=opencc_instance.convert(details["videoDetails"]["title"]),
            album='',
            player_name=opencc_instance.convert(details["videoDetails"]["author"]),
            artwork_url=f'https://i.ytimg.com/vi/{video_id}/sddefault.jpg',
            provider="youtube",
        )

    def download_playlist(self, url: str) -> None:
        """
        download playlist
        :param url: playlist url
        """
        # 获取配置
        config: Config = inject.instance(Config)
        wechat: WorkWeChat = inject.instance(WorkWeChat)
        file_station: FileStation = FileStation(
            ip_address=config.SYNOLOGY_HOST,
            port=config.SYNOLOGY_PORT,
            username=config.SYNOLOGY_USERNAME,
            password=config.SYNOLOGY_PASSWORD,
            secure=config.SYNOLOGY_USE_SSL,
            cert_verify=config.SYNOLOGY_CERT_VERIFY,
            dsm_version=config.SYNOLOGY_DSM_VERSION,
        )
        try:
            # 获得播放列表
            ydl_opts_cp = copy.deepcopy(ydl_opts)
            ydl_opts_cp.update({
                'format': 'bestaudio/best',
                'dump_single_json': True,
                'extract_flat': True,
            })
            # extract the info now
            rsp = yt_dlp.YoutubeDL(ydl_opts_cp).extract_info(url, False)
            playlist_name: str = rsp["title"]
            for _i in rsp["entries"]:
                try:
                    song_url: str = _i["url"].split("&")[0]
                    video_id: str = parse_qs(urlparse(url=song_url).query)["v"][0]
                    song_meta: MetaInfo = self.get_mp3_meta_info(video_id)
                    # 检查文件是否存在
                    dst_file: str = os.path.join(
                        config.SYNOLOGY_MUSIC_DIR,
                        f"{song_meta.name}.mp3"
                    )
                    file_info = file_station.get_file_info(dst_file)
                    if (
                            file_info['data']['files'][0].get('additional') and
                            file_info['data']['files'][0]['additional'].get('real_path')
                    ):
                        logger.info(f"song({song_meta.name}) already exists, skip")
                        continue
                    logger.info(f"start download song: {song_meta.name}")
                    download_path: str = self.download_song(song_url, song_meta)
                    # 重命名文件
                    song_path: str = os.path.join(
                        os.path.dirname(download_path),
                        f"{song_meta.name}.mp3"
                    )
                    shutil.move(download_path, song_path)
                    logger.info(f"finished download song: {song_meta.name}")
                    # 上传文件到群晖
                    upload_result = file_station.upload_file(config.SYNOLOGY_MUSIC_DIR, song_path)
                    if upload_result == "Upload Complete":
                        wechat.message_send(
                            agentid=config.AGENT_ID,
                            msgtype=MsgType.TEXTCARD,
                            touser=('@all',),
                            textcard=TextCard(
                                title='歌曲同步成功',
                                description=(
                                    f'播放列表: <div class="highlight">{playlist_name}</div>'
                                    f'歌曲名称: {song_meta.name}'
                                ),
                                url=song_url,
                            )
                        )
                except Exception:
                    logger.warning(f"failed to download song: {_i['title']}", exc_info=True)
                finally:
                    # clean music cache dir
                    music_tmp: str = os.path.join(
                        self.tmp_dir,
                        'music',
                    )
                    shutil.rmtree(music_tmp, ignore_errors=True)
        except Exception:
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
        _song_name: str = str(uuid4()) + '.' + "mp3"

        # The directory where we will download to.
        download_dir = os.path.join(self.tmp_dir, 'music')
        logger.info("saving the files to: {}".format(download_dir))

        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # name of the temp file
        _path = os.path.join(download_dir, _song_name)

        # start downloading the song
        ydl_opts_cp = copy.deepcopy(ydl_opts)
        ydl_opts_cp['outtmpl'] = _path
        ydl_opts_cp['format'] = 'bestaudio/best'
        ydl_opts_cp['progress_hooks'] = [YouTubeMusic.progress_handler]
        ydl = yt_dlp.YoutubeDL(ydl_opts_cp)
        ydl.download([url])
        logger.info('Downloaded!')
        # convert to mp3
        YouTubeMusic.convert_to_mp3(_path)
        # set song meta
        YouTubeMusic.set_mp3_meta_data(song_meta, _path)
        return _path
