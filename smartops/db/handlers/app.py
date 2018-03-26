import logging

from smartops.db.handlers import app_status as status_handler
from smartops.db.handlers import database
from smartops.db.handlers import utils
from smartops.db import exception
from smartops.db import models
from smartops.tasks import client as celery_client


APP_SUPPORTED_FIELDS = [
    'name', 'entrypoint', 'test_plan'
]
APP_CREATING_REQUIRED_FIELDS = [
    'name'
]
APP_IGNORED_FIELDS = [
    'id', 'created_at', 'updated_at'
]
APP_RESP_FIELDS = [
    'id', 'name', 'entrypoint', 'created_at',
    'updated_at', 'blueprint', 'test_plan',
    'status', 'containers', 'pods', 'services',
    'error'
]
APP_TEST_FIELDS = [
    'url', 'load'
]


def _get_app(app_id, session=None, **kwargs):
    if isinstance(app_id, (int, long)):
        return utils.get_db_object(
            session, models.App, id=app_id, **kwargs
        )
    raise exception.InvalidParameter(
        'App id %s type is not compatible' % app_id
    )


def _is_app_editable(app):
    if app.status.status.endswith('ING'):
        raise exception.Forbidden(
            'app %s is not editable or deletable '
            'when status is %s' % (app.name, app.status)
        )
    return True


@database.run_in_session()
@utils.wrap_to_dict(APP_RESP_FIELDS)
def list_apps(session=None, **filters):
    """list apps."""
    apps = utils.list_db_objects(
        session, models.App, **filters
    )
    return apps


@utils.supported_filters(
    APP_CREATING_REQUIRED_FIELDS,
    ignore_support_keys=APP_IGNORED_FIELDS
)
@database.run_in_session()
@utils.wrap_to_dict(APP_RESP_FIELDS)
def create_app(exception_when_existing=True,
    name=None, session=None, **kwargs
):
    try:
        return utils.add_db_object(
            session, models.App,
            exception_when_existing,
            name, **kwargs
        )
    except exception.DuplicatedRecord:
        session.rollback()
        message = {'error': 'App name %s already exists.' % name}
        return message


@database.run_in_session()
@utils.wrap_to_dict(APP_RESP_FIELDS)
def get_app_by_id(app_id, session=None, **kwargs):
    app = _get_app(
        app_id, session=session, **kwargs
    )
    return app


@database.run_in_session()
def get_app_setconfigs(app_id, session=None, **kwargs):
    app = _get_app(
        app_id, session=session, **kwargs
    )
    return app.setconfigs


@database.run_in_session()
@utils.wrap_to_dict(APP_RESP_FIELDS)
def update_app_by_id(app_id, session=None, **kwargs):
    app = _get_app(
        app_id, session=session
    )
    if _is_app_editable(app):
        try:
            entrypoint = kwargs['entrypoint']
            entrypoints = app.blueprint.entrypoints
            if entrypoint not in entrypoints:
                raise exception.InvalidParameter(
                    'Entrypoint: %s does not exist in blueprint.', entrypoint
                )
            status_handler.update_status_by_app_id(
                app_id,
                session=session,
                status='CREATING_STEP_3',
                message='Finished selecting entrypoints',
                severity='INFO'
            )
        except KeyError:
            pass
        try:
            test_plan = kwargs['test_plan']
            if set(test_plan.keys()) != set(APP_TEST_FIELDS):
                raise exception.InvalidParameter(
                    'Test plan keys %s are invalid.', test_plan.keys()
                )
            status_handler.update_status_by_app_id(
                app_id,
                session=session,
                status='CREATING_STEP_4',
                message='Finished updating test plans',
                severity='INFO'
            )
        except KeyError:
            pass

        return utils.update_db_object(session, app, **kwargs)


@database.run_in_session()
@utils.wrap_to_dict(APP_RESP_FIELDS)
def update_app_status_by_id(app_id, status, message):
    app = _get_app(
        app_id, session=session
    )
    utils.update_db_object(
        session,
        status=status,
        message=message
    )


@database.run_in_session()
def delete_app_by_id(
    app_id, also_delete_containers=False,
    session=None, **kwargs
):
    app = _get_app(
        app_id, session=session
    )
    logging.info(
        'deleting app %s with also_delete_containers=%s ',
        app.name, also_delete_containers
    )
    if _is_app_editable(app):
        del_obj = utils.del_db_object(
            session, app
        )
        if also_delete_containers:
            pass
        return del_obj


@database.run_in_session()
def get_entrypoints(app, session=None):
    blueprint = app.blueprint
    if not blueprint.content:
        raise exception.RecordDoesNotExist(
            'Blueprint %s content does not exist, '
            'try submitting valid blueprint first?' % blueprint_id
        )
    e = blueprint.content['entrypoints']
    return list(e) if not isinstance(e, list) else e


@database.run_in_session()
def get_dryrun_base_plan(app_id, session=None):
    app = _get_app(app_id, session=session)
    try:
        content = app.blueprint.content
    except:
        raise exception.RecordDoesNotExist(
            'App: %s does not have a valid blueprint, '
            'try submitting valid blueprint first?' % app_id
        )
    resource_controllers = filter(
        lambda x: (
            'spec' in x.keys()
            and 'template' in x['spec'].keys()
            and 'containers' in x['spec']['template']['spec'].keys()
            and all('resources' in c.keys() for c in x['spec']['template']['spec']['containers'])
        ),
        content
    )
    print resource_controllers
    plans = []
    for controller in resource_controllers:
        plan = {}
        plan['name'] = controller['metadata']['name'].replace('rc', '')
        plan['pod_replicas'] = controller['spec']['replicas']
        plan['containers'] = []
        for container in controller['spec']['template']['spec']['containers']:
            c = {}
            c['name'] = container['name']
            c['cpu'] = float(
                container['resources']['limits']['cpu'].replace('m', '')
            )/1000
            c['memory'] = float(
                container['resources']['limits']['memory'].replace('Mi', '')
            )
            plan['containers'].append(c)
        plans.append(plan)
    return plans


@database.run_in_session()
def deploy_app(app_id, session=None, **data):
    app = _get_app(app_id, session=session)
    entrypoint = app.entrypoint
    app_blueprint = app.blueprint.content
    test_plan = app.test_plan
    logging.info(
        'Sending deploy app task to deployment manager for app %s',
        app_id
    )
    celery_client.celery.send_task(
        'smartops.tasks.deploy_app',
        (
            app_id, entrypoint, app_blueprint,
            test_plan
        )
    )
    return {
        'message': 'Deployment task sent.',
        'app_id': app_id
    }


@database.run_in_session()
def dry_run(app_id, session=None):
    app = _get_app(app_id, session=session)
    entrypoint = app.entrypoint
    app_blueprint = app.blueprint.content
    test_plan = app.test_plan
    logging.info(
        'Sending deploy capacity planner task to deploy manager for app %s',
        app_id
    )
    celery_client.celery.send_task(
        'smartops.tasks.deploy_capacity_planner',
        (
            app_id, entrypoint, app_blueprint,
            test_plan,
        )
    )
    status_handler.update_status_by_app_id(
        app_id,
        session=session,
        status='PLANNING',
        message='Probing best capacity plans',
        severity='INFO'
    )
    return {
        'message': 'Capacity Planner deployment task sent.',
        'app_id': app_id
    }


def test_app():
    celery_client.celery.send_task('smartops.tasks.test',())
    return {
        'message': 'task sent'
    }
