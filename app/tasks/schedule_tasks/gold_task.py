# -*- coding: utf-8 -*-


import json
from typing import Dict, Any, List, Optional, Tuple

import requests
import inject
import pymannkendall
import template_logging
from celery import Celery
from template_transaction import CommitContext
from redis_lock import Lock
from sqlalchemy import desc
from work_wechat import WorkWeChat, MsgType, TextCard

from app.dependencies import Config, MainDBSession, CacheRedis, Cache
from app.models import GoldPrice
from app.constants.enum import GoldPriceState

logger = template_logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)


@celery_app.task(ignore_result=True, time_limit=600)
def sync_gold_price():
    """
    同步黄金价格
    """
    # 获取配置
    config: Config = inject.instance(Config)

    jd_url: str = config.JD_FINANCE_API_URL
    headers: Dict[str, Any] = json.loads(config.JD_FINANCE_API_HEADERS)
    params: Dict[str, Any] = json.loads(config.JD_FINANCE_API_PARAMS)

    logger.info(f"prepare to call, url is {jd_url}, headers is {headers}, params is {params}")
    # 调用京东金融api
    query_response = requests.get(jd_url, headers=headers, params=params)

    if not query_response.ok:
        logger.warning(f"error to sync gold price, query_response is {query_response.text}")
        return
    response_data: Dict[str, Any] = query_response.json()
    # 接口错误打印日志
    if response_data['resultCode'] != 0:
        logger.warning(f"api error, response_data is {response_data}")
        return
    # 获取核心数据
    gold_price_info: Dict[str, Any] = response_data['resultData']['datas']
    # 保存数据
    session: MainDBSession = inject.instance(MainDBSession)

    gold_price_id: int = int(gold_price_info['id'])
    # 加分布式🔒, 并发插入id可能相同
    lock_key: str = f"sync-gold-price-lock:{config.PROJECT_NAME}-{config.RUNTIME_ENV}-{gold_price_id}"
    # 获取redis
    redis_cache: CacheRedis = inject.instance(CacheRedis)
    lock = Lock(redis_cache, lock_key)
    if lock.acquire(blocking=True, timeout=30):
        try:
            with CommitContext(session):
                gold_price: GoldPrice = session.query(GoldPrice).filter(
                    GoldPrice.id == gold_price_id
                ).first()
                if gold_price is not None:
                    logger.info(f"gold price-{gold_price_id} have already saved!")
                    return
                gold_price = GoldPrice()
                gold_price.id = gold_price_id
                gold_price.product_sku = gold_price_info['productSku']
                gold_price.demode = gold_price_info['demode']
                gold_price.price_num = gold_price_info['priceNum']
                gold_price.price = gold_price_info['price']
                gold_price.yesterday_price = gold_price_info['yesterdayPrice']
                gold_price.time = gold_price_info['time']
                session.add(gold_price)
                logger.info(f'current gold price is {gold_price.price} ..........')
        except Exception as e:
            logger.error(f"failed to do migrate", exc_info=True)
            raise e
        finally:
            # 释放🔒
            lock.release()

    logger.info(f'run sync_gold_price done')


def get_notify_cache_key(notify_key: GoldPriceState) -> str:
    """
    @param: notify_key 通知类型
    根据GoldPriceState返回本次通知缓存key
    """
    # 获取配置
    config: Config = inject.instance(Config)
    return f"{config.PROJECT_NAME}-{config.RUNTIME_ENV}-{notify_key}"


def skip_notify(notify_key: GoldPriceState) -> Tuple[bool, int]:
    """
    @param: notify_key 通知类型
    判断是否需要跳过本次通知
    """
    # 获取cache
    cache: Cache = inject.instance(Cache)
    # 获取配置
    config: Config = inject.instance(Config)
    cache_key: str = get_notify_cache_key(notify_key)
    # 获得重复推送次数
    _cache_bytes: Optional[bytes] = cache.get_cache(cache_key)
    _notify_times: int = int(_cache_bytes.decode()) if _cache_bytes else 0
    if _notify_times >= config.DUPLICATE_NOTIFY_TIMES:
        return True, _notify_times
    return False, _notify_times


def save_notify_times(notify_key: GoldPriceState, notify_times: int) -> None:
    """
    @param: notify_key 通知类型
    @param: notify_times 当前重复通知多少次
    保存重复通知次数
    """
    # 获取cache
    cache: Cache = inject.instance(Cache)
    # 获取配置
    config: Config = inject.instance(Config)
    cache_key: str = get_notify_cache_key(notify_key)
    cache.store_cache(cache_key, notify_times, config.DUPLICATE_NOTIFY_TIME_LIMIT)


@celery_app.task(ignore_result=True, time_limit=600)
def gold_price_remind():
    """
    黄金价格上涨提醒
    """
    # 获取配置
    config: Config = inject.instance(Config)
    wechat: WorkWeChat = inject.instance(WorkWeChat)

    # 查询数据
    session: MainDBSession = inject.instance(MainDBSession)
    with CommitContext(session):
        gold_price_ls: List[GoldPrice] = session.query(
            GoldPrice
        ).order_by(desc(GoldPrice.time)).limit(config.SAMPLE_COUNT).all()
    # 判断最近的一条价格是否到达设置目标价格
    if not gold_price_ls:
        logger.info(f'empty gold price data')
        return
    # 定义推送映射
    _notify_mapping: Dict[GoldPriceState, TextCard] = dict()
    # 金价超过目标价格
    if gold_price_ls[0].price >= config.RISE_TO_TARGET_PRICE:
        _notify_mapping[GoldPriceState.RISE_TO_TARGET_PRICE] = TextCard(
            title='黄金价格提醒',
            description=(
                f'当前金价: <div class="highlight">{gold_price_ls[0].price}</div>'
                f'达到目标价格: {config.RISE_TO_TARGET_PRICE}'
            ),
            url='https://m.jdjygold.com/finance-gold/msjgold/homepage?orderSource=7'
        )
    # 金价低于目标价格
    if gold_price_ls[0].price <= config.FALL_TO_TARGET_PRICE:
        _notify_mapping[GoldPriceState.FALL_TO_TARGET_PRICE] = TextCard(
            title='黄金价格提醒',
            description=(
                f'当前金价: <div class="gray">{gold_price_ls[0].price}</div>'
                f'达到目标价格: {config.FALL_TO_TARGET_PRICE}'
            ),
            url='https://m.jdjygold.com/finance-gold/msjgold/homepage?orderSource=7'
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
        if test_res.h and test_res.trend == 'increasing':
            min_price: float = min(price_values)
            # 计算在该样本内当前金额与最小金额的差值
            difference_price: float = price_values[0] - min_price
            # 计算百分比
            percent: float = round(
                100 * float(difference_price) / min_price,
                4
            )
            logger.info(f"金价趋势上涨 当前金价: {price_values[0]} 上涨金额: {round(difference_price, 2)} 上涨百分比: {percent}%")
            if difference_price >= config.TARGET_RISE_PRICE:
                _notify_mapping[GoldPriceState.REACH_TARGET_RISE_PRICE] = TextCard(
                    title='黄金价格上涨提醒',
                    description=(
                        f'当前金价: <div class="highlight">{round(price_values[0], 4)}</div>'
                        f'上涨金额: <div class="highlight">{round(difference_price, 4)}</div>'
                        f'上涨百分比: <div class="highlight">{percent}%</div>'
                        f'达到设定目标: {config.TARGET_RISE_PRICE}'
                    ),
                    url='https://m.jdjygold.com/finance-gold/msjgold/homepage?orderSource=7'
                )
        # 趋势下跌
        if test_res.h and test_res.trend == 'decreasing':
            max_price: float = max(price_values)
            # 计算在该样本内当前金额与最小金额的差值
            difference_price: float = price_values[0] - max_price
            # 计算百分比
            percent: float = round(
                100 * float(difference_price) / max_price,
                4
            )
            logger.info(f"金价趋势下跌 当前金价: {price_values[0]} 下跌金额: {round(difference_price, 2)} 下跌百分比: {percent}%")
            if abs(difference_price) >= config.TARGET_FALL_PRICE:
                _notify_mapping[GoldPriceState.REACH_TARGET_FALL_PRICE] = TextCard(
                    title='黄金价格下跌提醒',
                    description=(
                        f'当前金价: <div class="gray">{round(gold_price_ls[0].price, 4)}</div>'
                        f'下跌金额: <div class="gray">{round(difference_price, 4)}</div>'
                        f'下跌百分比: <div class="gray">{percent}%</div>'
                        f'达到设定目标: {config.TARGET_FALL_PRICE}'
                    ),
                    url='https://m.jdjygold.com/finance-gold/msjgold/homepage?orderSource=7'
                )

    # 准备推送
    for _state, _text_card in _notify_mapping.items():
        _skip, _notify_times = skip_notify(_state)
        if _skip:
            logger.info(f"skip notify, _notify_times is {_notify_times}")
            continue
        _notify_times = _notify_times + 1
        wechat.message_send(
            agentid=config.AGENT_ID,
            msgtype=MsgType.TEXTCARD,
            touser=('@all',),
            textcard=_text_card
        )
        save_notify_times(_state, _notify_times)
    logger.info(f'run gold_price_remind done')
