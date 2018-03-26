import logging

from smartops.db.handlers import database
from smartops.db.handlers import utils
from smartops.db import exception
from smartops.db import models


STATUS_RESP_FIELDS = [
    'id', 'status', 'message', 'severity'
]


def _get_status(status_id, session=None, **kwargs):
    if isinstance(status_id, (int, long)):
        return utils.get_db_object(session, models.Status, status_id, **kwargs)
    raise exception.InvalidParameter(
        'Status id %s type is not compatible' % status_id
    )


@database.run_in_session()
@utils.wrap_to_dict(STATUS_RESP_FIELDS)
def get_status_by_app_id(app_id, session=None):
    app = utils.get_db_object(
        session, models.App, id=app_id
    )
    try:
        status = app.status
    except Exception:
        raise exception.RecordDoesNotExist(
            'App %s does not exist or have attribute: status' % app_id
        )
    return status


@database.run_in_session()
def update_status_by_app_id(app_id, session=None, **kwargs):
    app = utils.get_db_object(
        session, models.App, id=app_id
    )
    try:
        status = app.status
    except Exception:
        raise exception.RecordDoesNotExist(
            'App %s does not exist or have attribute: status' % app_id
        )
    return utils.update_db_object(session, status, **kwargs)
