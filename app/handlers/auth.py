# -*- coding: utf-8 -*-


import json
from typing import Dict, Any

import inject
import requests
import template_logging
from template_rbac import OAuth2SSO

from app.constants.auth import Role
from app.exceptions import AuthorizedFailException

logger = template_logging.getLogger(__name__)


def get_user_roles_handler(user_info: Any):
    logger.info(f"get_user_roles_handler, user_info is {user_info}")
    logger.warning("you may forget to implement handler: get_user_roles_handler")
    return [Role.Leader]


def user_define_validator_handler(user_info: Any, jwt_obj: Dict[str, Any]):
    # 检验jwt token
    if not jwt_obj or not jwt_obj.get('data') or not jwt_obj["data"].get('username'):
        raise AuthorizedFailException()
    # 校验数据的完整性
    if not user_info or not user_info.get('username'):
        raise AuthorizedFailException()
    if user_info['username'] != jwt_obj["data"]["username"]:
        raise AuthorizedFailException()


def get_user_info_handler(jwt_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
        从jwt字典中提取用户信息
    """
    access_token: str = jwt_obj["data"]["access_token"]
    oauth2_sso_instance: OAuth2SSO = inject.instance(OAuth2SSO)
    # 获得 用户信息[可加缓存]
    headers = {
        'Authorization': f"Bearer {access_token}",
    }
    resp = requests.post(oauth2_sso_instance.userinfo_endpoint, headers=headers, verify=False)
    resp_data: Dict[str, Any] = json.loads(resp.text)
    if 'preferred_username' not in resp_data:
        logger.error(f"failed to get userinfo: f{resp_data.get('error_description')}")
        raise AuthorizedFailException()
    # 整理用户信息
    user_info: Dict[str, Any] = {
        "user_id": resp_data["sub"],
        "email_verified": resp_data["email_verified"],
        "name": resp_data["name"],
        "username": resp_data["preferred_username"],
        "given_name": resp_data["given_name"],
        "family_name": resp_data["family_name"],
        "email": resp_data["email"],
    }
    logger.info(f"user_info is {user_info}")
    return user_info
