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

from elasticsearch import helpers as es_helpers
from elasticsearch.exceptions import RequestError

from ocd_backend.es import elasticsearch as es
from ocd_backend.pipeline import setup_pipeline
from ocd_backend.settings import SOURCES_CONFIG_FILE, DEFAULT_INDEX_PREFIX
from ocd_backend.utils.misc import load_sources_config
from ocd_frontend.settings import DUMPS_DIR, API_URL, LOCAL_DUMPS_DIR


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


def _process_choices(val):
    print val
    return val


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
def frontend():
    """Front-end API"""


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
    click.echo('Creating indexes for ES mappings in %s' % (mapping_dir))

    for mapping_file_path in glob('%s/ocd_mapping_*.json' % mapping_dir):
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

    :param delete-template: if provided, delete template too
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
    indices = es.cat.indices()

    if not indices:
        click.secho('No indices available in this instance', fg='red')
        return None

    for index in indices.strip().split('\n'):
        index = index.split()
        if u'resolver' not in index[1] and u'combined_index' not in index[1]:
            click.secho('%s (%s docs, %s)' % (index[1], index[4], index[6]),
                        fg='green')
            available.append(index[1])

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
                all_keys.append(sub_key)

    click.echo('Available sources:')
    for source in sorted(all_keys):
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
        for item in source.get('entities'):
            if (not entiteit and item) or (entiteit and item.get('entity') in entiteit):
                source.update(item)
                setup_pipeline(source)


@command('runserver')
@click.argument('host', default='0.0.0.0')
@click.argument('port', default=5000, type=int)
def frontend_runserver(host, port):
    """
    Run development server on ``host:port``.

    :param host: host to run dev server on (defaults to 0.0.0.0)
    :param port: defaults to 5000
    """
    from werkzeug.serving import run_simple
    from ocd_frontend.wsgi import application
    run_simple(host, port, application, use_reloader=True, use_debugger=True)


@command('create')
@click.option('--index', default=None)
@click.pass_context
def create_dump(ctx, index):
    """
    Create a dump of an index. If you don't provide an ``--index`` option,
    you will be prompted with a list of available index names. Dumps are
    stored as a gzipped txt file in ``settings.DUMPS_DIR/<index_name>/<
    timestamp>_<index-name>.gz``, and a symlink ``<index-name>_latest.gz`` is
    created, pointing to the last created dump.

    :param ctx: Click context, so we can issue other management commands
    :param index: name of the index you want to create a dump for
    """
    if not index:
        available_idxs = ctx.invoke(available_indices)
        if not available_idxs:
            return
        index = click.prompt('Name of index to dump')

        if index not in available_idxs:
            click.secho('"%s" is not an available index' % index, fg='red')
            return

    match_all = {'query': {'match_all': {}}}

    total_docs = es.count(index=index).get('count')

    path = _create_path(path=os.path.join(DUMPS_DIR, index))
    dump_name = '%(index_name)s_%(timestamp)s.gz' % {
        'index_name': index,
        'timestamp': datetime.now().strftime('%Y%m%d%H%M%S')
    }
    new_dump = os.path.join(path, dump_name)

    with gzip.open(new_dump, 'wb') as g:
        with click.progressbar(es_helpers.scan(es, query=match_all, scroll='1m',
                                               index=index),
                               length=total_docs) as documents:
            for doc in documents:
                g.write('%s\n' % json.dumps(doc))

    click.secho('Generating checksum', fg='green')
    checksum = _checksum_file(new_dump)
    checksum_path = os.path.join(DUMPS_DIR, index, '%s.sha1' % dump_name)

    with open(checksum_path, 'w') as f:
        f.write(checksum)

    click.secho('Created dump "%s" (checksum %s)' % (dump_name, checksum),
                fg='green')


    latest = os.path.join(path, '%s_latest.gz' % index)
    try:
        os.unlink(latest)
    except OSError:
        click.secho('First time creating dump, skipping unlinking',
                    fg='yellow')
    os.symlink(new_dump, latest)
    click.secho('Created symlink "%s_latest.gz" to "%s"' % (index, new_dump),
                fg='green')

    latest_checksum = os.path.join(os.path.dirname(checksum_path), '%s_latest.gz.sha1' % index)
    try:
        os.unlink(latest_checksum)
    except OSError:
        click.secho('First time creating dump, skipping unlinking checksum',
                    fg='yellow')
    os.symlink(checksum_path, latest_checksum)
    click.secho('Created symlink "%s_latest.gz.sha1" to "%s"' % (index, checksum_path),
                fg='green')


@command('list')
@click.option('--api-url', default=API_URL)
def list_dumps(api_url):
    """
    List available dumps of API instance at ``api_address``. Use this option to
    obtain information about dumps available at other OpenCultuurData API
    instances.

    :param api_url: URL of API location
    """
    url = urljoin(api_url, 'dumps')

    try:
        r = requests.get(url)
    except:
        click.secho('No OCD API instance with dumps available at {url}'
                    .format(url=url), fg='red')
        return

    if not r.ok:
        click.secho('Request on {url} failed'.format(url=url), fg='red')

    dumps = r.json().get('dumps', {})
    for index in dumps:
        click.secho(index, fg='green')
        for dump in sorted(dumps.get(index, []), reverse=True):
            click.secho('\t{dump}'.format(dump=dump), fg='green')


@command('download')
@click.option('--api-url', default=API_URL, help='URL to API instance to fetch '
                                                 'dumps from.')
@click.option('--destination', '-d', default=LOCAL_DUMPS_DIR,
              help='Directory to download dumps to.')
@click.option('--collections', '-c', multiple=True)
@click.option('--all-collections', '-a', is_flag=True, expose_value=True,
              help='Download latest version of all collections available')
def download_dumps(api_url, destination, collections, all_collections):
    """
    Download dumps of OCD collections to your machine, for easy ingestion.

    :param api_url: URL to API instance to fetch dumps from. Defaults to ``ocd_frontend.settings.API_URL``, which is set to the API instance hosted by OpenCultuurData itself.
    :param destination: path to local directory where dumps should be stored. Defaults to ``ocd_frontend.settings.LOCAL_DUMPS_DIR``.
    :param collections: Names of collections to fetch dumps for. Optional; you will be prompted to select collections when not provided.
    :param all_collections: If this flag is set, download all available dumps. Optional; you will be prompted to select collections when not provided.
    """
    url = urljoin(api_url, 'dumps')
    try:
        r = requests.get(url)
    except:
        click.secho('Could not connect to API', fg='red')
        return

    available_collections = [(i+1, index) for i, index in enumerate(r.json().get('dumps'))]
    dumps = r.json().get('dumps')

    if all_collections:
        # Download all the things
        for collection in dumps:
            _download_dump([d for d in dumps.get(collection)
                            if d.endswith('_latest.gz')][0],
                           collection=collection,
                           target_dir=destination)
        return

    if not collections:
        for i, dump in available_collections:
            click.secho('{i}) {index}'.format(i=i, index=dump), fg='yellow')

        collection = click.prompt('For which collection do you want to download'
                                  ' a dump? Please provide the number correspon'
                                  'ding to the collection that you want to down'
                                  'load', type=click.Choice([
            str(i[0]) for i in available_collections]))

        collection = dict(available_collections)[int(collection)]
        for i, dump in enumerate(dumps[collection]):
            click.secho('{i}) {dump}'.format(i=i+1, dump=dump), fg='yellow')

        dump_url = click.prompt('Which dump of the collection "{collection}" do'
                                ' you want to download? Please provide the numb'
                                'er corresponding to the dump that you want to '
                                'download',
                                type=click.Choice([str(j) for j in range(1, len(dumps[collection]) + 1)]))
        dump_url = dumps[collection][int(dump_url)]

        _download_dump(dump_url=dump_url, collection=collection,
                       target_dir=destination)
        return

    for collection in collections:
        if collection not in dumps.keys():
            click.secho('"{}" is not available as a dump, skipping'.format(collection),
                        fg='red')
            continue

        for i, dump in enumerate(dumps[collection]):
            click.secho('{i}) {dump}'.format(i=i+1, dump=dump), fg='yellow')

        dump_url = click.prompt('Which dump of the collection "{collection}" do'
                                ' you want to download? Please provide the numb'
                                'er corresponding to the dump that you want to '
                                'download',
                                type=click.Choice([str(j) for j in range(1, len(dumps[collection]) + 1)]))
        dump_url = dumps[collection][int(dump_url)]

        _download_dump(dump_url=dump_url, collection=collection,
                       target_dir=destination)


@command('load')
@click.option('--collection-dump', '-c', help='Path to dump of collection to load',
              default=None, type=click.Path(exists=True))
@click.option('--collection-name', '-n', help='An index will be created with th'
                                              'is name. If left empty, collecti'
                                              'on name will be derived from dum'
                                              'p name.', default=None)
def load_dump(collection_dump, collection_name):
    """
    Restore an index from a dump file.

    :param collection_dump: Path to a local gzipped dump to load.
    :param collection_name: Name for the local index to restore the dump to. Optional; will be derived from the dump name, at your own risk. Note that the pipeline will add a "ocd_" prefix string to the collection name, to ensure the proper mapping and settings are applied.
    """
    available_dumps = glob(os.path.join(LOCAL_DUMPS_DIR, '*/*.gz'))
    if not collection_dump:
        choices = []
        for i, dump in enumerate(available_dumps):
            choices.append(unicode(i+1))
            click.secho('{i}) {dump}'.format(i=i+1, dump=dump), fg='green')
        dump_idx = click.prompt('Choose one of the dumps listed above',
                                type=click.Choice(choices))
        collection_dump = available_dumps[int(dump_idx) - 1]

    collection = os.path.abspath(collection_dump)
    collection_id = '_'.join(collection.split('/')[-1].split('.')[0].split('_')[:2])

    if not collection_name:
        collection_name = collection_id.replace('ocd_', '')

    source_definition = {
        'id': collection_id,
        'extractor': 'ocd_backend.extractors.staticfile.StaticJSONDumpExtractor',
        'transformer': 'ocd_backend.transformers.BaseTransformer',
        'loader': 'ocd_backend.loaders.ElasticsearchLoader',
        'cleanup': 'ocd_backend.tasks.CleanupElasticsearch',
        'item': 'ocd_backend.items.LocalDumpItem',
        'dump_path': collection,
        'index_name': collection_name
    }

    click.secho(str(source_definition), fg='yellow')

    setup_pipeline(source_definition)

    click.secho('Queued items from {}. Please make sure your Celery workers'
                ' are running, so the loaded items are processed.'.format(collection),
                fg='green')


# Register commands explicitly with groups, so we can easily use the docstring
# wrapper
frontend.add_command(frontend_runserver)

dumps.add_command(load_dump)
dumps.add_command(list_dumps)
dumps.add_command(create_dump)
dumps.add_command(download_dumps)

elasticsearch.add_command(es_put_template)
elasticsearch.add_command(es_put_mapping)
elasticsearch.add_command(create_indexes)
elasticsearch.add_command(delete_indexes)
elasticsearch.add_command(available_indices)

extract.add_command(extract_list_sources)
extract.add_command(extract_start)


if __name__ == '__main__':
    cli()
