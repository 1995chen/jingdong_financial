# -*- coding: utf-8 -*-


"""
    自定义异常类，与code_map配合使用
"""
from app.constants.code_map import CODE_MAP

__all__ = [
    'ClientException',
    'ServerException',
]


class CommonException(Exception):
    """自定义异常基类，禁止外部使用"""

    def __init__(self, message=''):
        super().__init__()
        self.code = None
        self.message = message

    def __str__(self):
        return str(self.message)


class ClientException(CommonException):
    """客户端错误"""

    def __init__(self, message=''):
        super().__init__()
        self.code = 40000
        self.message = message or CODE_MAP[self.code]


class ServerException(CommonException):
    """服务器端错误"""

    def __init__(self, message=''):
        super().__init__()
        self.code = 50000
        self.message = message or CODE_MAP[self.code]
