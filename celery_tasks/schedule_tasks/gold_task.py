# -*- coding: utf-8 -*-

"""
gold price sync task
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import inject
import pymannkendall
import requests
from celery import Celery
from redis_lock import Lock
from sqlalchemy import desc
from work_wechat import MsgType, TextCard, WorkWeChat

from infra.dependencies import Config, MainRDB, MainRedis
from infra.enums.gold import GoldPriceState
from infra.models import GoldPrice

logger = logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)


@celery_app.task(ignore_result=True, time_limit=600)
def sync_gold_price() -> None:
    """
    同步黄金价格
    """
    # 获取配置
    config: Config = inject.instance(Config)

    jd_url: str = config.GOLD_CONFIG.JD_FINANCE_API_URL
    headers: Dict[str, Any] = json.loads(config.GOLD_CONFIG.JD_FINANCE_API_HEADERS)
    params: Dict[str, Any] = json.loads(config.GOLD_CONFIG.JD_FINANCE_API_PARAMS)

    logger.info(f"prepare to call, url is {jd_url}, headers is {headers}, params is {params}")
    # 调用京东金融api
    query_response = requests.get(jd_url, headers=headers, params=params, timeout=60)

    if not query_response.ok:
        logger.warning(f"error to sync gold price, query_response is {query_response.text}")
        return
    response_data: Dict[str, Any] = query_response.json()
    # 接口错误打印日志
    if response_data["resultCode"] != 0:
        logger.warning(f"api error, response_data is {response_data}")
        return
    # 获取核心数据
    gold_price_info: Dict[str, Any] = response_data["resultData"]["datas"]
    gold_price_id: int = int(gold_price_info["id"])
    # 加分布式🔒, 并发插入id可能相同
    lock_key: str = f"sync-gold-price-lock:{config.PROJECT_NAME}-{config.ENV.value}-{gold_price_id}"
    # 获取redis
    redis_cache: MainRedis = inject.instance(MainRedis)
    lock = Lock(redis_cache, lock_key)
    if lock.acquire(blocking=True, timeout=30):
        try:
            with inject.instance(MainRDB).get_session() as session:
                gold_price: GoldPrice = (
                    session.query(GoldPrice).filter(GoldPrice.id == gold_price_id).first()
                )
                if gold_price is not None:
                    logger.info(f"gold price-{gold_price_id} have already saved!")
                    return
                gold_price = GoldPrice()
                gold_price.id = gold_price_id
                gold_price.product_sku = gold_price_info["productSku"]
                gold_price.demode = gold_price_info["demode"]
                gold_price.price_num = gold_price_info["priceNum"]
                gold_price.price = gold_price_info["price"]
                gold_price.yesterday_price = gold_price_info["yesterdayPrice"]
                gold_price.time = gold_price_info["time"]
                session.add(gold_price)
                session.commit()
                logger.info(f"current gold price is {gold_price.price} ..........")
        except Exception as e:
            logger.error("failed to do migrate", exc_info=True)
            raise e
        finally:
            # 释放🔒
            lock.release()

    logger.info("run sync_gold_price done")


def get_notify_cache_key(notify_key: GoldPriceState) -> str:
    """
    @param: notify_key 通知类型
    根据GoldPriceState返回本次通知缓存key
    """
    # 获取配置
    config: Config = inject.instance(Config)
    return f"{config.PROJECT_NAME}-{config.ENV.value}-{notify_key}"


def skip_notify(notify_key: GoldPriceState) -> Tuple[bool, int]:
    """
    @param: notify_key 通知类型
    判断是否需要跳过本次通知
    """
    # 获取cache
    redis_client: MainRedis = inject.instance(MainRedis)
    # 获取配置
    config: Config = inject.instance(Config)
    cache_key: str = get_notify_cache_key(notify_key)
    # 获得重复推送次数
    _cache_bytes: Optional[bytes] = redis_client.get(cache_key)
    _notify_times: int = int(_cache_bytes.decode()) if _cache_bytes else 0
    if _notify_times >= config.GOLD_CONFIG.DUPLICATE_NOTIFY_TIMES:
        return True, _notify_times
    return False, _notify_times


def save_notify_times(notify_key: GoldPriceState, notify_times: int) -> None:
    """
    @param: notify_key 通知类型
    @param: notify_times 当前重复通知多少次
    保存重复通知次数
    """
    # 获取cache
    redis_client: MainRedis = inject.instance(MainRedis)
    # 获取配置
    config: Config = inject.instance(Config)
    cache_key: str = get_notify_cache_key(notify_key)
    redis_client.set(cache_key, notify_times, config.GOLD_CONFIG.DUPLICATE_NOTIFY_TIME_LIMIT)


@celery_app.task(ignore_result=True, time_limit=600)
def gold_price_remind() -> None:
    """
    黄金价格上涨提醒
    """
    # 获取配置
    config: Config = inject.instance(Config)
    wechat: WorkWeChat = inject.instance(WorkWeChat)

    # 查询数据
    with inject.instance(MainRDB).get_session() as session:
        gold_price_ls: List[GoldPrice] = (
            session.query(GoldPrice)
            .order_by(desc(GoldPrice.time))
            .limit(config.GOLD_CONFIG.SAMPLE_COUNT)
            .all()
        )
    # 判断最近的一条价格是否到达设置目标价格
    if not gold_price_ls:
        logger.info("empty gold price data")
        return
    # 定义推送映射
    _notify_mapping: Dict[GoldPriceState, TextCard] = {}
    # 金价超过目标价格
    if gold_price_ls[0].price >= config.GOLD_CONFIG.RISE_TO_TARGET_PRICE:
        _notify_mapping[GoldPriceState.RISE_TO_TARGET_PRICE] = TextCard(
            title="黄金价格提醒",
            description=(
                f'当前金价: <div class="highlight">{gold_price_ls[0].price}</div>'
                f"达到目标价格: {config.GOLD_CONFIG.RISE_TO_TARGET_PRICE}"
            ),
            url="https://m.jdjygold.com/finance-gold/msjgold/homepage?orderSource=7",
        )
    # 金价低于目标价格
    if gold_price_ls[0].price <= config.GOLD_CONFIG.FALL_TO_TARGET_PRICE:
        _notify_mapping[GoldPriceState.FALL_TO_TARGET_PRICE] = TextCard(
            title="黄金价格提醒",
            description=(
                f'当前金价: <div class="gray">{gold_price_ls[0].price}</div>'
                f"达到目标价格: {config.GOLD_CONFIG.FALL_TO_TARGET_PRICE}"
            ),
            url="https://m.jdjygold.com/finance-gold/msjgold/homepage?orderSource=7",
        )
    # 仅一条数据,不计算涨跌幅
    if len(gold_price_ls) > 2:
        # 取出金额
        price_values: List[float] = [_i.price for _i in gold_price_ls]
        # 取数据时用的时间倒序,这里要反转数组[只取近期的20组数据进行趋势预测]
        time_sorted_asc = list(reversed(price_values))
        # 趋势测试
        test_res: Any = pymannkendall.original_test(time_sorted_asc)
        logger.info(f"test_res is {test_res}")
        # 趋势上涨
        if test_res.h and test_res.trend == "increasing":
            min_price: float = min(price_values)
            # 计算在该样本内当前金额与最小金额的差值
            difference_price: float = price_values[0] - min_price
            # 计算百分比
            percent: float = round(100 * float(difference_price) / min_price, 4)
            logger.info(
                f"金价趋势上涨 当前金价: {price_values[0]} 上涨金额: "
                f"{round(difference_price, 2)} 上涨百分比: {percent}%"
            )
            if difference_price >= config.GOLD_CONFIG.TARGET_RISE_PRICE:
                _notify_mapping[GoldPriceState.REACH_TARGET_RISE_PRICE] = TextCard(
                    title="黄金价格上涨提醒",
                    description=(
                        f'当前金价: <div class="highlight">{round(price_values[0], 4)}</div>'
                        f'上涨金额: <div class="highlight">{round(difference_price, 4)}</div>'
                        f'上涨百分比: <div class="highlight">{percent}%</div>'
                        f"达到设定目标: {config.GOLD_CONFIG.TARGET_RISE_PRICE}"
                    ),
                    url="https://m.jdjygold.com/finance-gold/msjgold/homepage?orderSource=7",
                )
        # 趋势下跌
        if test_res.h and test_res.trend == "decreasing":
            max_price: float = max(price_values)
            # 计算在该样本内当前金额与最小金额的差值
            difference_price = price_values[0] - max_price
            # 计算百分比
            percent = round(100 * float(difference_price) / max_price, 4)
            logger.info(
                f"金价趋势下跌 当前金价: {price_values[0]} 下跌金额: "
                f"{round(difference_price, 2)} 下跌百分比: {percent}%"
            )
            if abs(difference_price) >= config.GOLD_CONFIG.TARGET_FALL_PRICE:
                _notify_mapping[GoldPriceState.REACH_TARGET_FALL_PRICE] = TextCard(
                    title="黄金价格下跌提醒",
                    description=(
                        f'当前金价: <div class="gray">{round(gold_price_ls[0].price, 4)}</div>'
                        f'下跌金额: <div class="gray">{round(difference_price, 4)}</div>'
                        f'下跌百分比: <div class="gray">{percent}%</div>'
                        f"达到设定目标: {config.GOLD_CONFIG.TARGET_FALL_PRICE}"
                    ),
                    url="https://m.jdjygold.com/finance-gold/msjgold/homepage?orderSource=7",
                )

    # 准备推送
    for _state, _text_card in _notify_mapping.items():
        _skip, _notify_times = skip_notify(_state)
        if _skip:
            logger.info(f"skip notify, _notify_times is {_notify_times}")
            continue
        _notify_times = _notify_times + 1
        wechat.message_send(
            agentid=config.WECHAT_WORK_CONFIG.AGENT_ID,
            msgtype=MsgType.TEXTCARD,
            touser=("@all",),
            textcard=_text_card,
        )
        save_notify_times(_state, _notify_times)
    logger.info("run gold_price_remind done")
