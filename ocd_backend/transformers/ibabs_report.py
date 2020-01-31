import re

import iso8601
import simplejson as json

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer

log = get_source_logger('ibabs_report')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def report_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'ibabs',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    report = Report(original_item['id'],
                    collection='report',
                    **source_defaults)
    report.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                        source=self.source_definition['key'],
                                                        supplier='allmanak',
                                                        collection=self.source_definition['source_type'])

    # Determine title field
    title_field = None
    keys = sorted(original_item.keys(), key=len)
    for field in keys:
        # Search for things that look like title
        if field.lower()[0:3] == 'tit':
            title_field = field
            break

    for field in keys:
        id_for_field = '%sIds' % field
        if id_for_field in original_item and title_field is None:
            title_field = field
            break

    if title_field is None:
        log.error("Unable to determine title field. Original item: %s" % json.dumps(original_item))
    else:
        report.name = original_item[title_field]

    report.classification = original_item.get('_ReportName')
    report.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                        source=self.source_definition['key'],
                                                        supplier='allmanak',
                                                        collection=self.source_definition['source_type'])
    try:
        report.creator = Organization(original_item['_Extra']['Values']['Fractie(s)'],
                                      collection='party',
                                      **source_defaults)
        report.creator.name = original_item['_Extra']['Values']['Fractie(s)']
    except KeyError:
        pass

    # Determine description field
    description_field = None
    possible_fields = ('agendapunt', 'onderwerp', 'indieners')
    for field in possible_fields:
        if field in original_item.keys():
            description_field = field
    try:
        report.description = original_item[description_field]
    except KeyError:
        try:
            report.description = original_item['_Extra']['Values']['Omschrijving']
        except KeyError:
            pass

    # Determine date field
    date_field = None
    keys = sorted(original_item.keys(), key=len)
    for field in keys:
        # Search for things that look like title
        if 'datum' in field.lower():
            date_field = field
            break

    if date_field is None:
        log.error("Unable to determine date field. Original item: %s" % json.dumps(original_item))

    datum = None
    if date_field in original_item:
        if isinstance(original_item[date_field], list):
            datum = original_item[date_field][0]
        else:
            datum = original_item[date_field]

    start_date = None
    if datum is not None:
        # msgpack does not like microseconds for some reason.
        # no biggie if we disregard it, though
        report.start_date = iso8601.parse_date(re.sub(r'\.\d+\+', '+', datum))
        start_date = True
        report.end_date = iso8601.parse_date(re.sub(r'\.\d+\+', '+', datum))

    if original_item.get('status') == 'Aangenomen':
        report.result = ResultPassed
    elif original_item.get('status') == 'Verworpen':
        report.result = ResultFailed

    report.attachment = list()
    for document in original_item['_Extra']['Documents'] or []:
        attachment_file = MediaObject(document['Id'],
                                      collection='attachment',
                                      **source_defaults)
        attachment_file.identifier_url = 'ibabs/report/%s' % document['Id']
        attachment_file.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                     source=self.source_definition['key'],
                                                                     supplier='allmanak',
                                                                     collection=self.source_definition['source_type'])

        attachment_file.original_url = document['PublicDownloadURL']
        attachment_file.size_in_bytes = document['FileSize']
        attachment_file.name = document['DisplayName']
        attachment_file.is_referenced_by = report
        if start_date:
            attachment_file.last_discussed_at = report.start_date
        report.attachment.append(attachment_file)

    report.save()
    return report
