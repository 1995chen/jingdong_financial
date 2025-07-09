# -*- coding: UTF-8 -*-


"""
dependencies: auth component
"""

import contextvars
import functools
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from infra.exceptions import (
    AuthenticationFailed,
    HandlerNotCallableException,
    InvalidTypeException,
    NotFoundException,
    NotImplementedException,
    PermissionDenied,
)
from infra.utils import decode_token

__all__ = [
    "RequestStore",
    "AuthStore",
    "Auth",
    "get_auth_by_config",
    "AuthConfig",
]
logger = logging.getLogger(__name__)
# Define context to store http request object data
request_store: contextvars.ContextVar[Optional["RequestStore"]] = contextvars.ContextVar(
    "request_store"
)


# do not check snake_case naming style
# pylint: disable=C0103,R0902
@dataclass
class AuthConfig:
    """
    grpc auth config
    """

    # jwt token timeout
    JWT_EXPIRE_TIME: int = 86400
    # jwt token secret key
    JWT_SECRET_KEY: str = ""


@dataclass
class RequestStore:
    """
    http request info model
    """

    client_ip: str = ""
    base_url: str = ""
    url: str = ""
    method: str = ""
    header: str = ""
    body: bytes = b""
    path_params: Dict[str, Any] = field(default_factory=lambda: {})
    query_params: Dict[str, Any] = field(default_factory=lambda: {})


@dataclass
class AuthStore:
    """
    auth info model
    """

    # token
    token: str
    # jwt object
    jwt_obj: Dict[str, Any]
    # user info
    user_info: Any


class Auth:
    """
    Auth dependencies
    support role based permission check
    """

    def __init__(self, config: AuthConfig, auth_role: bool = False):
        """
        init method
        :param config:
        """
        self.jwt_secret = config.JWT_SECRET_KEY
        self.jwt_expire_time = config.JWT_EXPIRE_TIME
        self.auth_role = auth_role
        # Store tokens and decouple from frameworks
        self.registry = threading.local()
        # Get the user role handler
        self.get_user_roles_handler: Optional[Callable[[Any], List[str]]] = None
        # User-defined verification handler
        self.user_define_validator_handler: Optional[Callable[[Any, Dict[str, Any]], Any]] = None
        # Handler for getting user information
        self.get_user_info_handler: Optional[Callable[[Dict[str, Any]], Any]] = None

    def set_get_user_roles_handler(self, handler: Callable[[Any], List[str]]) -> None:
        """
        set handler: this handler support get user roles
        :raises HandlerNotCallableException: handler not callable
        """
        if not callable(handler):
            raise HandlerNotCallableException(f"{type(self).__name__}.set_get_user_roles_handler")
        self.get_user_roles_handler = handler

    def set_user_define_validator_handler(self, handler: Callable) -> None:
        """
        set handler: this handler support user define validator
        :raises HandlerNotCallableException: handler not callable
        """
        if not callable(handler):
            raise HandlerNotCallableException(
                f"{type(self).__name__}.set_user_define_validator_handler"
            )
        self.user_define_validator_handler = handler

    def set_get_user_info_handler(self, handler: Callable[[Dict[str, Any]], Any]) -> None:
        """
        set handler: this handler support get user info
        :raises HandlerNotCallableException: handler not callable
        """
        if not callable(handler):
            raise HandlerNotCallableException(f"{type(self).__name__}.set_get_user_info_handler")
        self.get_user_info_handler = handler

    def __get_user_roles(self, user_info: Any, **kwargs: Optional[Any]) -> List[str]:
        """
        get user roles
        :param user_info: User details, which are obtained from get_user_info_handler
        :return:
        :raises NotImplementedException: handler not implemented
        """
        if not callable(self.get_user_roles_handler):
            logger.error("NotImplementedException get_user_roles_handler")
            raise NotImplementedException("get_user_roles_handler")
        return self.get_user_roles_handler(user_info, **kwargs)

    def __get_user_info(self, jwt_obj: Dict[str, Any], **kwargs: Any) -> Any:
        """
        Returns the current user information
        :param jwt_obj: jwt dict
        :return:
        :raises NotImplementedException: handler not implemented
        """
        if not callable(self.get_user_info_handler):
            logger.error("NotImplementedException get_user_info_handler")
            raise NotImplementedException("get_user_info_handler")
        return self.get_user_info_handler(jwt_obj, **kwargs)

    def __do_user_define_valid(self, user_info: Any, jwt_obj: Dict[str, Any]) -> Any:
        """
        User-defined verification
        :param user_info: user info
        :param jwt_obj:
        :return:
        :raises NotImplementedException: handler not implemented
        """
        if not callable(self.user_define_validator_handler):
            logger.error("NotImplementedException user_define_validator_handler")
            raise NotImplementedException("user_define_validator_handler")
        return self.user_define_validator_handler(user_info, jwt_obj)

    def set_token(self, token: Optional[str]) -> None:
        """
        Set token, this operation is done in before request
        Used to determine whether the user is logged in and apply
        the user's custom verification method
        :param token: request jwt token
        :raises InvalidTypeException: invalid type
        """
        if token is None:
            self.registry.token = token
            return
        if not isinstance(token, str):
            raise InvalidTypeException("token must be str")
        self.registry.token = token

    def get_token(self) -> Optional[str]:
        """
        Get the stored thread local object
        :return: token str
        """
        return getattr(self.registry, "token", None)

    def set_request(self, request: RequestStore) -> None:
        """
        Set request, this operation is done in before request
        Used to save user request information
        :param request: RequestStore object
        :raises InvalidTypeException: invalid type
        """
        if not isinstance(request, RequestStore):
            raise InvalidTypeException("request object must be a instance of RequestStore")
        self.registry.request = request
        request_store.set(request)

    def get_request(self) -> Optional[RequestStore]:
        """
        get RequestStore
        :return: http request instance
        """
        return getattr(self.registry, "request", None) or request_store.get(None)

    def get_auth_store(self) -> Optional[AuthStore]:
        """
        get AuthStore
        """
        return getattr(self.registry, "auth_store", None)

    def raise_for_valid_token(self, **user_kwargs: Optional[Any]) -> None:
        """
        valid token
        :param user_kwargs: Additional custom parameters
        :raises AuthenticationFailed: auth failed
        :raises NotFoundException: user not found
        """
        token: Optional[str] = self.get_token()
        if not token:
            raise AuthenticationFailed()
        jwt_obj: Dict[str, Any] = decode_token(token, self.jwt_secret)
        user_info: Any = self.__get_user_info(jwt_obj, **user_kwargs)
        if user_info is None:
            logger.error("user not found, token is {token}")
            raise NotFoundException(f"user info not found, token is {token}")
        self.__do_user_define_valid(user_info, jwt_obj)
        _auth_store: AuthStore = AuthStore(token=token, jwt_obj=jwt_obj, user_info=user_info)
        self.registry.auth_store = _auth_store

    def auth(
        self, require_roles: Optional[List[str]] = None, **user_kwargs: Optional[Any]
    ) -> Callable:
        """
        Verify whether the current user meets the system role requirements of the API
        :param require_roles: Tuple/List, API required roles
        :param user_kwargs: Additional custom parameters
        :return:
        :raises AuthenticationFailed: authentication failed
        :raises NotFoundException: not found
        :raises InvalidTypeException: invalid type
        :raises PermissionDenied: no permission
        """

        def wrapper_outer(func: Callable) -> Any:
            @functools.wraps(func)
            def wrapper(*args: Optional[Any], **kwargs: Optional[Any]) -> Any:
                # Verification token
                self.raise_for_valid_token(**user_kwargs)
                # Do not verify role
                if not require_roles:
                    return func(*args, **kwargs)
                # Determine user_roles
                if not isinstance(require_roles, list):
                    raise InvalidTypeException("require_roles must be list")
                auth_store: Optional[AuthStore] = self.get_auth_store()
                if auth_store is None:
                    raise NotFoundException("empty auth_store")
                user_roles: List[str] = self.__get_user_roles(auth_store.user_info, **user_kwargs)
                if not isinstance(user_roles, list):
                    logger.error(
                        f"get_user_roles_handler must return a list, "
                        f"get {user_roles}, type {type(user_roles)}"
                    )
                    raise InvalidTypeException("user_roles must be list")
                if not self.auth_role or not require_roles:
                    return func(*args, **kwargs)
                cross_roles: Set[str] = set(user_roles) & set(require_roles)
                # Permissions not met
                if len(cross_roles) == 0:
                    raise PermissionDenied(
                        f"user_roles: {user_roles}, require_roles: {require_roles}"
                    )

                return func(*args, **kwargs)

            return wrapper

        return wrapper_outer

    def clear(self) -> None:
        """
        After the request is completed, you can call this method to clean up
        """
        if hasattr(self.registry, "auth_store"):
            del self.registry.auth_store
        if hasattr(self.registry, "token"):
            del self.registry.token
        if hasattr(self.registry, "request"):
            del self.registry.request
            request_store.set(None)


def get_auth_by_config(config: AuthConfig, auth_role: bool = False) -> Auth:
    """
    :param config:
    :param auth_role:
    :return: Auth instance
    """
    instance: Auth = Auth(config, auth_role=auth_role)
    return instance
