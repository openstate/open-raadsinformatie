from functools import wraps
import json

from flask import jsonify, request

from ocd_frontend.factory import create_app_factory


def create_app(settings_override=None):
    """Returns the REST API application instance."""
    app = create_app_factory(__name__, __path__, settings_override)
    app.errorhandler(OcdApiError)(OcdApiError.serialize_error)

    def add_cors_headers(resp):
        resp.headers['Access-Control-Allow-Origin'] = '*'
        # See https://stackoverflow.com/questions/12630231/how-do-cors-and-access-control-allow-headers-work
        resp.headers['Access-Control-Allow-Headers'] = 'origin, content-type, accept'
        return resp

    app.after_request(add_cors_headers)

    return app


class OcdApiError(Exception):
    """API error class.

    :param msg: the message that should be returned to the API user.
    :param status_code: the HTTP status code of the response
    """

    def __init__(self, msg, status_code):
        self.msg = msg
        self.status_code = status_code

    def __str__(self):
        return repr(self.msg)

    @staticmethod
    def serialize_error(e):
        return jsonify(dict(status='error', error=e.msg)), e.status_code


def decode_json_post_data(fn):
    """Decorator that parses POSTed JSON and attaches it to the request
    object (:obj:`request.data`)."""

    @wraps(fn)
    def wrapped_function(*args, **kwargs):
        if request.method == 'POST':
            data = request.get_data(cache=False)
            if not data:
                raise OcdApiError('No data was POSTed', 400)

            try:
                request_charset = request.mimetype_params.get('charset')
                if request_charset is not None:
                    data = json.loads(data, encoding=request_charset)
                else:
                    data = json.loads(data)
            except:
                raise OcdApiError('Unable to parse POSTed JSON', 400)

            request.data = data

        return fn(*args, **kwargs)

    return wrapped_function
