import re

import iso8601

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer

log = get_source_logger('ibabs_report')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def report_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'ibabs',
        'collection': 'report',
    }

    report = CreativeWork(original_item['id'][0],
                          source=self.source_definition['key'],
                          supplier='ibabs',
                          collection='report')
    report.canonical_id = original_item['id'][0]
    report.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                        source=self.source_definition['key'],
                                                        supplier='allmanak',
                                                        collection=self.source_definition['source_type'])

    report_name = original_item['_ReportName'].split(r'\s+')[0]
    report.classification = u'Report'

    name_field = None
    try:
        name_field = self.source_definition['fields'][report_name]['name']
    except KeyError:
        for field in original_item.keys():
            # Search for things that look like title
            if field.lower()[0:3] == 'tit':
                name_field = field
                break

            id_for_field = '%sIds' % (field,)
            if id_for_field in original_item and name_field is None:
                name_field = field
                break

    report.name = original_item[name_field][0]

    # Temporary binding reports to municipality as long as events and agendaitems are not
    # referenced in the iBabs API
    report.creator = TopLevelOrganization(self.source_definition['allmanak_id'],
                                          source=self.source_definition['key'],
                                          supplier='allmanak',
                                          collection=self.source_definition['source_type'])

    try:
        name_field = self.source_definition['fields'][report_name]['description']
        report.description = original_item[name_field][0]
    except KeyError:
        try:
            report.description = original_item['_Extra']['Values']['Toelichting']
        except KeyError:
            pass

    try:
        datum_field = self.source_definition['fields'][report_name]['start_date']
    except KeyError:
        datum_field = 'datum'

    datum = None
    if datum_field in original_item:
        if isinstance(original_item[datum_field], list):
            datum = original_item[datum_field][0]
        else:
            datum = original_item[datum_field]

    if datum is not None:
        # msgpack does not like microseconds for some reason.
        # no biggie if we disregard it, though
        report.start_date = iso8601.parse_date(re.sub(r'\.\d+\+', '+', datum))
        report.end_date = iso8601.parse_date(re.sub(r'\.\d+\+', '+', datum))

    report.status = EventConfirmed

    report.attachment = list()
    for document in original_item['_Extra']['Documents'] or []:
        attachment_file = MediaObject(document['Id'],
                                      source=self.source_definition['key'],
                                      supplier='ibabs',
                                      collection='attachment')
        attachment_file.canonical_id = document['Id']
        attachment_file.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                     source=self.source_definition['key'],
                                                                     supplier='allmanak',
                                                                     collection=self.source_definition['source_type'])

        attachment_file.original_url = document['PublicDownloadURL']
        attachment_file.size_in_bytes = document['FileSize']
        attachment_file.name = document['DisplayName']
        attachment_file.is_referenced_by = report
        if report.start_date:
            attachment_file.last_discussed_at = report.start_date
        report.attachment.append(attachment_file)

    report.save()
    return report
