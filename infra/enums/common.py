# -*- coding: utf-8 -*-

"""
enums: common
"""

from enum import Enum, IntEnum


class Switch(IntEnum):
    """
    Switch
    """

    # Open
    Open = 1
    # Close
    Close = 0


class RuntimeEnv(Enum):
    """
    Production/Test Environment
    """

    # Prod
    PROD = "PROD"
    # Dev
    DEVELOPMENT = "DEVELOPMENT"
