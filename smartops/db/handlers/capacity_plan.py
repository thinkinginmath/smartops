import logging

from smartops.db.handlers import app as app_handler
from smartops.db.handlers import database
from smartops.db.handlers import utils
from smartops.db import exception
from smartops.db import models


def _get_capacity_plan(capacity_plan_id, session=None, **kwargs):
    if isinstance(capacity_plan_id, (int, long)):
        return utils.get_db_object(
            session, models.CapacityPlan, id=capacity_plan_id, **kwargs
        )
    raise exception.InvalidParameter(
        'Capacity Plan id %s type is not compatible' % capacity_plan_id
    )


@database.run_in_session()
def get_capacity_plan(capacity_plan_id, session=None):
    return _get_capacity_plan(
        capacity_plan_id, session=session
    )


@database.run_in_session()
def create_capacity_plan(app_id, session=None, **kwargs):
    app = app_handler._get_app(app_id, session=session)
    capacity_plan = utils.add_db_object(session, models.CapacityPlan, **kwargs)
    return utils.update_db_object(session, app, capacity_plan=capacity_plan)


@database.run_in_session()
def list_capacity_plans(app_id, session=None, **kwargs):
    return utils.list_db_objects(session, models.CapacityPlan, **kwargs)


@database.run_in_session()
def start_capacity_plan(app_id, session=None, **kwargs):
    capacity_plan = 1
    return
