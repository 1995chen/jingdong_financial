# -*- coding: utf-8 -*-


"""
clash config task
"""


import base64
import logging
import os
from typing import Any, Dict, List
from urllib.parse import quote

import inject
import requests
import yaml
from bs4 import BeautifulSoup
from celery import Celery

from infra.dependencies import ClashSubscribeIetm, Config
from infra.utils.network import check_port, get_with_retry

logger = logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)


def get_direct_proxies(group_key: str, sub_url: str) -> List[Dict[str, Any]]:
    """
    get real proxies
    :param group_key: group name
    :param sub_url: subscribe url
    :return: proxies
    """
    config: Config = inject.instance(Config)
    if sub_url.startswith("http"):
        sub_url = quote(sub_url)
    transfer_url: str = (
        f"http://{config.CLASH_CONFIG.SUB_CONVERTER_HOST}:{config.CLASH_CONFIG.SUB_CONVERTER_PORT}"
        f"/sub?target=clash&new_name=true&url={sub_url}&insert=false"
    )
    success, response = get_with_retry(transfer_url, no_retry_codes=[422, 404])
    if response is None or not success:
        return []
    yaml_text: str = response.text
    yaml_text = yaml_text.replace("!<str> ", "")
    yaml_value = yaml.safe_load(yaml_text)
    # 拿到所有proxies的信息
    proxies: List[Dict[str, Any]] = []
    if "proxies" not in yaml_value or yaml_value["proxies"] is None:
        return proxies
    idx: int = 0
    for _i in yaml_value["proxies"]:
        _i["name"] = f"{group_key}_{idx}"
        proxies.append(_i)
        idx += 1
    return proxies


def get_base64_proxies(group_key: str, sub_url: str) -> List[Dict[str, Any]]:
    """
    get base64 proxies
    :param group_key: group name
    :param sub_url: subscribe url
    :return: proxies
    """
    config: Config = inject.instance(Config)
    # 定义proxies的信息
    proxies: List[Dict[str, Any]] = []
    # 拿到base64解析结果
    success, response = get_with_retry(sub_url, no_retry_codes=[422, 404])
    if response is None or not success:
        return []
    try:
        sub_lines = base64.b64decode(response.text).decode()
    except Exception:  # pylint: disable=W0718
        return []
    idx: int = 0
    for _u in sub_lines.split("\n"):
        if (
            not _u.startswith("ss://")
            and not _u.startswith("ssr://")
            and not _u.startswith("vmess://")
        ):
            continue
        # 逐行解析每一个的信息
        transfer_url: str = (
            f"http://{config.CLASH_CONFIG.SUB_CONVERTER_HOST}"
            f":{config.CLASH_CONFIG.SUB_CONVERTER_PORT}"
            f"/sub?target=clash&new_name=true&url={_u}&insert=false"
        )
        success, response = get_with_retry(transfer_url, no_retry_codes=[422, 404])
        if response is None or not success:
            continue
        yaml_text: str = response.text
        yaml_text = yaml_text.replace("!<str> ", "")
        yaml_value = yaml.safe_load(yaml_text)

        if "proxies" not in yaml_value or yaml_value["proxies"] is None:
            continue
        for _i in yaml_value["proxies"]:
            _i["name"] = f"{group_key}_{idx}"
            proxies.append(_i)
            idx += 1
    return proxies


def generate_subscribe_yaml(proxies: List[Dict[str, Any]]) -> None:
    """
    generate subscribe yaml
    :param proxies: proxies
    """
    config: Config = inject.instance(Config)
    config_workspace_path: str = os.path.join(config.PROJECT_PATH, "configs")
    template_path: str = os.path.join(config_workspace_path, "config.template")

    with open(template_path, "r", encoding="utf-8") as template_file:
        template_value = yaml.safe_load(template_file)
    # 添加到proxies
    template_value["proxies"].extend(proxies)
    # 添加到proxy-groups
    proxy_names: List[str] = [_i["name"] for _i in proxies]
    for _g in template_value["proxy-groups"]:
        if _g["name"] in {
            "🚀 节点选择",
            "♻️ 自动选择",
            "🐟 漏网之鱼",
        }:
            _g["proxies"].extend(proxy_names)
    # 写文件
    yaml_fp: str = os.path.join(config_workspace_path, "config.yaml")
    with open(yaml_fp, "w", encoding="utf-8") as fo:
        yaml.dump(template_value, fo, allow_unicode=True)


def get_from_github_free_ss(
    url: str = "https://github.com/Alvin9999/new-pac/wiki/ss%E5%85%8D%E8%B4%B9%E8%B4%A6%E5%8F%B7",
) -> List[str]:
    """
    get github free ssr proxies
    :param url:
    :return: subscribe urls
    """
    target_links = []
    try:
        _response = requests.get(
            url,
            timeout=10,
        )
        soup = BeautifulSoup(_response.text, "html.parser")
        target_links.extend([i.text.strip() for i in soup.find_all("pre")])
    except Exception:  # pylint: disable=W0718
        logger.info(f"failed to get ss link, url is {url}")
    return target_links


@celery_app.task(ignore_result=True, time_limit=600)
def sync_clash_config() -> None:
    """
    同步CLASH配置
    """
    logger.info("start run sync_clash_config....")
    # 获取配置
    config: Config = inject.instance(Config)
    subscribe_list: List[ClashSubscribeIetm] = []
    subscribe_list.extend(config.CLASH_CONFIG.SUBSCRIBE_LIST)
    # get link from github free ss
    github_free_links: List[str] = get_from_github_free_ss()
    for _idx, _link in enumerate(github_free_links):
        subscribe_list.append(
            ClashSubscribeIetm(GROUP=f"github_free_{_idx}", URL=_link, TYPE="direct")
        )
    full_proxies: List[Dict[str, Any]] = []
    for _i in subscribe_list:
        if _i.TYPE == "direct":
            full_proxies.extend(get_direct_proxies(_i.GROUP, _i.URL))
        if _i.TYPE == "base64":
            full_proxies.extend(get_base64_proxies(_i.GROUP, _i.URL))
        logger.info(f"query {_i.GROUP}/{_i.URL}, full proxies count is {len(full_proxies)}.")
    # check node valid
    full_proxies = [_i for _i in full_proxies if check_port(_i["server"], _i["port"])]
    # 将节点合并整合最终的配置
    generate_subscribe_yaml(full_proxies)
