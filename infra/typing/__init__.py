# -*- coding: utf-8 -*-


"""
typing: typing module
"""

from typing import Any, Dict, TypeVar  # pylint: disable=cyclic-import

__all__ = [
    "T",
    "StrOrIntT",
    "DictStrAny",
    "ItemT",
]

# Generics T
T = TypeVar("T")
# str or int typing
StrOrIntT = TypeVar("StrOrIntT", int, str)
DictStrAny = Dict[str, Any]
ItemT = TypeVar("ItemT")
