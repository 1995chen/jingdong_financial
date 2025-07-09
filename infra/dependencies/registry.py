# -*- coding: UTF-8 -*-

"""
dependency: registry component
"""

import contextvars
import logging
import threading
from typing import Optional

from infra.exceptions import InvalidTypeException

__all__ = [
    "Registry",
    "bind_registry",
]
logger = logging.getLogger(__name__)


class Registry:
    """
    Registry dependencies
    store context
    """

    def __init__(self) -> None:
        """
        init method
        """
        # store thread local objs
        self.local_registry = threading.local()
        # Define context to store http request object data
        self.trace_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
            "trace_id"
        )

    def set_trace_id(self, trace_id: str) -> None:
        """
        store trace id
        :param trace_id: trace id
        :raises InvalidTypeException: invalid type
        """
        if not isinstance(trace_id, str):
            raise InvalidTypeException("trace_id must be str")
        self.local_registry.trace_id = trace_id
        # store to context
        self.trace_id_context.set(trace_id)

    def get_trace_id(self) -> Optional[str]:
        """
        Get the stored thread local object
        :return: trace id
        """
        return getattr(self.local_registry, "trace_id", None) or self.trace_id_context.get(None)

    def clear(self) -> None:
        """
        clear after request end
        """
        if hasattr(self.local_registry, "trace_id"):
            del self.local_registry.trace_id
            self.trace_id_context.set(None)


def bind_registry() -> Registry:
    """
    :return: Registry instance
    """
    instance: Registry = Registry()
    return instance
