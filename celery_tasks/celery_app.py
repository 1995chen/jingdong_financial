# -*- coding: utf-8 -*-


"""
Celery app module
"""

import logging

import inject
from celery import Celery

logger = logging.getLogger(__name__)
celery_app: Celery = inject.instance(Celery)
