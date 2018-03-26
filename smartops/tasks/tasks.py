import os, sys
import logging

from celery.signals import celeryd_init
from celery.signals import setup_logging

from smartops.actions import deploy
from smartops.db.handlers import database
from smartops.db.handlers import app as app_handler
from smartops.tasks.client import celery
#from smartops.utils import flags
from smartops.utils import logsetting
from smartops.utils import setting_wrapper as setting


@celery.task(name='smartops.tasks.deploy_app')
def deploy_app(app_id, entrypoint, blueprint, test_plan):
    try:
        deploy.deploy(app_id, entrypoint, blueprint, test_plan)
    except Exception as error:
        logging.exception(error)


@celery.task(name='smartops.tasks.deploy_capacity_planner')
def deploy_capacity_planner(app_id, entrypoint, blueprint, test_plan):
    try:
        deploy.deploy_capacity_planner(app_id, entrypoint, blueprint, test_plan)
    except Exception as error:
        logging.exception(error)
