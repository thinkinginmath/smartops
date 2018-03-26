import datetime
import functools
import logging
import re
import requests
import simplejson as json
import yaml

from flask import Blueprint
from flask import make_response
from flask import request
from smartops.api import exception_handler
from smartops.api import utils
from smartops.db.handlers import app as app_handler
from smartops.db.handlers import app_status as status_handler
from smartops.db.handlers import blueprint as blueprint_handler
from smartops.db.handlers import capacity_plan as capacity_plan_handler
from smartops.db.handlers import database
# from smartops.db.handlers import metrics as metrics_handler
from smartops.db.handlers import sla as sla_handler
from smartops.utils import flags
from smartops.utils import logsetting
from smartops.utils import util


api = Blueprint('api', __name__)

def _wrap_response(func, response_code):
    def wrapped_func(*args, **kwargs):
        return utils.make_json_response(
            response_code,
            func(*args, **kwargs)
        )
    return wrapped_func


def _get_request_args(**kwargs):
    """Get request args as dict.
    The value in the dict is converted to expected type.
    Args:
       kwargs: for each key, the value is the type converter.
    """
    args = dict(request.args)
    logging.log(
        logsetting.getLevelByName('fine'),
        'origin request args: %s', args
    )
    for key, value in args.items():
        if key in kwargs:
            converter = kwargs[key]
            if isinstance(value, list):
                args[key] = [converter(item) for item in value]
            else:
                args[key] = converter(value)
    logging.log(
        logsetting.getLevelByName('fine'),
        'request args: %s', args
    )
    return args


def _get_request_data():
    """Convert reqeust data from string to python dict.
    If the request data is not json formatted, raises
    exception_handler.BadRequest.
    If the request data is not json formatted dict, raises
    exception_handler.BadRequest
    If the request data is empty, return default as empty dict.
    Usage: It is used to add or update a single resource.
    """
    if request.form:
        return request.form.to_dict()
    if request.data:
        try:
            print "DATA:", request.data
            data = json.loads(request.data)
        except Exception:
            raise exception_handler.BadRequest(
                'request data is not json formatted: %s' % request.data
            )
        if not isinstance(data, dict):
            raise exception_handler.BadRequest(
                'request data is not json formatted dict: %s' % request.data
            )
        return data
    else:
        return {}


@api.route('/apps', methods=['GET'])
def list_apps():
    data = _get_request_args()
    return utils.make_json_response(
        200,
        app_handler.list_apps(
            **data
        )
    )
    return apps

@api.route('/apps/<int:app_id>', methods=['GET'])
def get_app_by_id(app_id):
    data = _get_request_args()
    return utils.make_json_response(
        200,
        app_handler.get_app_by_id(
            app_id, **data
        )
    )


@api.route('/apps/<int:app_id>/config', methods=['GET'])
def show_app_config(app_id):
    data = _get_request_args()
    return utils.make_json_response(
        200,
        app_handler.get_app_setconfigs(
            app_id, **data
        )
    )


@api.route('/apps/<int:app_id>/status', methods=['GET'])
def show_app_status(app_id):
    return utils.make_json_response(
        200,
        status_handler.get_status_by_app_id(
            app_id
        )
    )


@api.route('/apps/<int:app_id>', methods=['PUT'])
def update_app_by_id(app_id):
    data = _get_request_data()
    return utils.make_json_response(
        200,
        app_handler.update_app_by_id(
            app_id, **data
        )
    )


@api.route('/apps', methods=['POST'])
def create_app():
    data = _get_request_data()
    response = app_handler.create_app(**data)
    if 'error' in response.keys():
        return utils.make_json_response(
            409,
            response
        )
    return utils.make_json_response(
        200,
        response
    )


@api.route('/apps/<int:app_id>', methods=['DELETE'])
def delete_app_by_id(app_id):
    data = _get_request_data()
    return utils.make_json_response(
        200,
        app_handler.delete_app_by_id(
            app_id, **data
        )
    )


@api.route('/apps/<int:app_id>/blueprint', methods=['GET'])
def get_blueprint_by_app_id(app_id):
    blueprint = blueprint_handler.get_blueprint_by_app_id(app_id)
    if not blueprint:
        return utils.make_json_response(
            404,
            {
                'error': 'Blueprint not found for App: %s' % app_id
            }
        )
    return utils.make_json_response(
        200,
        blueprint
    )


@api.route('/apps/<int:app_id>/raw_blueprint', methods=['GET'])
def get_raw_blueprint_by_app_id(app_id):
    raw_blueprint = blueprint_handler.get_raw_blueprint_by_app_id(app_id)
    if raw_blueprint == None:
        return utils.make_json_response(
            404,
            {
                'error': 'Blueprint not found for App: %s' % app_id
            }
        )
    response = make_response(raw_blueprint, 200)
    response.headers["content-type"] = "text/plain"
    return response


@api.route('/apps/<int:app_id>/blueprint', methods=['PUT'])
def update_blueprint_by_app_id(app_id):
    data = _get_request_data()
    return utils.make_json_response(
        200,
        blueprint_handler.validate_and_upsert_blueprint(
            app_id, **data
        )
    )


@api.route('/apps/<int:app_id>/entrypoint', methods=['GET'])
def get_entrypoints(app_id):
    app = app_handler.get_app_by_id(app_id)
    if not app['entrypoints']:
        app_handler.get_entrypoints(app)
    return utils.make_json_response(
        200,
        app['entry_points']
    )



#@api.route('/apps/<int:app_id>/metrics', methods=['GET'])
#def list_app_metrics(app_id):
#    data = _get_request_args()
#    return utils.make_json_response(
#        200,
#        metrics_handler.list_metrics(
#            app_id, *data
#        )
#    )


#@api.route('/apps/<int:app_id>/metrics', methods=['DELETE'])
#def delete_app_metrics(app_id):
#    return utils.make_json_response(
#        200,
#        metrics_handler.delete_metrics_by_app_id(
#            app_id
#        )
#    )


@api.route('/apps/<int:app_id>/sla', methods=['GET'])
def get_app_sla(app_id):
    return utils.make_json_response(
        200,
        sla_handler.get_sla_by_app_id(
            app_id
        )
    )


@api.route('/apps/<int:app_id>/sla', methods=['PUT'])
def update_app_sla(app_id):
    data = _get_request_data()
    return utils.make_json_response(
        200,
        sla_handler.update_sla_by_app_id(
            app_id, **data
        )
    )


@api.route('/apps/<int:app_id>/status', methods=['GET'])
def get_app_status(app_id):
    return utils.make_json_response(
        200,
        status_handler.get_status_by_app_id(app_id)
    )


@api.route('/apps/<int:app_id>/status', methods=['PUT'])
def update_app_status(app_id):
    data = _get_request_data()
    return utils.make_json_response(
        200,
        status_handler.update_status_by_app_id(
            app_id, *data
        )
    )


@api.route('/apps/<int:app_id>/dryrun_base_plan', methods=['GET'])
def get_dryrun_base_plan(app_id):
    return utils.make_json_response(
        200,
        app_handler.get_dryrun_base_plan(
            app_id
        )
    )


@api.route('/apps/<int:app_id>/capacity_plans/create', methods=['POST'])
def create_capacity_plan(app_id):
    data = _get_request_data()
    return utils.make_json_response(
        200,
        capacity_plan_handler.create_capacity_plan(
            app_id, *data
        )
    )


@api.route('/apps/<int:app_id>/capacity_plans', methods=['GET'])
def list_capacity_plans(app_id):
    return utils.make_json_response(
        200,
        capacity_plan_handler.list_capacity_plans(
            app_id, **kwargs
        )
    )


@api.route('/capacity_plans/<int:capacity_plan_id>', methods=['GET'])
def get_capacity_plan(capacity_plan_id):
    return utils.make_json_response(
        200,
        capacity_plan_handler.get_capacity_plan(
            capacity_plan_id
        )
    )


@api.route('/apps/testapp', methods=['GET'])
def test_app():
    return utils.make_json_response(
        200,
        app_handler.test_app()
    )


@api.route('/apps/<int:app_id>/dry_run', methods=['POST'])
def start_dry_run(app_id):
    logging.info('Starting dry run for app: %s', app_id)
    response = app_handler.dry_run(app_id)
    if 'status' in response:
        return utils.make_json_response(
            202, response
        )
    else:
        return utils.make_json_response(
            200, response
        )


@api.route('/apps/<int:app_id>/dry_run_result', methods=['GET'])
def get_dry_run_result(app_id):
    logging.info('Getting dry run result for app: %s', app_id)
    result = {}
    if app_id == 1:
        result = requests.get('http://10.145.88.66:30500/api/autoshift/api/v1/apps/6/demand-profiles/11/all-merged')
    else:
        result = requests.get('http://10.145.88.66:30500/api/autoshift/api/v1/apps/7/demand-profiles/12/all-merged')
    return utils.make_json_response(
        200,
        result.json()
    )


@api.route('/apps/<int:app_id>/deploy', methods=['POST'])
def deploy_app(app_id):
    data = _get_request_data()
    logging.info('Starting deployment of app: %s', app_id)
    response = app_hadnler.deploy_app(
        app_id, **data
    )
    if 'status' in response:
        return utils.make_json_response(
            202, response
        )
    else:
        return utils.make_json_response(
            200, response
        )
"""

def init():
    logging.info('Initializing Flask...')
    database.init()


if __name__ == '__main__':
    flags.init()
    logsetting.init()
    init()
    app.run(host='0.0.0.0', port=8080, debug=True)
"""
