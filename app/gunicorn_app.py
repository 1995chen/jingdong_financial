# -*- coding: utf-8 -*-


import gunicorn.app.base
import gunicorn.glogging


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    # 默认配置
    DEFAULT_CONFIG = {
        'workers': 1,
        'threads': 10,
        'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s',
    }

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def init(self, parser, opts, args):
        pass

    def load_config(self):
        for key, value in self.DEFAULT_CONFIG.items():
            key = key.lower()
            if key in self.cfg.settings:
                self.cfg.set(key, value)
        for key, value in self.options.items():
            key = key.lower()
            if key in self.cfg.settings:
                self.cfg.set(key, value)

    def load(self):
        return self.application


def run_http_server(app, options: dict):
    app = StandaloneApplication(app, options)
    app.run()
