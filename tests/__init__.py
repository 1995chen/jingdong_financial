# -*- coding: utf-8 -*-

"""
test: test module
"""

import os

# set config path
os.environ["CONFIG_PATH"] = os.path.join(
    os.path.dirname(os.path.abspath(os.path.realpath(__file__))), "test_data"
)
# set env
os.environ["ENV_FOR_DYNACONF"] = "development"
