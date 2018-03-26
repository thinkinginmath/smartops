import logging

from smartops.db.handlers import app as app_handler
from smartops.db.handlers import app_status as status_handler
from smartops.db.handlers import database
from smartops.db.handlers import utils
from smartops.db import exception
from smartops.db import models


SLA_RESP_FIELDS = [
    'id', 'latency', 'error_rate', 'app_id'
]


def _get_sla(sla_id, session=None, **kwargs):
    if isinstance(sla_id, (int, long)):
        return utils.get_db_object(session, models.Sla, id=sla_id, **kwargs)
    raise exception.InvalidParameter(
        'SLA id %s type is not compatible' % sla_id
    )


@database.run_in_session()
@utils.wrap_to_dict(SLA_RESP_FIELDS)
def get_sla_by_app_id(app_id, session=None):
    app = app_handler._get_app(app_id, session=session)
    try:
        sla = app.sla
    except Exception:
        raise exception.RecordDoesNotExist(
            'App %s does not exist or app does not have sla attribute' % app_id
        )
    return sla


@database.run_in_session()
@utils.wrap_to_dict(SLA_RESP_FIELDS)
def update_sla_by_app_id(
    app_id, exception_when_existing=True,
    session=None, **kwargs
):
    cost = 100.0
    app = app_handler._get_app(app_id, session=session)
    sla = app.sla
    try:
        error_rate = float(kwargs['sla']['error_rate'])
        latency = int(kwargs['sla']['latency'])
    except Exception:
        raise exception.InvalidParameter(
            'Parameter missing in your request'
        )
    if not sla:
        sla = utils.add_db_object(
            session, models.AppSla, exception_when_existing,
            error_rate, latency, cost, app_id
        )
    else:
        sla = utils.update_db_object(
            session, sla, error_rate=error_rate, latency=latency
        )
    print '---------------------------'
    status_handler.update_status_by_app_id(
        app_id,
        session=session,
        status='CREATING_STEP_1',
        message='Finished posting app SLA',
        severity='INFO'
    )
    return sla
