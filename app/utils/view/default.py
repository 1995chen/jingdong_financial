# -*- coding: utf-8 -*-


import os

import inject
from flask import send_from_directory

from app.dependencies import Config
from app.utils.view.response import page_not_found


def default_serve(path: str = ''):
    config: Config = inject.instance(Config)
    if path == '':
        # 根路径返回主模板
        return send_from_directory(config.FRONTEND_PATH, 'index.html', cache_timeout=0)
    elif path.startswith("api/"):
        return page_not_found(message="%s not found" % path)
    else:
        abs_path = os.path.join(config.FRONTEND_PATH, path)
        if not os.path.exists(abs_path):
            path = "index.html"
        return send_from_directory(config.FRONTEND_PATH, path, cache_timeout=0)
