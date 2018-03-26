import logging
import simplejson as json
import sys
import redis

from contextlib import contextmanager

from jinja2 import Environment, FileSystemLoader
from smartops.db.handlers import app as app_handler
from smartops.utils import setting_wrapper as setting


@contextmanager
def lock(lock_name, blocking=True, timeout=10):
    """acquire a lock to do some actions.
    The lock is acquired by lock_name among the whole distributed
    systems.
    """
    redis_instance = redis.Redis(host='redis', port=6379, db=0)
    instance_lock = redis_instance.lock(lock_name, timeout=timeout)
    owned = False
    try:
        locked = instance_lock.acquire(blocking=blocking)
        if locked:
            owned = True
            logging.debug('acquired lock %s', lock_name)
            yield instance_lock
        else:
            logging.info('lock %s is already hold', lock_name)
            yield None

    except Exception as error:
        logging.info(
            'redis fails to acquire the lock %s', lock_name)
        logging.exception(error)
        yield None

    finally:
        if owned:
            instance_lock.acquired_until = 0
            instance_lock.release()
            logging.debug('released lock %s', lock_name)
        else:
            logging.debug('nothing to release %s', lock_name)


def generate_application_topology(app_id, entrypoint, blueprint, test_plan):
    return

def load_capacity_plan(app_id, entrypoint, blueprint, test_plan):
    plan_dir = setting.CAPACITY_PLAN_DIR
    plan_file = setting.CAPACITY_PLAN_FILE
    api_endpoint = setting.API_ENDPOINT
    j2_env = Environment(
        loader=FileSystemLoader(plan_dir),
        trim_blocks=True
    )
    json_str = j2_env.get_template(plan_file).render(
        capacity_planner_name='capacity_plan_%s' % app_id,
        api_endpoint=api_endpoint,
        application_topology=generate_application_topology(
            app_id, endpoint, blueprint, test_plan
        )
    )
    plan = json.loads(json_str)
    print '===========plan is %s' % plan
    sys.exit()
    return capacity_plan


class ActionHelper(object):

    @staticmethod
    def update_status(app_id, status, message):
        app = app_handler.update_app_status_by_id(
            app_id,
            status=status,
            message=message
        )
        return app
