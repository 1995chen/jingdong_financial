# -*- coding: utf-8 -*-


"""
utils: common utils
"""

import logging
import re
from typing import Any, Dict, Iterator, List

import jwt

from infra.constant import CODE_MAP
from infra.enums import StatusCode
from infra.exceptions import InvalidToken, InvalidTypeException
from infra.typing import T

logger = logging.getLogger(__name__)

__all__ = [
    "decode_token",
    "chunks",
    "make_json_response",
    "name_convert_to_camel",
    "name_convert_to_snake",
]


def decode_token(jwt_token: str, jwt_secret: str) -> Dict[str, Any]:
    """
    jwt token decode
    :param jwt_token:
    :param jwt_secret:
    :return:
    :raises InvalidTypeException: invalid type
    :raises InvalidTypeException: invalid type
    :raises InvalidToken: invalid token
    """
    if not isinstance(jwt_token, str):
        raise InvalidTypeException("jwt_token must be str")
    try:
        jwt_obj: Dict[str, Any] = jwt.decode(
            jwt_token, key=jwt_secret, verify=True, algorithms=["HS256"]
        )
    except (jwt.InvalidSignatureError,) as exc:
        logger.warning(f"invalid token: {jwt_token}", exc_info=True)
        raise InvalidToken(jwt_token) from exc
    except (Exception,) as exc:
        logger.error(f"decode token error: {jwt_token}", exc_info=True)
        raise InvalidToken(jwt_token) from exc
    return jwt_obj


def chunks(lis: List[T], n: int) -> Iterator[List[T]]:
    """
    Yield successive n-sized chunks from l.
    :param lis: list
    :param n: chunk size
    """
    assert isinstance(lis, list)
    for i in range(0, len(lis), n):
        yield lis[i : i + n]


def make_json_response(
    code: StatusCode = StatusCode.SUCCESS, data: Any = None, msg: Any = ""
) -> Dict[str, Any]:
    """
    build http json response
    :return: response dict
    """
    if not msg:
        msg = CODE_MAP.get(code) or ""
    return {
        "code": code.value,
        "data": data if data is not None else [],
        "msg": msg,
    }


def name_convert_to_camel(name: str) -> str:
    """
    Convert underscore to camel case
    :param name: input string
    :return: output string
    """
    contents = re.findall("_[a-z]+", name)
    for content in set(contents):
        name = name.replace(content, content[1:].title())
    return name


def name_convert_to_snake(name: str) -> str:
    """
    CamelCase to Underline
    :param name: input string
    :return: output string
    """
    if re.search(r"[^_][A-Z]", name):
        name = re.sub(r"([^_])([A-Z][a-z]+)", r"\1_\2", name)
        return name_convert_to_snake(name)
    return name.lower()
