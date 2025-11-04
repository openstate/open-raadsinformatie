from utils.pdf_naming import PdfNaming
from flask import (
    send_from_directory, abort
)

def get_format_from_request(request):
    format = PdfNaming.FORMAT_ORIGINAL
    if request.args.get('format') == 'markdown':
        format = PdfNaming.FORMAT_MARKDOWN
    elif request.args.get('format') == 'metadata':
        format = PdfNaming.FORMAT_METADATA

    return format

def resolve_send_file(request, db, canonical_id):
    format = get_format_from_request(request)
    content_type, filename, fullpath = db.get_fullpath_from_canonical_id(canonical_id, format)
    if not fullpath:
        return abort(404)

    relative_path = fullpath.replace('/opt/ori/data/', '')
    return send_from_directory('/opt/ori/data', relative_path, as_attachment=True, mimetype=content_type, download_name=filename)
    