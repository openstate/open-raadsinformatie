#!/usr/bin/env python
from datetime import datetime
import json
from glob import glob
import gzip
from hashlib import sha1
import os
import requests
import sys
import time
from urlparse import urljoin

import click
from click.core import Command
from click.decorators import _make_command


def command(name=None, cls=None, **attrs):
    """
    Wrapper for click Commands, to replace the click.Command docstring with the
    docstring of the wrapped method (i.e. the methods defined below). This is
    done to support the autodoc in Sphinx, and the correct display of
    docstrings
    """
    if cls is None:
        cls = Command

    def decorator(f):
        r = _make_command(f, name, attrs, cls)
        r.__doc__ = f.__doc__
        return r
    return decorator


def _generate_for_organisations(name, almanak):
    organisations = [{
        "id": "%s_municipality" % (name.lower(),),
        "extractor": "ocd_backend.extractors.odata.ODataExtractor",
        "transformer": "ocd_backend.transformers.BaseTransformer",
        "item": "ocd_backend.items.organisations.MunicipalityOrganisationItem",
        "enrichers": [],
        "loader": "ocd_backend.loaders.ElasticsearchLoader",
        "cleanup": "ocd_backend.tasks.CleanupElasticsearch",
        "hidden": False,
        "index_name": name.lower(),
        "file_url": (
            "http://dataderden.cbs.nl/ODataApi/OData/45006NED/Gemeenten"),
        "doc_type": "organisations",
        "filter": {
            "Title": name.lower()
        },
        "keep_index_on_update": True
    }, {
        "id": "%s_organisations" % (name.lower(),),
        "extractor": "ocd_backend.extractors.almanak.OrganisationsExtractor",
        "transformer": "ocd_backend.transformers.BaseTransformer",
        "item": "ocd_backend.items.organisations.AlmanakOrganisationItem",
        "enrichers": [],
        "loader": "ocd_backend.loaders.ElasticsearchLoader",
        "cleanup": "ocd_backend.tasks.CleanupElasticsearch",
        "hidden": False,
        "index_name": name.lower(),
        "file_url": almanak,
        "doc_type": "organisations",
        "item_xpath": "//",
        "keep_index_on_update": True
    }]
    return organisations


def _generate_for_persons(name, almanak):
    persons = [{
        "id": "%s_persons" % (name.lower(),),
        "extractor": "ocd_backend.extractors.almanak.PersonsExtractor",
        "transformer": "ocd_backend.transformers.BaseTransformer",
        "item": "ocd_backend.items.persons.AlmanakPersonItem",
        "enrichers": [],
        "loader": "ocd_backend.loaders.ElasticsearchLoader",
        "cleanup": "ocd_backend.tasks.CleanupElasticsearch",
        "hidden": False,
        "index_name": name.lower(),
        "file_url": almanak,
        "doc_type": "persons",
        "item_xpath": "//",
        "keep_index_on_update": True
    }]
    return persons


def _generate_for_msi(name, almanak):
    sources = [{
        "id": "%s_meetings" % (name.lower(),),
        "extractor": "ocd_backend.extractors.ibabs.IBabsMeetingsExtractor",
        "transformer": "ocd_backend.transformers.BaseTransformer",
        "item": "ocd_backend.items.ibabs_meeting.IBabsMeetingItem",
        "enrichers": [],
        "loader": "ocd_backend.loaders.ElasticsearchLoader",
        "cleanup": "ocd_backend.tasks.CleanupElasticsearch",
        "hidden": False,
        "index_name": name.lower(),
        "doc_type": "events",
        "sitename": name,
        "keep_index_on_update": True
    }, {
        "id": "%s_reports" % (name.lower(),),
        "extractor": "ocd_backend.extractors.ibabs.IBabsReportsExtractor",
        "transformer": "ocd_backend.transformers.BaseTransformer",
        "item": "ocd_backend.items.ibabs_meeting.IBabsReportItem",
        "enrichers": [],
        "loader": "ocd_backend.loaders.ElasticsearchLoader",
        "cleanup": "ocd_backend.tasks.CleanupElasticsearch",
        "hidden": False,
        "index_name": name.lower(),
        "doc_type": "events",
        "sitename": name,
        "keep_index_on_update": True,
        "regex": ".*"
    }, {
        "id": "%s_committees" % (name.lower(),),
        "extractor": "ocd_backend.extractors.ibabs.IBabsCommitteesExtractor",
        "transformer": "ocd_backend.transformers.BaseTransformer",
        "item": "ocd_backend.items.ibabs_committee.CommitteeItem",
        "enrichers": [],
        "loader": "ocd_backend.loaders.ElasticsearchLoader",
        "cleanup": "ocd_backend.tasks.CleanupElasticsearch",
        "hidden": False,
        "index_name": name.lower(),
        "doc_type": "organisations",
        "sitename": name,
        "keep_index_on_update": True
    }]
    return sources


@click.group()
@click.version_option()
def cli():
    """Open Raads Informatie Data"""


@cli.group()
def sources():
    """Generate sources for a municipality"""


@command('municipality')
@click.argument('name', default='')
@click.argument('almanak', default='')
@click.argument('provider', default='msi')
def generate_sources_municipality(name, almanak, provider):
    """
    This generate the sources for a municipality

    param: name: The name of the municipality
    param: almanak: The link to the Almanak page
    param: provider: The provider of the information system. Currently: msi
    """

    method_name = '_generate_for_%s' % (provider,)
    possibles = globals().copy()
    possibles.update(locals())
    method = possibles.get(method_name)

    sources = (
        _generate_for_organisations(name, almanak) +
        _generate_for_persons(name, almanak) +
        method(name, almanak)
    )

    print json.dumps(sources, indent=2)

sources.add_command(generate_sources_municipality)

if __name__ == '__main__':
    cli()
