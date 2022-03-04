# -*- coding: utf-8 -*-


from app.exceptions.base import ClientException, ServerException
from app.exceptions.client import (
    ParamsTypeErrorException, ParamsInvalidException,
    KeyParamsMissingException, AuthorizedFailException
)

__all__ = [
    # 基础异常
    'ClientException',
    'ServerException',
    # 客户端异常
    'ParamsTypeErrorException',
    'ParamsInvalidException',
    'KeyParamsMissingException',
    # 认证异常
    'AuthorizedFailException',
]
