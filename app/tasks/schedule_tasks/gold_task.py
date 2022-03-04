# -*- coding: utf-8 -*-


import json
from typing import Dict, Any

import requests
import inject
import template_logging
from celery import Celery
from template_transaction import CommitContext
from redis_lock import Lock

from app.dependencies import Config, MainDBSession, CacheRedis
from app.models import GoldPrice

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
        except Exception as e:
            logger.error(f"failed to do migrate", exc_info=True)
            raise e
        finally:
            # 释放🔒
            lock.release()

    logger.info(f'run sync_gold_price done')
