# -*- coding: utf-8 -*-


import threading
import json
from typing import Optional
from dataclasses import dataclass, asdict

import inject
import template_logging
import template_exception
from flask import Request, Response
from werkzeug.exceptions import NotFound, BadRequest
from pymysql.constants import ER
from sqlalchemy.exc import DatabaseError
from template_rbac import AuthStore, Auth
from template_babel import get_text as _

from app.constants.code_map import CODE_MAP
from app.exceptions import ParamsInvalidException, ServerException, ClientException
from app.dependencies import MainDBSession
from app.utils.view import response

logger = template_logging.getLogger(__name__)


@dataclass
class HandlerStore:
    # 请求url
    url: str
    # 请求方式
    method: str
    # 请求
    args: str
    body: str


@dataclass
class RequestInfo(HandlerStore):
    # token
    token: str
    # 用户信息
    user_info: str


class GlobalErrorHandler:

    def __init__(self):
        self.registry = threading.local()

    def set_request(self, request: Request):
        # 获取信息
        body: str = json.dumps(request.json or request.form) if request.data else "null"
        handler_store: HandlerStore = HandlerStore(
            request.url, request.method, request.query_string.decode(), body,
        )
        self.registry.handler_store = handler_store

    def get_handler_store(self) -> Optional[HandlerStore]:
        return getattr(self.registry, 'handler_store', None)

    def get_request_info(self) -> str:
        """
        获取请求信息
        """
        auth: Auth = inject.instance(Auth)
        auth_store: AuthStore = auth.get_auth_store()
        token: str = auth_store.token if auth_store else 'null'
        user_info: str = json.dumps(auth_store.user_info) if auth_store else 'null'
        # 获得handler store
        handler_store: Optional[HandlerStore] = self.get_handler_store()
        # 本地request info
        request_info: RequestInfo = RequestInfo(
            handler_store.url, handler_store.method, handler_store.args, handler_store.body,
            token, user_info
        )
        return json.dumps(asdict(request_info))

    def clear(self):
        """
        清理
        """
        if hasattr(self.registry, 'handler_store'):
            del self.registry.handler_store

    @staticmethod
    def __handle_500(exception: Exception):
        """
        处理500错误
        :param exception:
        :return:
        """
        code: int = 5001
        if hasattr(exception, 'code') and exception.code:
            code = exception.code
        # response 500
        return response.exception(
            code=code,
            status=500,
            message=str(exception)
        )

    @staticmethod
    def __handle_401(exception: Exception):
        """
        处理401错误
        :param exception:
        :return:
        """
        code: int = 40104
        if hasattr(exception, 'code') and exception.code:
            code = exception.code
        # response 401
        return response.exception(
            code=code,
            status=401,
            message=str(exception)
        )

    @staticmethod
    def __handle_400(exception: Exception):
        """
        处理400错误
        :param exception:
        :return:
        """
        code: int = 4001
        if hasattr(exception, 'code') and exception.code:
            code = exception.code
        # response 400
        return response.exception(
            code=code,
            status=400,
            message=str(exception)
        )

    @staticmethod
    def __handle_404(exception: Exception):
        """
        处理404错误
        :param exception:
        :return:
        """
        # response 404
        return response.page_not_found(
            message=str(exception)
        )

    def __handler_database_error(self, exception: DatabaseError) -> Response:
        code, msg = exception.orig.args
        if code == ER.LOCK_DEADLOCK:
            return response.error(
                message=_('其它用户或系统正在操作，请稍后再试')
            )
        if code == ER.LOCK_WAIT_TIMEOUT:
            return response.error(
                message=_('获取数据库锁失败，其它用户或系统正在操作，请稍后再试')
            )
        if code == ER.DATA_TOO_LONG:
            return response.error(
                message=_('数据数据太长，超过了列的长度限制。具体报错：%s') % msg
            )
        if code == ER.TRUNCATED_WRONG_VALUE_FOR_FIELD:
            return response.error(
                message=_('提交了数据库不支持的字符。具体报错：%s') % msg
            )
        if code == ER.TABLE_EXISTS_ERROR:
            return response.error(
                message=_('该表已存在。具体报错：%s') % msg
            )
        if code == ER.DUP_ENTRY:
            return response.error(
                message=_('记录重复。具体报错：%s') % msg
            )
        if code == ER.INVALID_DEFAULT or code == ER.PARSE_ERROR:
            return response.error(
                message=_('建表时发生错误。具体报错：%s') % msg
            )
        if code == ER.BAD_FIELD_ERROR:
            return response.error(
                message=_('查询了不存在的列。具体报错：%s') % msg
            )
        if code == ER.NO_SUCH_TABLE:
            return response.error(
                message=_('表不存在。具体报错：%s') % msg
            )
        # 2006 mysql server has gone away, 2013 lost connection
        if code == 2006 or code == 2013:
            return response.error(
                message=_('数据库链接异常，请稍后再试。具体报错：%s') % msg
            )
        return self.__handle_500(exception)

    def __handler_sso_error(self, exception: template_exception.SSOException) -> Response:
        """
        处理SSO异常
        """
        code: int = exception.code or 40100
        # 默认返回信息
        message: str = str(CODE_MAP[40100])
        if isinstance(exception, template_exception.AuthorizedFailException):
            return response.error(code=code, message=message)
        if isinstance(exception, template_exception.UserResourceNotFoundException):
            return response.error(code=code, message=message)
        if isinstance(exception, template_exception.TokenInvalidException):
            return response.error(code=code, message=message)
        return self.__handle_401(exception)

    def global_api_error_handler(self, exception: Exception) -> Response:
        """
        这里捕获所有异常,handler内部按类型处理
        """
        # 忽略静态文件的异常
        if isinstance(exception, NotFound):
            return self.__handle_404(exception)
        logger.error(f"request info is {self.get_request_info()}", exc_info=True)
        # 认证相关异常
        if isinstance(exception, template_exception.SSOException):
            return self.__handler_sso_error(exception)
        # 参数校验不通过
        if isinstance(exception, ParamsInvalidException):
            code: int = exception.code if hasattr(exception, 'code') else 4001
            return response.error(code=code, message=exception.message)
        # 回滚主库
        session = inject.instance(MainDBSession)
        session.rollback()
        # 客户端异常
        if isinstance(exception, ClientException):
            code: int = exception.code if hasattr(exception, 'code') else 4001
            return response.error(code=code, message=str(exception))
        # 数据库异常
        if isinstance(exception, DatabaseError):
            return self.__handler_database_error(exception)
        # 服务器异常
        if isinstance(exception, ServerException):
            return self.__handle_500(exception)
        # 处理BadRequest
        if isinstance(exception, BadRequest):
            return self.__handle_400(exception)
        return self.__handle_500(exception)


global_error_handler: GlobalErrorHandler = GlobalErrorHandler()
