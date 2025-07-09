# -*- coding: utf-8 -*-

"""
handlers: json encoder handler
"""

import dataclasses
import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from json import JSONEncoder
from typing import Any, Callable, Dict, List, Type

from celery.schedules import crontab
from numpy import ndarray

__all__ = [
    "JSONEncoderHandler",
]

logger = logging.getLogger(__name__)


class JSONEncoderHandler(JSONEncoder):
    """
    handler for json encoder
    """

    def default(self, o: Any) -> Any:
        """
        implement default method
        :param o: obj
        :return: any
        """
        try:
            if isinstance(o, (timedelta, datetime, date, uuid.UUID, crontab)):
                return str(o)
            if isinstance(o, Decimal):
                return float(o)
            if isinstance(o, Enum):
                return o.value
            if dataclasses.is_dataclass(o):
                return self._asdict(o)
            if hasattr(o, "to_dict") and callable(o.to_dict):
                return o.to_dict()
            if isinstance(o, ndarray):
                return o.tolist()
            iterable = iter(o)
        except TypeError:
            logger.warning(f"failed to transfer obj: {o}, use JSONEncoder.default()")
        else:
            return list(iterable)
        return JSONEncoder.default(self, o)

    def _asdict(self, obj: Any, *, dict_factory: Type = dict) -> Any:
        """
        for dataclass to dict
        :param obj: obj
        :param dict_factory: type
        :return: any
        :raises TypeError:  TypeError
        """
        # pylint: disable=W0212
        if not dataclasses._is_dataclass_instance(obj):  # type: ignore[attr-defined]
            raise TypeError("asdict() should be called on dataclass instances")
        return self._asdict_inner(obj, dict_factory)

    def _asdict_inner(self, obj: Any, dict_factory: Callable) -> Any:
        """
        for inner dataclass to dict
        :param obj: obj
        :param dict_factory: dict_factory
        :return: any
        """
        # pylint: disable=W0212
        if dataclasses._is_dataclass_instance(obj):  # type: ignore[attr-defined]
            list_result: List[Any] = []
            for f in dataclasses.fields(obj):
                value = self._asdict_inner(getattr(obj, f.name), dict_factory)
                list_result.append((f.name, value))
            return dict_factory(list_result)
        if isinstance(obj, tuple) and hasattr(obj, "_fields"):
            dict_result: Dict[Any, Any] = {}
            for index, key in enumerate(obj._fields):
                dict_result[key] = self._asdict_inner(obj[index], dict_factory)
            return dict_result
        if isinstance(obj, (list, tuple)):
            return type(obj)(self._asdict_inner(v, dict_factory) for v in obj)
        if isinstance(obj, dict):
            return type(obj)(
                (self._asdict_inner(k, dict_factory), self._asdict_inner(v, dict_factory))
                for k, v in obj.items()
            )
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            return obj.to_dict()
        return obj
