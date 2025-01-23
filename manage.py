#!/usr/bin/env python
from copy import deepcopy
from datetime import datetime
from glob import glob
from hashlib import sha1
import json
import os
import requests
import sys
from pprint import pprint
from uuid import uuid4

import redis
import click
from click.core import Command

from elasticsearch.exceptions import RequestError
from elasticsearch.helpers import reindex

from ocd_backend.es import elasticsearch as es
from ocd_backend.es import setup_elasticsearch
from ocd_backend.models.postgres_database import PostgresDatabase
from ocd_backend.models.postgres_models import ItemHash, Property, Resource, Source, StoredDocument
from ocd_backend.models.serializers import PostgresSerializer
from ocd_backend.pipeline import setup_pipeline
from ocd_backend.settings import SOURCES_CONFIG_FILE, \
    DEFAULT_INDEX_PREFIX, DUMPS_DIR, REDIS_HOST, REDIS_PORT
from ocd_backend.utils.indexed_file import IndexedFile
from ocd_backend.utils.misc import load_sources_config
from ocd_backend.utils.monitor import get_recent_counts
from ocd_backend.utils.file_parsing import file_parser, md_file_parser, md_file_parser_using_ocr, parse_result_is_empty

# NOTE: don't forget to change this value if you forked this repo and
# renamed '/opt/oci'
sys.path.insert(0, '/opt/ori')


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

@cli.group()
def developers():
    """Utilities for developers"""


@click.command('put_template')
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


@click.command('put_mapping')
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


@click.command('create_indexes')
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


@click.command('delete_indexes')
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
    for index, stats in indices['indices'].items():
        click.echo('- %s (%s docs, %s)' % (index, stats['docs']['num_docs'],
                                           stats['index']['size']))
    if click.confirm('Are you sure you want to delete the above indices?'):
        es.indices.delete(index=index_glob)

    if delete_template or click.confirm('Do you want to delete the template too?'):
        es.indices.delete_template('ocd_template')


@click.command('available_indices')
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


@click.command('copy')
@click.argument('source_index')
@click.argument('target_index')
def es_copy_data(source_index, target_index):
    """
    CCopy elasticsearch data from one index ot another.

    :param source_index: The source index
    :param target-index: The target index
    :param target-host: The target host
    """

    es.reindex(body={
        'source': {
            'index': source_index
        },
        'dest': {
            'index': target_index,
        }
    })

@click.command('list_sources')
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
            for sub_key in list(source):
                all_keys.append('%s -s %s' % (key, sub_key))

    click.echo('Available sources:')
    for source in sorted(set(all_keys)):
        click.echo(' - %s' % source)


@click.command('start')
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
        setup_pipeline.delay(source, uuid4().hex)
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
        source_run_uuid = uuid4().hex

        selected_entities = []
        for item in source.get('entities'):
            if (not entiteit and item) or (entiteit and item.get('entity') in entiteit):
                selected_entities.append(item.get('entity'))

                new_source = deepcopy(source)
                new_source.update(item)
                setup_pipeline.delay(new_source, source_run_uuid)

        click.echo('[%s] Processed pipelines: %s' % (source_id, ', '.join(selected_entities)))


@click.command('load_redis')
@click.argument('modus')
@click.option('--source_path', default='*')
@click.option('--sources_config', default=SOURCES_CONFIG_FILE)
def extract_load_redis(modus, source_path, sources_config):
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True)

    available_sources = load_sources_config(sources_config)
    redis_sources = redis_client.keys(source_path)

    sources = []
    for redis_source in redis_sources:
        if redis_source[0:1] == '_':
            # Settings are underscored so we skip them
            continue

        source_value = redis_client.get(redis_source)
        if source_value.startswith('disabled'):
            # If value equals disabled we will not process the source
            continue
        elif modus in source_value:
            sources.append(redis_source)
    #pprint(available_sources)
    for provider, municipalities in available_sources.items():
        for m in municipalities.keys():
            redis_source = "%s.%s" % (provider, m,)
            redis_client.set(redis_source, modus)


@click.command('process')
@click.argument('modus')
@click.option('--source_path', default='*')
@click.option('--sources_config', default=SOURCES_CONFIG_FILE)
@click.option('--start_date', default=None)
@click.option('--end_date', default=None)
@click.option('--lock_key', default=None)
@click.option('--indexed_filename', default=None)
def extract_process(modus, source_path, sources_config, start_date, end_date, lock_key, indexed_filename):
    """
    Start extraction based on the flags in Redis.
    It uses the source_path in Redis db 1 to identify which municipalities should be extracted.
    A municipality can be set using 'SET ori.ibabs.arnhem enabled'.
    Currently, possible values are: enabled, disabled and archived.

    :param modus: the configuration to use for processing, starting with an underscore. i.e. _enabled, _archived, _disabled. Looks for configuration in redis like _custom.start_date
    :param source_path: path in redis to search, i.e. ori.ibabs.arnhem. Defaults to *
    :param sources_config: Path to file containing pipeline definitions. Defaults to the value of ``settings.SOURCES_CONFIG_FILE``
    :param start_date: Use this start_date instead of the value defined in redis
    :param end_date: Use this end_date instead of the value defined in redis
    :param lock_key: If passed, this redis key contains the source that is currently being processed
    :param indexed_filename: If passed, write start time and end time of processing to this file
    """
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True)

    available_sources = load_sources_config(sources_config)
    redis_sources = redis_client.keys(source_path)

    sources = []
    for redis_source in redis_sources:
        if redis_source[0:1] == '_':
            # Settings are underscored so we skip them
            continue

        source_value = redis_client.get(redis_source)
        if source_value.startswith('disabled'):
            # If value equals disabled we will not process the source
            continue
        elif modus in source_value:
            sources.append(redis_source)

    if not redis_sources:
        click.echo('No sources found in redis')
        return
    elif not sources:
        click.echo('Redis sources found but non match the modus %s' % modus)
        return

    settings_path = '_%s.*' % modus
    setting_keys = redis_client.keys(settings_path)
    if not setting_keys:
        click.echo('No settings found in redis for %s' % settings_path)
        return

    settings = {}
    enabled_entities = []
    for key in setting_keys:
        _, _, name = key.rpartition('.')
        value = redis_client.get(key)
        if name == 'entities':
            enabled_entities = value.split(' ')
        else:
            settings[name] = value

    if start_date is not None:
        settings['start_date'] = start_date
    if end_date is not None:
        settings['end_date'] = end_date
    if lock_key is not None:
        settings['lock_key'] = lock_key
    if indexed_filename is not None:
        settings['indexed_filename'] = indexed_filename

    for source in sources:
        try:
            project, provider, source_name = source.split('.')
            available_source = available_sources['%s.%s' % (project, provider)][source_name]
            source_run_uuid = uuid4().hex

            click.echo('[%s] Start extract for %s' % (source_name, source_name))
            IndexedFile(settings.get('indexed_filename')).signal_start(source_name)

            selected_entities = []
            for entity in available_source.get('entities', []):
                if not enabled_entities or entity.get('entity') in enabled_entities:
                    selected_entities.append(entity.get('entity'))

                    # Redis settings are overruled by source definitions, for some sources a start_date must be enforced
                    new_source = deepcopy(settings)
                    new_source.update(deepcopy(available_source))
                    new_source.update(entity)

                    setup_pipeline.delay(new_source, source_run_uuid)

            click.echo('[%s] Started pipelines: %s' % (source_name, ', '.join(selected_entities)))
        except ValueError:
            click.echo('Invalid source format %s in redis' % source)
        except KeyError:
            click.echo('Source %s in redis does not exist in available sources' % source)


@click.command('monthly_check')
@click.option('--token')
def es_monthly_check(token):
    result = get_recent_counts()
    #pprint(result)
    lines = []
    for idx, total in result.items():
        if total < 20:
            muni = ' '.join([i for i in idx.split('_')[1:-1] if i != 'fixed'])
            lines.append(
                "%s heeft %d documenten erbij in de afgelopen maand" % (muni, total,))
    #print(lines)
    if len(lines) > 0:
        payload = {
          "title":"Possible fetch problems this month ...",
          "body":"\n".join(lines),
          "assignees":[
            "breyten"],
          "labels":["bug"]}
        resp = requests.post(
            'https://api.github.com/repos/openstate/open-raadsinformatie/issues',
            headers={
                'X-GitHub-Api-Version': '2022-11-28',
                'Accept': 'application/vnd.github+json',
                'Authorization': 'Bearer ' + token
            },
            data=json.dumps(payload)
        )
        print(resp)

@click.command('purge_dbs')
@click.pass_context
def developers_purge_dbs(ctx):
    """
    Purges the Postgres database, Redis and Elastic Search index.
    Checks development env by testing environment variable.
    """
    RELEASE_STAGE = os.getenv('RELEASE_STAGE')
    if RELEASE_STAGE != "development":
        print("*** This should only be run in development ***")
        return

    # Postgres
    try:
        database = PostgresDatabase(serializer=PostgresSerializer)
        session = database.Session()
        session.query(ItemHash).delete()
        session.query(Source).delete()
        session.query(Property).delete()
        session.query(StoredDocument).delete()
        session.query(Resource).delete()
        session.commit()
    except Exception as e:
        print(f'Error purging Postgres db: {e}')

    # Redis
    try:
        redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True)
        redis_client.flushdb()
    except Exception as e:
        print(f'Error purging redis: {e}')

    # Elastic Search
    try:
        indices = ctx.invoke(available_indices)
        for index in indices:
            es.indices.delete(index=index)
    except Exception as e:
        print(f'Error purging Elastic Search: {e}')


    print("Postgres database, Redis and Elastic Search index have been purged")

@click.command('process_pdfs')
@click.option('--dir')
def developers_process_pdfs(dir):
    """
    Processes all pdfs contained in dir
    """
    print(f"Processing all pdfs in directory {dir}", flush=True)

    files = glob(f"{dir}/*.pdf")
    print(f"Number of files: {len(files)}", flush=True)
    for filename in files:
        print(f"\nNow processing {filename}", flush=True)
        ocr_used = None
        md_text = md_file_parser(filename, filename)
        if parse_result_is_empty(md_text):
            print(f"Parse result is empty, now trying OCR", flush=True)
            md_text = md_file_parser_using_ocr(filename, filename)
            ocr_used = True

        extension = '.txt' if ocr_used else '.md'
        _, name = os.path.split(filename)
        root, ext = os.path.splitext(filename)
        result_file = f"{root}{extension}"

        with open(result_file, 'w') as f:
            for page in md_text:
                f.write(f"{page}\n")
            print(f"Result written to {root}{extension}", flush=True)

# Register commands explicitly with groups, so we can easily use the docstring
# wrapper
elasticsearch.add_command(es_put_template)
elasticsearch.add_command(es_put_mapping)
elasticsearch.add_command(create_indexes)
elasticsearch.add_command(delete_indexes)
elasticsearch.add_command(available_indices)
elasticsearch.add_command(es_copy_data)
elasticsearch.add_command(es_monthly_check)

extract.add_command(extract_list_sources)
extract.add_command(extract_start)
extract.add_command(extract_process)
extract.add_command(extract_load_redis)

developers.add_command(developers_purge_dbs)
developers.add_command(developers_process_pdfs)

if __name__ == '__main__':
    cli()
