# -*- coding: utf-8 -*-


from typing import Optional, Tuple

import inject
from flask import Flask, request
from flask_compress import Compress

import template_logging
from template_rbac import Auth, OAuth2SSO
from template_babel import TemplateBabel
from template_pagination import Pagination
from template_json_encoder import TemplateJSONEncoder

from app.dependencies import MainDBSession, Config
from app.utils.view.default import default_serve
from app.utils.view.response import simple_response
from app.utils.view.language import get_language
from app.handlers.error_handler import global_error_handler

from app.resources import (
    test,
    user,
    config,
    gold,
    music,
)

logger = template_logging.getLogger(__name__)

# 获得auth
auth: Auth = inject.instance(Auth)
babel_cfg: TemplateBabel = inject.instance(TemplateBabel)
pagination: Pagination = inject.instance(Pagination)


def bind_app_hook(app):
    """
    绑定请求前后钩子
    :param app: Flask App实例
    :return:
    """

    @app.before_request
    def before_request():
        """
        每次请求前，校验身份与IP地址
        :return:
        """
        # 注入token
        token: Optional[str] = request.headers.get("Authorization") or request.args.get("token")
        auth.set_token(token)
        # 存储本地请求
        global_error_handler.set_request(request)
        # 设置语言
        babel_cfg.set_lang(get_language())

    @app.after_request
    def cors_after_request(resp):
        resp.headers.set('Access-Control-Allow-Origin', '*')
        resp.headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        resp.headers.set('Access-Control-Allow-Headers',
                         'Response-Language, Content-Type, Cache-Control, Authorization, X-Requested-With')
        return resp

    @app.teardown_request
    def flask_teardown(_exception):
        config_instance: Config = inject.instance(Config)
        # [静态文件]跳过
        if not request.path.startswith(config_instance.API_PREFIX):
            return
        del _exception
        inject.instance(MainDBSession).remove()
        # 清理操作
        prepare_to_clean: Tuple = (
            global_error_handler, auth, babel_cfg, pagination
        )
        for _func in prepare_to_clean:
            _func.clear()
        del prepare_to_clean


def bind_api(app):
    # 注册路由表
    blueprints = (
        test.get_resources(),
        user.get_resources(),
        config.get_resources(),
        gold.get_resources(),
        music.get_resources(),
    )
    for bp in blueprints:
        app.register_blueprint(bp)
    # 绑定认证地址
    oauth2_sso: OAuth2SSO = inject.instance(OAuth2SSO)
    # 绑定资源
    app.register_blueprint(oauth2_sso.get_resources())
    app.register_error_handler(Exception, global_error_handler.global_api_error_handler)
    app.url_map.strict_slashes = False
    # 静态文件
    app.add_url_rule("/", endpoint="root_path", view_func=default_serve, methods=('get',))
    app.add_url_rule("/<path:path>", view_func=default_serve, methods=('get',))


def bind_app_health_check_endpoint(app):
    """
    绑定健康检查api
    :param app: Flask App实例
    :return:
    """

    @app.route('/api/health', methods=['GET'])
    def health_info():
        # 返回各个组件的健康状况
        return simple_response({
            'mysql': True,
            'redis': True,
        })


def create_app() -> Flask:
    app = Flask(__name__)
    Compress(app)

    app.config["RESTFUL_JSON"] = {"cls": TemplateJSONEncoder}
    app.json_encoder = TemplateJSONEncoder

    # 绑定全局异常处理器、请求前后钩子、默认终端等
    bind_app_hook(app)
    bind_app_health_check_endpoint(app)
    # 绑定路由
    bind_api(app)
    return app


flask_app: Flask = create_app()
