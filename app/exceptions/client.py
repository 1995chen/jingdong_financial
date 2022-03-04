# -*- coding: utf-8 -*-


# 客户端错误
from app.exceptions.base import ClientException
from app.constants.code_map import CODE_MAP


class ParamsTypeErrorException(ClientException):
    """参数类型错误"""

    def __init__(self, name, param_type):
        super().__init__()
        self.code = 40001
        self.message = str(CODE_MAP[self.code]) % (name, param_type)


class ParamsInvalidException(ClientException):
    """不合法的参数"""

    def __init__(self, errors):
        super().__init__()
        self.code = 40002
        error_text = ''
        for key, value in errors.items():
            error_text += '%s: %s;' % (key, value)
        self.message = str(CODE_MAP[self.code]) % error_text


class KeyParamsMissingException(ClientException):
    """缺少必要参数"""

    def __init__(self, name):
        super().__init__()
        self.code = 40003
        self.message = str(CODE_MAP[self.code]) % name


class AuthorizedFailException(ClientException):
    """身份验证失败"""

    def __init__(self):
        super().__init__()
        self.code = 40100
        self.message = CODE_MAP[self.code]
