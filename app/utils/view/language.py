# -*- coding: utf-8 -*-


from flask import request


def get_language() -> str:
    lang: str = request.accept_languages.best or 'zh-cn'
    if lang.lower() in ('zh-cn', 'zh'):
        lang = "zh_CN"
    else:
        lang = "en_US"
    return lang
