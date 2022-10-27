# -*- coding: utf-8 -*-


from typing import Any

import template_logging
from flask import Blueprint
from flask_restful import Resource, reqparse

from app.resources import Api
from app.tasks.schedule_tasks.music_task import sync_play_list

logger = template_logging.getLogger(__name__)


class SyncPlayList(Resource):
    # http://www.pythondoc.com/Flask-RESTful/reqparse.html

    # 这里是公共参数定义
    common_parser = reqparse.RequestParser()

    def get(self) -> Any:
        """
        立即同步播放列表
        """
        sync_play_list.apply_async()
        return {'result': True, 'state': "success"}


def get_resources():
    blueprint = Blueprint('Music', __name__)
    api = Api(blueprint)
    api.add_resource(SyncPlayList, '/sync')
    return blueprint
