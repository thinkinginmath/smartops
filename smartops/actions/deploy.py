import logging

from smartops.actions import util
from smartops.db.handlers import app as app_handler
from smartops.deployment.deploy_manager import DeployManager
from smartops.deployment.deploy_manager import CapacityPlannerDeployManager


def deploy(app_id, entrypoint, blueprint, test_plan):
    with util.lock('serialized_action', timeout=1000) as lock:
        if not lock:
            raise Exception('Failed to acquire lock for deployment.')

        deploy_successful = True
        try:
            deploy_manager = DeployManager(
                app_id, entrypoint, blueprint, test_plan)
            logging.info('Created deploy manager for %s', app_id)
            deploy_manager.deploy()
        except Exception as error:
            logging.exception(error)
            deploy_successful = False

        if not deploy_successful:
            util.ActionHelper.update_staus(
                app_id, status='ERROR', message='Failed to deploy application.'
            )


def deploy_capacity_planner(app_id, entrypoint, blueprint, test_plan):
    with util.lock('serialized_action', timeout=1000) as lock:
        if not lock:
            raise Exception('Failed to acquire lock for deployment.')

        capacity_plan_blueprint = util.load_capacity_plan(
            app_id, entrypoint, blueprint, test_plan
        )
        deploy_successful = True
        try:
            deploy_manager = CapacityPlannerDeployManager(
                app_id, capacity_plan_blueprint
            )
            logging.info('Created capacity plan deploy manager for %s', app_id)
            deploy_manager.deploy()
        except Exception as error:
            logging.exception(error)
            deploy_successful = False

        if not deploy_successful:
            util.ActionHelper.update_status(
                app_id,
                status='ERROR',
                message='Failed to deploy capacity planner.'
            )
