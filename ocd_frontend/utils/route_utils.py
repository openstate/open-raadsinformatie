import os
import json

from utils.pdf_naming import PdfNaming
from flask import (
    send_from_directory, abort, make_response, current_app
)
from ocd_frontend.settings import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, SOURCES_CONFIG_FILE
from utils.sources import load_sources_config
from elasticsearch import Elasticsearch

elasticsearch = Elasticsearch([{'host': ELASTICSEARCH_HOST, 'port': ELASTICSEARCH_PORT, 'timeout': 600}])
SPOTLIGHTS_FILE = 'data/spotlights.json'

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

def get_indices():
    # First get indices from Elasticsearch
    es_results = elasticsearch.indices.get_alias('*')
    es_results = {list(v["aliases"].keys())[0]: k for k, v in es_results.items()}
    # is now a dict containing entries like "ori_texel": "ori_texel_20260624063543"

    # Get source definitions
    sources = load_sources_config(SOURCES_CONFIG_FILE)

    # Link source definitions to indices (_type is e.g. "ori.ibabs")
    indices = {}
    for _type, h in sources.items():
        for _source, source_definition in h.items():
            supplier = source_definition['supplier']
            es_prefix = source_definition.get("es_prefix", 'ori')
            match es_prefix:
                case 'ori':
                    source_type = "Gemeente"
                case 'owi':
                    source_type = "Waterschap"
                case 'osi':
                    source_type = "Provincie"
                case _:
                    raise Exception(f"unknown es_prefix {es_prefix}")

            alias = f"{es_prefix}_{source_definition['index_name']}"
            if es_results.get(alias):
                indices[es_results[alias]] = {
                    "alias": alias,
                    "type": source_type,
                    "Gemeentenaam": source_definition["source_name"],
                    "CBScode": source_definition.get("cbs_id", '').upper(),
                    "key": source_definition['key'],
                    "supplier": supplier
                }
            else:
                current_app.logger.error(f"No index found for {alias}")

    return indices

def get_spotlights():
  if not os.path.exists(SPOTLIGHTS_FILE):
    return {}

  with open(SPOTLIGHTS_FILE) as f:
    spotlights = json.load(f)
    return spotlights


def write_spotlights(spotlights):
  with open(SPOTLIGHTS_FILE, 'w') as f:
    json.dump(spotlights, f)


def add_spotlight(cbs_code):
  indices_info = get_indices()

  source = next(filter(lambda h: h['CBScode'] == cbs_code, indices_info.values()), None)
  if not source:
    raise Exception(f"Source with cbs code {cbs_code} does not exist")

  spotlights = get_spotlights()
  spotlights[cbs_code] = source
  write_spotlights(spotlights)


def remove_spotlight(cbs_code):
  spotlights = get_spotlights()
  if cbs_code in spotlights:
    spotlights.pop(cbs_code)
    write_spotlights(spotlights)
  else:
    raise Exception(f"Source with cbs code {cbs_code} was not spotlighted")
