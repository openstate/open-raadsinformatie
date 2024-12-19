import json

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer
from ocd_backend.utils.misc import is_valid_iso8601_date
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, RETRY_MAX_RETRIES, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX

log = get_source_logger('ibabs_report')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
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

    if title_field is None:
        for field in keys:
            id_for_field = '%sIds' % field
            if id_for_field in original_item:
                title_field = field
                break

    if title_field is not None:
        report_name = original_item[title_field]
    else:
        report_name = original_item.get('_Extra', {}).get('Values', {}).get('Titel')

    if report_name is None:
        report_name = original_item.get('_ReportName')

    if report_name is None:
        log.warning(f'[{self.source_definition["key"]}] Unable to determine title field. Original item: '
                  f'{json.dumps(original_item, default=str)}')
    else:
        report.name = report_name

    report.classification = original_item.get('_ReportName')
    report.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                        source=self.source_definition['key'],
                                                        supplier='allmanak',
                                                        collection=self.source_definition['source_type'])
    try:
        name = original_item.get('_Extra', {}).get('Values', {}).get('Fractie(s)')
        if name is not None:
            report.creator = Organization(name,
                                        collection='party',
                                        **source_defaults)
            report.creator.name = name
    except AttributeError as e:
        # "'NoneType' object has no attribute 'get'" when a dict entry is present but has value None
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
            report.description = original_item.get('_Extra', {}).get('Values', {}).get('Omschrijving')
        except AttributeError:
            pass

    datum = original_item.get('datum')
    if is_valid_iso8601_date(datum):
        report.start_date = datum
        report.end_date = datum

    if original_item.get('status') == 'Aangenomen':
        report.result = ResultPassed
    elif original_item.get('status') == 'Verworpen':
        report.result = ResultFailed

    report.attachment = list()
    for document in original_item['_Extra'].get('Documents', []) or []:
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
        attachment_file.file_name = document['FileName']
        attachment_file.is_referenced_by = report
        if is_valid_iso8601_date(datum):
            attachment_file.last_discussed_at = datum
        report.attachment.append(attachment_file)

    report.save()
    return report
