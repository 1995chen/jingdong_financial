# -*- coding: utf-8 -*-


import inject
import template_logging

from app import dependencies

logger = template_logging.getLogger(__name__)

inject.configure(dependencies.bind, bind_in_runtime=False)
