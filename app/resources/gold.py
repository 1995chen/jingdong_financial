# -*- coding: utf-8 -*-


from typing import Any, Optional

import template_logging
from flask import Blueprint
from flask_restful import Resource, reqparse

from app.resources import Api
from app.models import GoldPrice
from app.services.gold import get_latest_price, get_current_price

logger = template_logging.getLogger(__name__)


class GoldPriceInfoList(Resource):
    # http://www.pythondoc.com/Flask-RESTful/reqparse.html

    # 这里是公共参数定义
    common_parser = reqparse.RequestParser()

    def get(self) -> Any:
        """
        获取用户登陆信息
        """
        return get_latest_price()


class GoldPriceInfo(Resource):
    # http://www.pythondoc.com/Flask-RESTful/reqparse.html

    # 这里是公共参数定义
    common_parser = reqparse.RequestParser()

    def get(self) -> Optional[GoldPrice]:
        """
        获取用户登陆信息
        """
        return get_current_price()


def get_resources():
    blueprint = Blueprint('GoldPrice', __name__)
    api = Api(blueprint)
    api.add_resource(GoldPriceInfoList, '/list')
    api.add_resource(GoldPriceInfo, '/latest')
    return blueprint
