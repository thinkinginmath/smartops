"""Utils for API usage."""
import logging
from flask import make_response
import simplejson as json


def make_json_response(status_code, data):
    """Wrap json format to the reponse object."""

    result = json.dumps(data, indent=4) + '\r\n'
    resp = make_response(result, status_code)
    resp.headers['Content-type'] = 'application/json'
    return resp
