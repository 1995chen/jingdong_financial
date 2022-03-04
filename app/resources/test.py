# -*- coding: utf-8 -*-


from typing import Dict, Any

import inject
from flask import Blueprint
from flask_restful import Resource, reqparse

import template_logging
from template_babel import get_text as _

from app.resources import Api
from app.dependencies import Auth
from app.constants.auth import Role
from app.constants.code_map import CODE_MAP
from app.services.test import test_db, TestDbBO
from app.schemas.test import TestSchema

logger = template_logging.getLogger(__name__)
auth: Auth = inject.instance(Auth)
test_schema: TestSchema = TestSchema()


class Test(Resource):
    # http://www.pythondoc.com/Flask-RESTful/reqparse.html

    # 这里是公共参数定义
    common_parser = reqparse.RequestParser()
    # 在args中必须包含position参数[这里会做隐式的数据类型转换,转换失败会抛出异常]
    common_parser.add_argument('position', type=str, required=True, location='args', help='invalid param position')

    @auth.auth(require_roles=[])
    def get(self):
        # [继承公共参数]
        get_parser = self.common_parser.copy()
        get_parser.add_argument('head', type=str, default='', required=True, help='invalid param head')
        # 拿到本次请求数据[这里会拿到所有数据]
        args = get_parser.parse_args()
        # marshmallow 做数据高级校验[主要对数据的内容做校验,做一些正则校验啥的]
        # https://www.cameronmacleod.com/blog/better-validation-flask-marshmallow
        # 原则上Schema只应该出现在resource层,service及其他层不应该出现Schema[如果抛出异常会被handler处理, 这里可以不用管]
        schema_args: Dict[str, Any] = test_schema.load(args)
        logger.info(f"schema_args is {schema_args}")
        return test_db(TestDbBO(**schema_args))

    @auth.auth(require_roles=[Role.Leader])
    def post(self):
        return {'result': True, 'state': "success"}


class TestNoAuth(Resource):

    def get(self):
        # 这里模拟一个异常的发生
        raise Exception(_('sssss'))
        return {'result': True, 'state': CODE_MAP[20000]}


class TestPagination(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('position', type=str, default='')
        parser.add_argument('head', type=str, location='args', required=True, help='need param: head')
        args = parser.parse_args()
        return test_db(TestDbBO(**args))


def get_resources():
    blueprint = Blueprint('Test', __name__)
    api = Api(blueprint)
    api.add_resource(Test, '/use_auth')
    api.add_resource(TestNoAuth, '/use_no_auth')
    api.add_resource(TestPagination, '/use_pagination')
    return blueprint
