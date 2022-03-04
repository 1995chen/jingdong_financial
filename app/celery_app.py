# -*- coding: utf-8 -*-


import inject
import template_logging
from celery import Celery

logger = template_logging.getLogger(__name__)
celery_app = inject.instance(Celery)
