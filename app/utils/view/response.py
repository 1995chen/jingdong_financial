# -*- coding: utf-8 -*-


import time
import json
import mimetypes
from typing import Optional, Any, Dict

import inject
from flask import Response, make_response, jsonify
from template_rbac import AuthStore, Auth

from app.constants.code_map import CODE_MAP

__all__ = [
    'success',
    'error',
    'exception',
    'page_not_found',
    'download_reponse',
    'simple_response',
]

mimetypes.add_type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx')


def __get_response_header() -> Optional[Dict[str, Any]]:
    auth: Auth = inject.instance(Auth)
    auth_store: AuthStore = auth.get_auth_store()
    headers: Optional[str, Any] = None
    if auth_store:
        headers = {"token": auth_store.token}
    return headers


def success(message: Optional[str] = None, data: Any = None, status: int = 200, code: int = 20000) -> Response:
    """
    函数体处理成功，请求流程正常结束
    """
    if data is None:
        data = dict()
    res = {
        'code': code,
        'message': message or str(CODE_MAP.get(code, 'Success')),
        'data': data,
        'timestamp': int(time.time())
    }
    return Response(json.dumps(res), status=status, headers=__get_response_header(), mimetype='application/json')


def error(message: Optional[str] = None, data: Any = None, status: int = 400, code: int = 40000) -> Response:
    """
    函数体捕获到已知客户端异常，请求流程由于缺失必要参数而无法继续执行
    """
    if data is None:
        data = dict()
    res = {
        'code': code,
        'message': message or str(CODE_MAP.get(code, 'Bad Request')),
        'data': data,
        'timestamp': int(time.time())
    }
    return Response(json.dumps(res), status=status, headers=__get_response_header(), mimetype='application/json')


def exception(message: Optional[str] = None, status: int = 500, code: int = 50000) -> Response:
    """
    函数体捕获到未知异常，请求流程未能正常结束
    """
    res = {
        'code': code,
        'message': message or str(CODE_MAP.get(code, 'Server Error')),
        'timestamp': int(time.time())
    }
    return Response(json.dumps(res), status=status, headers=__get_response_header(), mimetype='application/json')


def page_not_found(message: Optional[str] = None, data: Any = None, status: int = 404, code: int = 40400) -> Response:
    """
    函数体捕获到已知客户端异常，请求流程由于缺失必要参数而无法继续执行
    """
    if data is None:
        data = dict()
    res = {
        'code': code,
        'message': message or str(CODE_MAP.get(code, '404')),
        'data': data,
        'timestamp': int(time.time())
    }
    return Response(json.dumps(res), status=status, headers=__get_response_header(), mimetype='application/json')


def download_reponse(filename: str, payload: Optional[Dict[str, Any]]) -> Response:
    mt = mimetypes.guess_type(filename)[0]
    if not mt:
        return error(message='无法识别%s的mimetype' % filename)
    headers: Dict[str, Any] = __get_response_header() or dict()
    headers.update({
        'Content-Disposition': 'attachment; filename=%s' % filename
    })

    return Response(
        payload,
        status=200,
        headers=headers,
        mimetype=mt)


def simple_response(data: Any, status_code: Optional[int] = None) -> Response:
    """
    创建flask response
    """
    res = make_response(jsonify(data))
    if status_code is not None:
        res.status_code = status_code
    return res
