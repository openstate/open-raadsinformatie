from utils.pdf_naming import PdfNaming
from flask import (
    send_from_directory, abort, make_response
)

def get_format_from_request(request):
    format = PdfNaming.FORMAT_ORIGINAL
    if request.args.get('format') == 'markdown':
        format = PdfNaming.FORMAT_MARKDOWN
    elif request.args.get('format') == 'metadata':
        format = PdfNaming.FORMAT_METADATA

    return format

def _handle_send_file(content_type, filename, fullpath):
    if not fullpath:
        return abort(404)

    relative_path = fullpath.replace('/opt/ori/data/', '')
    response = make_response(
        send_from_directory('/opt/ori/data', relative_path, as_attachment=True, mimetype=content_type, download_name=filename)
    )
    response.headers['X-Accel-Redirect'] = f"/file_repository/{relative_path}"
    return response
    

def resolve_send_file(request, db, canonical_id):
    format = get_format_from_request(request)
    content_type, filename, fullpath = db.get_fullpath_from_canonical_id(canonical_id, format)
    return _handle_send_file(content_type, filename, fullpath)
    

def resolve_send_file_iri(request, db, canonical_iri):
    format = get_format_from_request(request)
    content_type, filename, fullpath = db.get_fullpath_from_canonical_iri(canonical_iri, format)
    return _handle_send_file(content_type, filename, fullpath)


def resolve_send_file_iri_like(request, db, canonical_iri):
    format = get_format_from_request(request)
    content_type, filename, fullpath = db.get_fullpath_from_canonical_iri_like(canonical_iri, format)
    return _handle_send_file(content_type, filename, fullpath)
