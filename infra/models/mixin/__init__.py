# -*- coding: utf-8 -*-


"""
model: mixin model
"""

from datetime import datetime
from typing import Any, Dict

__all = ["ToDictMixin"]


class ToDictMixin:
    """
    convert model to dict
    """

    # do not use it directly
    def to_dict(self) -> Dict[str, Any]:
        """
        convert model to dict
        """
        res: Dict[str, Any] = {}
        if hasattr(self, "dict_keys"):
            keys = self.dict_keys
            for c in keys:
                v = getattr(self, c, None)
                if isinstance(v, datetime):
                    res.update({c: v.strftime("%Y-%m-%d %H:%M:%S")})
                else:
                    res.update({c: v})
        else:
            keys = getattr(getattr(self, "__table__"), "columns")
            for c in keys:
                v = getattr(self, c.name, None)
                if isinstance(v, datetime):
                    res.update({c.name: v.strftime("%Y-%m-%d %H:%M:%S")})
                else:
                    res.update({c.name: v})
        return res
