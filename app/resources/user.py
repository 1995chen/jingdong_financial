# -*- coding: utf-8 -*-


import inject
import template_logging
from flask import Blueprint
from flask_restful import Resource, reqparse
from template_rbac import AuthStore

from app.resources import Api
from app.dependencies import Auth
from app.schemas.test import TestSchema

logger = template_logging.getLogger(__name__)
auth: Auth = inject.instance(Auth)
test_schema: TestSchema = TestSchema()


class User(Resource):
    # http://www.pythondoc.com/Flask-RESTful/reqparse.html

    # 这里是公共参数定义
    common_parser = reqparse.RequestParser()

    @auth.auth(require_roles=[])
    def get(self) -> AuthStore:
        """
        获取用户登陆信息
        """
        # [继承公共参数]
        get_parser = self.common_parser.copy()
        # 拿到本次请求数据[这里会拿到所有数据]
        args = get_parser.parse_args()
        logger.info(f"args is {args}")
        auth_store: AuthStore = auth.get_auth_store()
        return auth_store


def get_resources():
    blueprint = Blueprint('User', __name__)
    api = Api(blueprint)
    api.add_resource(User, '/info')
    return blueprint
