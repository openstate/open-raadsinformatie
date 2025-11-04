from ocd_frontend.models.postgres_database import FrontendPostgresDatabase
from ocd_frontend.utils.route_utils import get_format_from_request, resolve_send_file
from . import app

from flask import (
    request, abort
)

db = FrontendPostgresDatabase()

@app.route("/v1")
def index():
    return abort(404)

@app.route("/v1/resolve/ibabs/<item_type>/<uuid>")
def resolve_ibabs(_item_type, uuid):
    return resolve_send_file(request, db, uuid)

@app.route("/v1/resolve/api.notubiz.nl/document/<int:canonical_id>")
def resolve_notubiz(canonical_id):
    return resolve_send_file(request, db, canonical_id)

@app.route("/v1/resolve/parlaeus/agenda_item/<document_id>")
def resolve_parlaeus(document_id):
    return resolve_send_file(request, db, document_id)

@app.route("/v1/resolve/<path:path>/api/v1/meetings/<int:meeting_id>/documents/<int:document_id>")
@app.route("/v1/resolve/<path:path>/api//v1/meetings/<int:meeting_id>/documents/<int:document_id>", merge_slashes=False)
def resolve_go(_path, _meeting_id, document_id):
    return resolve_send_file(request, db, document_id)

@app.route('/v1/<path:path>')
def catch_all(_path):
    return abort(404)
