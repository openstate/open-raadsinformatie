from ocd_frontend.models.postgres_database import FrontendPostgresDatabase
from ocd_frontend.utils.route_utils import resolve_send_file, resolve_send_file_iri, resolve_send_file_iri_like
from . import app

from flask import (
    request, abort
)
db = FrontendPostgresDatabase()

@app.route("/v1")
def index():
    return abort(404)

@app.route("/v1/resolve/ibabs/<item_type>/<uuid>")
def resolve_ibabs(item_type, uuid):
    # iBabs items are referred to using a unique uuid
    return resolve_send_file(request, db, uuid)

@app.route("/v1/resolve/api.notubiz.nl/document/<int:canonical_id>")
def resolve_notubiz(canonical_id):
    # The canonical_id itself is not unique enough so find item using canonical_iri
    # The database values have 'format=json&version=1.17.0' appended, so use a LIKE search
    canonical_iri = f"https://api.notubiz.nl/document/{canonical_id}"
    return resolve_send_file_iri_like(request, db, canonical_iri)

@app.route("/v1/resolve/parlaeus/agenda_item/<document_id>")
def resolve_parlaeus(document_id):
    # The document_id of Parlaeus items seem to be unique enough to use as canonical_id in searches
    return resolve_send_file(request, db, document_id)

@app.route("/v1/resolve/<path:path>/api/v1/meetings/<int:meeting_id>/documents/<int:document_id>")
@app.route("/v1/resolve/<path:path>/api//v1/meetings/<int:meeting_id>/documents/<int:document_id>", merge_slashes=False)
def resolve_go(path, meeting_id, document_id):
    # The document_id itself is not unique enough so find item using canonical_iri
    canonical_iri = f"https://{path}/api/v1/meetings/{meeting_id}/documents/{document_id}"
    return resolve_send_file_iri(request, db, canonical_iri)

@app.route('/v1/<path:path>')
def catch_all(path):
    return abort(404)
