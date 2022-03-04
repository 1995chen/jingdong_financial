# -*- coding: utf-8 -*-


from typing import Dict, Any, Optional
import time
from functools import wraps
from urllib.parse import urljoin

import inject

import flask
import flask_restful
from werkzeug.wrappers import Response as ResponseBase
from werkzeug.exceptions import HTTPException
from marshmallow.exceptions import ValidationError
import template_logging
from template_rbac import AuthStore, Auth

from app.dependencies import Config
from app.utils.common import name_convert_to_snake
from app.constants.code_map import CODE_MAP
from app.exceptions.client import ParamsInvalidException

logger = template_logging.getLogger(__name__)


class Api(flask_restful.Api):
    def __init__(self, app=None):
        config: Config = inject.instance(Config)
        prefix: str = urljoin(
            urljoin(f"{config.API_PREFIX}/", 'v1/'),
            name_convert_to_snake(app.name)
        )
        super().__init__(app, prefix)

    def handle_error(self, origin_exception):
        """
        这里不做任何的异常处理,直接抛给全局handler统一处理
        """
        raise origin_exception

    def output(self, resource):
        """
        将API返回的数据统一输出
        """

        @wraps(resource)
        def wrapper(*args, **kwargs):
            try:
                resp = resource(*args, **kwargs)
            except ValidationError as origin_exception:
                # 对ValidationError进行处理
                raise ParamsInvalidException(origin_exception.messages)
            # 如果是一个Response则返回
            if isinstance(resp, ResponseBase):
                return resp
            data, code, headers = flask_restful.unpack(resp)

            if data is None:
                data = dict()
            # 返回成功的code
            app_code: int = 20000
            app_result: Dict[str, Any] = {
                'code': app_code,
                'message': str(CODE_MAP[app_code]),
                'data': data,
                'timestamp': int(time.time())
            }
            auth: Auth = inject.instance(Auth)
            auth_store: AuthStore = auth.get_auth_store()
            headers: Optional[str, Any] = None
            if auth_store:
                headers = {"token": auth_store.token}
            return self.make_response(app_result, code, headers=headers)

        wrapper.origin_func = resource
        return wrapper


def abort(http_status_code, **kwargs):
    """Raise a HTTPException for the given http_status_code. Attach any keyword
    arguments to the exception for later processing.
    """
    # noinspection PyUnresolvedReferences
    try:
        flask.abort(http_status_code)
    except HTTPException:
        # 使用自定义异常抛出
        _message: str = ''
        if kwargs.get('message'):
            _message = kwargs.get('message')
        raise ParamsInvalidException(_message)


# 替换abort方法
flask_restful.abort = abort
