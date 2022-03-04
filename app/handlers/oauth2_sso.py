# -*- coding: utf-8 -*-


import time
import json
import base64
from typing import Dict, Any

import inject
import template_logging
from template_rbac import ITokenInfo
from template_exception import AuthorizedFailException

logger = template_logging.getLogger(__name__)


def oauth2_sso_generate_token_info_handler(access_token_info: Dict[str, Any]) -> ITokenInfo:
    """
    获取到token后调用
    """
    logger.info(f"access_token_info is {access_token_info}")
    access_token: str = access_token_info['access_token']
    refresh_token: str = access_token_info['refresh_token']
    user_info_bs64: str = access_token.split('.')[1]
    # 计算缺省的等号
    missing_padding = 4 - len(user_info_bs64) % 4
    # 补充缺省的等号
    if missing_padding:
        user_info_bs64 += '=' * missing_padding
    try:
        user_info_json: str = base64.b64decode(user_info_bs64).decode('utf-8')
        user_info: Dict[str, Any] = json.loads(user_info_json)
        logger.info('根据token信息获取用户信息是: %s ' % user_info)
    except Exception:
        logger.error(f"invalid access_token_info: {access_token_info}", exc_info=True)
        raise AuthorizedFailException("invalid access_token")

    now_ts = int(time.time())
    token_info: ITokenInfo = ITokenInfo(
        access_token=access_token,
        expires_at=now_ts + access_token_info['expires_in'] - 30,
        refresh_token=refresh_token,
        refresh_expires_at=now_ts + access_token_info['refresh_expires_in'] - 60,
        token_type=access_token_info['token_type'],
        user_id=user_info['sub'],
        username=user_info['preferred_username'],
        email=user_info['email'],
        name=user_info['name'],
        family_name=user_info['family_name'],
        given_name=user_info['given_name'],
    )
    return token_info


def before_redirect_handler(args: Dict[str, str]) -> None:
    """
    认证完成后, 重定向增加相应的参数到query string
    """
    logger.info(f"args is {args}")
    pass


def oauth2_sso_logout_handler() -> Any:
    """
    登出的handler
    """
    from template_rbac import AuthStore, Auth
    auth: Auth = inject.instance(Auth)
    auth_store: AuthStore = auth.get_auth_store()
    logger.info(f"auth_store is {auth_store}")
    logger.warning("you may forget to implement handler: logout_handler")
