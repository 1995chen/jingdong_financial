# -*- coding: utf-8 -*-


import hashlib
import pickle
from typing import Any, Optional
from types import FunctionType

import inject
import template_logging

from app.dependencies import CacheRedis

logger = template_logging.getLogger(__name__)
redis_cache: CacheRedis = inject.instance(CacheRedis)


def get_cache_handler(key: str, timeout: Optional[int], **_user_kwargs: Any) -> Any:
    """
    获得缓存的handler
    """
    _value: Any = redis_cache.get(key)
    # 重置缓存时间
    if _user_kwargs.get('refresh_on_read', False) and timeout:
        redis_cache.expire(key, timeout)
    return _value


def store_cache_handler(key: str, value: Any, timeout: Optional[int], **_user_kwargs: Any) -> Any:
    """
    存储cache的handler
    """
    redis_cache.set(key, value, timeout)


def generate_cache_key_handler(func: FunctionType, *args: Any, **kwargs: Any) -> str:
    """
    根据方法以及方法的参数生成唯一key
    func: 方法
    args: 列表参数
    kwargs: 字典参数
    """
    param_bytes: bytes = pickle.dumps((args, kwargs))
    # key 过长优化
    cache_key: str = func.__module__ + '.' + func.__name__ + '.' + hashlib.md5(param_bytes).hexdigest()
    return cache_key
