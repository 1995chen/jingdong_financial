# -*- coding: utf-8 -*-


"""
TraceId module
"""

import functools
import logging
from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Optional
from uuid import uuid4

import inject
from starlette.requests import Request

from infra.dependencies import Registry

logger = logging.getLogger(__name__)

__all__ = [
    "ITrace",
    "EventIdTrace",
]


class ITrace(metaclass=ABCMeta):
    """
    Support For DatadogTrace
    """

    @staticmethod
    @abstractmethod
    def trace_id(*args, **kwargs) -> str:  # type: ignore[no-untyped-def]
        """
        :param args:
        :param kwargs:
        :return: trace id
        """

    @classmethod
    def trace(cls, **user_kwargs: Optional[Any]) -> Callable[..., Any]:
        """
        trace decorator
        :param user_kwargs: Append custom parameters
        :return:
        """

        def wrapper_outer(func: Callable) -> Any:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:  # type: ignore[no-untyped-def]
                """
                :param args:
                :param kwargs:
                :return:
                """
                logger.debug(f"user_kwargs is {user_kwargs}.")
                # set trace id
                inject.instance(Registry).set_trace_id(cls.trace_id(*args, **kwargs))
                return func(*args, **kwargs)

            return wrapper

        return wrapper_outer


class EventIdTrace(ITrace):
    """
    subclass of ITrace
    """

    @staticmethod
    def trace_id(*args, **kwargs) -> str:  # type: ignore[no-untyped-def]
        """
        :param args:
        :param kwargs:
        :return:
        """
        trace_id: str = str(uuid4())
        if args and isinstance(args[0], Request) and args[0].headers.get("trace_id"):
            trace_id = args[0].headers.get("trace_id")
        return trace_id
