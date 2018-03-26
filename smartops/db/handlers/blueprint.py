import logging
import yaml

from smartops.api import exception_handler as api_exception
from smartops.db.handlers import app as app_handler
from smartops.db.handlers import app_status as status_handler
from smartops.db.handlers import database
from smartops.db.handlers import utils
from smartops.db import exception as db_exception
from smartops.db import models


BLUEPRINT_RESP_FIELDS = [
    'id', 'entrypoints', 'content', 'app_id', 'topology'
]


def _get_blueprint(blueprint_id, session=None, **kwargs):
    if isinstance(blueprint_id, (int, long)):
        return utils.get_db_object(
            session, models.AppBlueprint, id=blueprint_id, **kwargs
        )
    raise db_exception.InvalidParameter(
        'Blueprint id %s type is not compatible' % blueprint_id
    )


def _get_blueprint_by_app_id(app_id, session=None, **kwargs):
    if isinstance(app_id, (int, long)):
        app = utils.get_db_object(session, models.App, id=app_id, **kwargs)
        blueprint = app.blueprint
        if not blueprint:
            blueprint = {}
        return blueprint
    raise db_exception.InvalidParameter(
        'App id %s type is not compatible.' % app_id
    )


def _generate_topology_from_blueprint(service_list):
    topology = {}
    services = filter(lambda x: x['kind'] == 'Service', service_list)
    rp_controllers = filter(
        lambda x: x['kind'] in ['ReplicationController', 'Deployment'],
        service_list
    )
    statefulsets = filter(lambda x: x['kind'] == 'StatefulSet', service_list)

    for service in services:
        topology.update(
            {
                service['spec']['selector']['name']
                    if 'selector' in service['spec'].keys() and
                        'name' in service['spec']['selector'].keys()
                    else service['metadata']['name']: {
                        'service_name': service['metadata']['name']
                    }
            }
        )

    for statefulset in statefulsets:
        topology[statefulset['spec']['serviceName']]['replica'] = (
            statefulset['spec']['replicas'])


    for rp_controller in rp_controllers:
        try:
            topology[rp_controller['spec']['selector']['name']]['replica'] = (
                rp_controller['spec']['replicas']
            )
        except KeyError:
            topology[rp_controller['spec']['template']['metadata']['labels']['name']]['replica'] = (
                rp_controller['spec']['replicas']
            )
    return topology


@database.run_in_session()
def get_raw_blueprint_by_app_id(app_id, session=None):
    blueprint = _get_blueprint_by_app_id(app_id, session=session)
    if not blueprint:
        return ''
    return blueprint.content_string


@database.run_in_session()
@utils.wrap_to_dict(BLUEPRINT_RESP_FIELDS)
def get_blueprint_by_id(blueprint_id, session=None, **kwargs):
    return _get_blueprint(
        blueprint_id, session=session, **kwargs
    )


@database.run_in_session()
@utils.wrap_to_dict(BLUEPRINT_RESP_FIELDS)
def get_blueprint_by_app_id(app_id, session=None):
    return _get_blueprint_by_app_id(
        app_id, session=session
    )


@database.run_in_session()
@utils.wrap_to_dict(BLUEPRINT_RESP_FIELDS)
def validate_and_upsert_blueprint(
    app_id, exception_when_existing=True,
    content=None, entrypoints=None,
    session=None, **kwargs
):
    app = app_handler._get_app(app_id, session=session)
    blueprint_content = content
    content_string = content
    service_list = filter(lambda x: x!='', blueprint_content.split('---'))
    try:
        service_list = map(lambda x: yaml.load(x), service_list)
    except yaml.parser.ParserError as parser_error:
        raise db_exception.NotAcceptable(
            'Failed to parse yaml content:%s' % parser_error
        )
    # Start: Validate each blueprint content and extract entrypoints
    entrypoints = []
    primitive_key_sets = set(['apiVersion', 'kind', 'metadata'])
    for service in service_list:
        if any([
            primitive_key_sets >= set(service.keys()),
            service['kind'] != 'Secret' and 'spec' not in service.keys(),
        ]):
            raise db_exception.NotAcceptable(
                'Validation failed: Not all requirements met.'
            )
        try:
            if service['kind'] == 'Service':
                entrypoints.append(service['metadata']['name'])
        except KeyError:
            raise db_exception.NotAcceptable(
                'Service kind not found or name is missing in metadata. '
            )
    topology = _generate_topology_from_blueprint(service_list)
    pods = reduce(
        lambda x,y: x+y,
        [topology[i]['replica'] for i in topology.keys()]
    )
    services = len(topology)
    containers = reduce(
        lambda x,y: x+y,
        [
            len(i['spec']['template']['spec']['containers'])
            if 'spec' in i.keys() and 'template' in i['spec'].keys() else 0
            for i in service_list
        ]
    )
    # Start: Upsert Blueprint table
    if app.blueprint:
        logging.info(
            'Content validated, update blueprint object with entrypoints: %s',
            app.blueprint
        )
        blueprint = app.blueprint
        utils.update_db_object(
            session,
            blueprint,
            content=service_list,
            content_string=content_string,
            entrypoints=entrypoints,
            topology=topology
        )
    else:
        logging.info(
            'Content validated, adding blueprint with entrypoints: %s',
            entrypoints
        )
        blueprint = utils.add_db_object(
            session, models.AppBlueprint, exception_when_existing,
            service_list, content_string, entrypoints, app_id,
            topology=topology, **kwargs
        )
    utils.update_db_object(
        session,
        app,
        containers=containers,
        services=services,
        pods=pods,
    )
    status_handler.update_status_by_app_id(
        app_id,
        session=session,
        status='CREATING_STEP_2',
        message='Finished updating app blueprint',
        severity='INFO'
    )
    return blueprint
