#!/usr/bin/env python
from copy import deepcopy
from datetime import datetime
import json
from glob import glob
from hashlib import sha1
import os
import requests
import sys

import redis
import click
from click.core import Command
from click.decorators import _make_command

from elasticsearch.exceptions import RequestError

from ocd_backend.es import elasticsearch as es
from ocd_backend.pipeline import setup_pipeline
from ocd_backend.settings import SOURCES_CONFIG_FILE, \
    DEFAULT_INDEX_PREFIX, DUMPS_DIR, REDIS_HOST, REDIS_PORT
from ocd_backend.utils.misc import load_sources_config


# NOTE: don't forget to change this value if you forked this repo and
# renamed '/opt/oci'
sys.path.insert(0, '/opt/ori')


def command(name=None, cls=None, **attrs):
    """
    Wrapper for click Commands, to replace the click.Command docstring with the
    docstring of the wrapped method (i.e. the methods defined below). This is
    done to support the autodoc in Sphinx, and the correct display of docstrings
    """
    if cls is None:
        cls = Command

    def decorator(f):
        r = _make_command(f, name, attrs, cls)
        r.__doc__ = f.__doc__
        return r
    return decorator


def _create_path(path):
    if not os.path.exists(path):
        click.secho('Creating path "%s"' % path, fg='green')
        os.makedirs(path)

    return path


def _checksum_file(target):
    """
    Compute sha1 checksum of a file. As some files could potentially be huge,
    iterate in blocks of 32kb to keep memory overhead to a minimum.

    :param target: path to file to compute checksum on
    :return: SHA1 checksum of file
    """
    checksum = sha1()
    # 'rb': don't convert input to text buffer
    with open(target, 'rb') as f:
        # Read in chunks; must be a multiple of 128 bytes
        for chunk in iter(lambda: f.read(32768), b''):
            checksum.update(chunk)
    return checksum.hexdigest()


def _write_chunks(chunks, f):
    """
    Write chunks (iterable) of a downloading file to filehandler f
    :param chunks: iterable containing chunks to write to disk
    :param f: open, writable filehandler
    """
    for chunk in chunks:
        # Filter out keep-alive chunks
        if chunk:
            f.write(chunk)
            f.flush()


def _download_dump(dump_url, collection, target_dir=DUMPS_DIR):
    """
    Download a Gzipped dump of a OpenCultuurData collection to disk. Compares
    the SHA1 checksum of the dump with the dump files already available
    locally, and skips downloading if the file is already available.

    :param dump_url: URL to the dump of an index
    :param collection: Name of the collection the URL is a dump of
    :param target_dir: Directory to download the dump files to. A directory
                       per index is created in the target directory, and per
                       dump file a checksum and a dump file will be created.
    :return: Path to downloaded dump
    """
    # Make sure the directory exists
    _create_path(os.path.join(target_dir, collection))

    # First, get the SHA1 checksum of the file we intend to download
    r = requests.get('{}.sha1'.format(dump_url))

    checksum = r.content

    # Compare checksums of already downloaded files with the checksum of the
    # file we are trying to download
    for c in glob('{}/*.sha1'.format(os.path.join(target_dir, collection))):
        # latest is a symlink
        if 'latest' in c:
            continue
        with open(c, 'r') as f:
            if checksum == f.read():
                click.secho('This file is already downloaded ({})'.format(c),
                            fg='yellow')
                return

    # Construct name of local file
    filepath = os.path.join(target_dir, collection, '{}_{}'.format(
        collection,
        datetime.now().strftime('%Y%m%d%H%S'))
    )

    # Get and write dump to disk (iteratively, as dumps could get rather big)
    r = requests.get(dump_url, stream=True)

    content_length = r.headers.get('content-length', False)

    with open('{}.gz'.format(filepath), 'wb') as f:
        if content_length:
            content_length = int(content_length)
            with click.progressbar(r.iter_content(chunk_size=1024),
                                   length=content_length / 1024,
                                   label=click.style(
                                           'Downloading {}'.format(dump_url),
                                           fg='green'
                                   )) as chunks:
                _write_chunks(chunks, f)
        else:
            _write_chunks(r.iter_content(chunk_size=1024), f)

    # Compare checksum of new file with the one on the server in order to make
    # sure everything went OK
    checksum_new_file = _checksum_file('{}.gz'.format(filepath))
    if checksum != checksum_new_file:
        click.secho('Something went wrong during downloading (checksums are not'
                    ' equal), removing file', fg='red')
        os.remove('{}.gz'.format(filepath))
        return

    with open('{}.gz.sha1'.format(filepath), 'w') as f:
        f.write(checksum)

    return '{}.gz'.format(filepath)


@click.group()
@click.version_option()
def cli():
    """Open Cultuur Data"""


@cli.group()
def elasticsearch():
    """Manage Elasticsearch"""


@cli.group()
def extract():
    """Extraction pipeline"""


@cli.group()
def dumps():
    """Create and load dumps of indices"""


@command('put_template')
@click.option('--template_file', default='es_mappings/ori_template.json',
              type=click.File('rb'), help='Path to JSON file containing the template.')
def es_put_template(template_file):
    """
    Put a template into Elasticsearch. A template contains settings and mappings
    that should be applied to multiple indices. Check ``es_mappings/ocd_template.json``
    for an example.

    :param template_file: Path to JSON file containing the template. Defaults to ``es_mappings/ocd_template.json``.
    """
    click.echo('Putting ES template: %s' % template_file.name)

    template = json.load(template_file)
    template_file.close()

    es.indices.put_template('ori_template', template)


@command('put_mapping')
@click.argument('index_name')
@click.argument('mapping_file', type=click.File('rb'))
def es_put_mapping(index_name, mapping_file):
    """
    Put a mapping for a specified index.

    :param index_name: name of the index to PUT a mapping for.
    :param mapping_file: path to JSON file containing the mapping.
    """
    click.echo('Putting ES mapping %s for index %s'
               % (mapping_file.name, index_name))

    mapping = json.load(mapping_file)
    mapping_file.close()

    es.indices.put_mapping(index=index_name, body=mapping)


@command('create_indexes')
@click.argument('mapping_dir', type=click.Path(exists=True, resolve_path=True))
def create_indexes(mapping_dir):
    """
    Create all indexes for which a mapping- and settings file is available.

    It is assumed that mappings in the specified directory follow the
    following naming convention: "ocd_mapping_{SOURCE_NAME}.json".
    For example: "ocd_mapping_rijksmuseum.json".
    """
    click.echo('Creating indexes for ES mappings in %s' % mapping_dir)

    for mapping_file_path in glob('%s/ori_mapping_*.json' % mapping_dir):
        # Extract the index name from the filename
        index_name = DEFAULT_INDEX_PREFIX
        mapping_file = os.path.split(mapping_file_path)[-1].split('.')[0]
        index_name = '%s_%s' % (DEFAULT_INDEX_PREFIX,
                                '_'.join(mapping_file.rsplit('_')[2:]))

        click.echo('Creating ES index %s' % index_name)

        mapping_file = open(mapping_file_path, 'rb')
        mapping = json.load(mapping_file)
        mapping_file.close()

        try:
            es.indices.create(index=index_name, body=mapping)
        except RequestError as e:
            error_msg = click.style('Failed to create index %s due to ES '
                                    'error: %s' % (index_name, e.error),
                                    fg='red')
            click.echo(error_msg)


@command('delete_indexes')
@click.option('--delete-template', is_flag=True, expose_value=True)
def delete_indexes(delete_template):
    """
    Delete all Open Cultuur Data indices. If option ``--delete-template`` is
    provided, delete the index template too (index template contains default
    index configuration and mappings).

    :param delete_template: if provided, delete template too
    """
    index_glob = '%s_*' % DEFAULT_INDEX_PREFIX
    indices = es.indices.status(index=index_glob, human=True)

    click.echo('Open Cultuur Data indices:')
    for index, stats in indices['indices'].iteritems():
        click.echo('- %s (%s docs, %s)' % (index, stats['docs']['num_docs'],
                                           stats['index']['size']))
    if click.confirm('Are you sure you want to delete the above indices?'):
        es.indices.delete(index=index_glob)

    if delete_template or click.confirm('Do you want to delete the template too?'):
        es.indices.delete_template('ocd_template')


@command('available_indices')
def available_indices():
    """
    Shows a list of collections available at ``ELASTICSEARCH_HOST:ELASTICSEARCH_PORT``.
    """
    available = []
    indices = [
        i.split() for i in es.cat.indices().strip().split('\n') if
        i.split()[2].startswith('%s_' % (DEFAULT_INDEX_PREFIX,))]

    if not indices:
        click.secho('No indices available in this instance', fg='red')
        return None

    for index in indices:
        click.secho('%s (%s docs, %s)' % (index[2], index[6], index[8]),
                    fg='green')
        available.append(index[2])

    return available


@command('list_sources')
@click.option('--sources_config', default=SOURCES_CONFIG_FILE)
def extract_list_sources(sources_config):
    """
    Show a list of available sources (preconfigured pipelines).
    Old-style sources might show multiple entities.
    New-style sources will show only the name of the source

    :param sources_config: Path to file containing pipeline definitions. Defaults to the value of ``settings.SOURCES_CONFIG_FILE``
    """
    sources = load_sources_config(sources_config)

    all_keys = list()
    for key, source in sources.items():
        all_keys.append(key)
        if 'id' not in source and 'entities' not in source:
            for sub_key in source.keys():
                all_keys.append('%s -s %s' % (key, sub_key))

    click.echo('Available sources:')
    for source in sorted(set(all_keys)):
        click.echo(' - %s' % source)


@command('start')
@click.option('--sources_config', default=SOURCES_CONFIG_FILE)
@click.argument('source_id')
@click.option('--subitem', '-s', multiple=True)
@click.option('--entiteit', '-e', multiple=True)
def extract_start(source_id, subitem, entiteit, sources_config):
    """
    Start extraction for a pipeline specified by ``source_id`` defined in
    ``--sources-config``. ``--sources-config defaults to ``settings.SOURCES_CONFIG_FILE``.
    When ``id`` is specified in the source it will trigger old-style json behaviour for backward compatibility reasons.

    Otherwise new-style yaml is assumed, which looks for ``entities`` in the source to determine the order in which entities are processed.
    If no ``entities`` are found in the source, all subitems of the source will be processed, if any.
    If one or more ``--subitem`` is specified, only those subitems will be processed.
    When one or more ``--entiteit`` is specified, only those entities will be processed. By default, all entities are processed.

    Note: ``--subitem`` and ``--entiteit`` only work in new-style yaml configurations.

    :param sources_config: Path to file containing pipeline definitions. Defaults to the value of ``settings.SOURCES_CONFIG_FILE``
    :param source_id: identifier used in ``--sources_config`` to describe pipeline
    :param subitem: one ore more items under the parent `source_id`` to specify which subitems should be run
    :param entiteit: one ore more entity arguments to specify which entities should be run
    """

    sources = load_sources_config(sources_config)

    # Find the requested source definition in the list of available sources
    source = sources.get(source_id)

    # Without a config we can't do anything, notify the user and exit
    if not source:
        click.echo('Error: unable to find source with id "%s" in sources '
                   'config' % source_id)
        return

    # Check for old-style json sources
    if 'id' in source:
        setup_pipeline(source)
        return

    # New-style behaviour
    selected_sources = dict()
    if 'entities' not in source:
        if subitem:
            for s in subitem:
                # Add the specified subs
                selected_sources[s] = source[s]
        else:
            # All sub sources if no subs are specified
            selected_sources = source
    else:
        # Only one main source
        selected_sources = {source_id: source}

    # Processing each item
    for source_id, source in selected_sources.items():
        click.echo('[%s] Start extract for %s' % (source_id, source_id))

        selected_entities = []
        for item in source.get('entities'):
            if (not entiteit and item) or (entiteit and item.get('entity') in entiteit):
                selected_entities.append(item.get('entity'))

                new_source = deepcopy(source)
                new_source.update(item)
                setup_pipeline(new_source)

        click.echo('[%s] Processed pipelines: %s' % (source_id, ', '.join(selected_entities)))


@command('process')
@click.argument('modus')
@click.option('--source_path', default='*')
@click.option('--sources_config', default=SOURCES_CONFIG_FILE)
def extract_process(modus, source_path, sources_config):
    """
    Start extraction based on the flags in Redis.
    It uses the source_path in Redis db 1 to identify which municipalities should be extracted.
    A municipality can be set using 'SET ori.ibabs.arnhem enabled'.
    Currently, possible values are: enabled, disabled and archived.

    :param modus: the configuration to use for processing, starting with an underscore. i.e. _enabled, _archived, _disabled. Looks for configuration in redis like _custom.start_date
    :param source_path: path in redis to search, i.e. ori.ibabs.arnhem. Defaults to *
    :param sources_config: Path to file containing pipeline definitions. Defaults to the value of ``settings.SOURCES_CONFIG_FILE``
    """
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=1)

    available_sources = load_sources_config(sources_config)
    redis_sources = redis_client.keys(source_path)

    if not redis_sources:
        click.echo('No sources found in redis')
        return None

    sources = []
    entities = {}

    for redis_source in redis_sources:
        if redis_source[0:1] == '_':
            # Settings are underscored so we skip them
            continue

        source_value = redis_client.get(redis_source)
        if source_value.startswith('disabled'):
            # If value equals disabled we will not process the source
            continue
        elif source_value.startswith(modus):
            sources.append(redis_source)

        source_entities = source_value.split(' ')
        if len(source_entities) > 1:
            entities[redis_source] = source_entities[1:]

    settings_path = '_%s.*' % modus
    setting_keys = redis_client.keys(settings_path)
    if not setting_keys:
        click.echo('No settings found in redis for %s' % settings_path)
        return

    settings = {}
    for key in setting_keys:
        _, _, name = key.rpartition('.')
        settings[name] = redis_client.get(key)

    for source in sources:
        try:
            project, provider, source_name = source.split('.')
            available_source = available_sources['%s.%s' % (project, provider)][source_name]
            enabled_entities = entities.get(source)

            click.echo('[%s] Start extract for %s' % (source_name, source_name))

            selected_entities = []
            for entity in available_source['entities']:
                if not enabled_entities or entity.get('entity') in enabled_entities:
                    selected_entities.append(entity.get('entity'))

                    new_source = deepcopy(available_source)
                    new_source.update(entity)
                    new_source.update(settings)
                    setup_pipeline(new_source)

            click.echo('[%s] Started pipelines: %s' % (source_name, ', '.join(selected_entities)))
        except ValueError:
            click.echo('Invalid source format %s in redis' % source)
        except KeyError:
            click.echo('Source %s in redis does not exist in available sources' % source)


# Register commands explicitly with groups, so we can easily use the docstring
# wrapper
elasticsearch.add_command(es_put_template)
elasticsearch.add_command(es_put_mapping)
elasticsearch.add_command(create_indexes)
elasticsearch.add_command(delete_indexes)
elasticsearch.add_command(available_indices)

extract.add_command(extract_list_sources)
extract.add_command(extract_start)
extract.add_command(extract_process)


if __name__ == '__main__':
    cli()
