# -*- coding: utf-8 -*-


from typing import Any

import inject
import template_logging
from flask import Blueprint
from flask_restful import Resource, reqparse

from app.resources import Api
from app.dependencies import Config, bind

logger = template_logging.getLogger(__name__)


class ApplicationConfig(Resource):
    # http://www.pythondoc.com/Flask-RESTful/reqparse.html

    # 这里是公共参数定义
    common_parser = reqparse.RequestParser()

    def get(self) -> Any:
        """
        获取用户登陆信息
        """
        # [继承公共参数]
        get_parser = self.common_parser.copy()
        get_parser.add_argument('inner_call_uuid', type=str, default='', required=True)
        # 拿到本次请求数据[这里会拿到所有数据]
        args = get_parser.parse_args()
        logger.info(f"args is {args}")
        config: Config = inject.instance(Config)
        # 验证内部调用UID
        if args['inner_call_uuid'] != config.INNER_CALL_UID:
            return {
                'status': 'invalid inner_call_uid'
            }
        # 刷新配置
        logger.info(f"clear and configure inject")
        inject.clear_and_configure(bind, bind_in_runtime=False)

        return {
            'status': 'success'
        }


class ApplicationConfigInfo(Resource):
    # http://www.pythondoc.com/Flask-RESTful/reqparse.html

    # 这里是公共参数定义
    common_parser = reqparse.RequestParser()

    def get(self) -> Any:
        """
        获取用户登陆信息
        """
        config: Config = inject.instance(Config)
        return config


def get_resources():
    blueprint = Blueprint('Config', __name__)
    api = Api(blueprint)
    api.add_resource(ApplicationConfig, '/refresh')
    api.add_resource(ApplicationConfigInfo, '/info')
    return blueprint
