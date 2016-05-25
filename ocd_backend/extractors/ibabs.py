import json
from pprint import pprint
import re

from lxml import etree
from suds.client import Client

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.exceptions import ConfigurationError

from ocd_backend import settings
from ocd_backend.utils.ibabs import (
    meeting_to_dict, document_to_dict, meeting_item_to_dict,
    meeting_type_to_dict, list_report_response_to_dict,
    list_entry_response_to_dict)


class IBabsBaseExtractor(BaseExtractor):
    """
    A base extractor for the iBabs SOAP service. Instantiates the client
    and configures the right port tu use.
    """

    def __init__(self, *args, **kwargs):
        super(IBabsBaseExtractor, self).__init__(*args, **kwargs)

        self.client = Client(settings.IBABS_WSDL)
        self.client.set_options(port='BasicHttpsBinding_IPublic')


class IBabsCommitteesExtractor(IBabsBaseExtractor):
    """
    Extracts committees from the iBabs SOAP service. This is done by checking
    if the meeting type contains the word 'commissie'.
    """

    def run(self):
        for mt in self.client.service.GetMeetingtypes(
            self.source_definition['sitename']
        ).Meetingtypes[0]:
            # TODO: should this be configurable?
            if 'commissie' in mt.Meetingtype.lower():
                yield 'application/json', json.dumps(meeting_type_to_dict(mt))


class IBabsMeetingsExtractor(IBabsBaseExtractor):
    """
    Extracts meetings from the iBabs SOAP service. The source definition should
    state which kind of meetings should be extracted.
    """

    def _meetingtypes_as_dict(self):
        return {
            o.Id: o.Description for o in self.client.service.GetMeetingtypes(
                self.source_definition['sitename']).Meetingtypes[0]}

    def run(self):
        start_date = self.source_definition.get(
            'start_date', '2015-06-01T00:00:00')
        end_date = self.source_definition.get(
            'end_date', '2016-07-01T00:00:00')
        print "Getting meetings for %s to %s" % (start_date, end_date,)
        meetings = self.client.service.GetMeetingsByDateRange(
            Sitename=self.source_definition['sitename'],
            StartDate=start_date,
            EndDate=end_date,
            MetaDataOnly=False)

        meeting_types = self._meetingtypes_as_dict()

        meeting_count = 0
        meeting_item_count = 0
        for meeting in meetings.Meetings[0]:
            meeting_dict = meeting_to_dict(meeting)
            # Getting the meeting type as a string is easier this way ...
            meeting_dict['Meetingtype'] = meeting_types[
                meeting_dict['MeetingtypeId']]
            yield 'application/json', json.dumps(meeting_dict)

            if meeting.MeetingItems is not None:
                for meeting_item in meeting.MeetingItems[0]:
                    meeting_item_dict = meeting_item_to_dict(meeting_item)
                    # This is a bit hacky, but we need to know this
                    meeting_item_dict['MeetingId'] = meeting_dict['Id']
                    meeting_item_dict['Meeting'] = meeting_dict
                    yield 'application/json', json.dumps(meeting_item_dict)
                    meeting_item_count += 1
            meeting_count += 1
        print "Extracted %d meetings and %d meeting items." % (
            meeting_count, meeting_item_count,)


class IBabsReportsExtractor(IBabsBaseExtractor):
    """
    Extracts reports from the iBabs SOAP Service. The source definition should
    state which kind of reports should be extracted.
    """

    def run(self):
        lists = self.client.service.GetLists(
            Sitename=self.source_definition['sitename'])

        try:
            kv = lists.iBabsKeyValue
        except AttributeError as e:
            print "No reports defined"
            return

        selected_lists = []
        for l in lists.iBabsKeyValue:
            include_regex = self.source_definition.get('include', None) or self.source_definition['regex']
            if not re.match(include_regex, l.Value.lower()):
                continue
            exclude_regex = self.source_definition.get('exclude', None) or r'^$'
            if re.match(exclude_regex, l.Value.lower()):
                continue
            selected_lists.append(l)

        for l in selected_lists:
            reports = self.client.service.GetListReports(
                Sitename=self.source_definition['sitename'], ListId=l.Key)
            report = reports.iBabsKeyValue[0]
            if len(reports.iBabsKeyValue) > 1:
                try:
                    report = [
                        r for r in reports.iBabsKeyValue if r.Value == l.Value][0]
                except IndexError as e:
                    pass

            active_page_nr = 0
            max_pages = self.source_definition.get('max_pages', 1)
            per_page = self.source_definition.get('per_page', 100)
            result_count = per_page
            total_count = 0
            yield_count = 0
            while ((active_page_nr < max_pages) and (result_count == per_page)):
                result = self.client.service.GetListReport(
                    Sitename=self.source_definition['sitename'], ListId=l.Key,
                    ReportId=report.Key, ActivePageNr=active_page_nr,
                    RecordsPerPage=per_page
                )
                result_count = 0
                # print "* %s: %s/%s - %d/%d" % (
                #     self.source_definition['sitename'],
                #     result.ListName, result.ReportName,
                #     active_page_nr, max_pages,)
                try:
                    document_element = result.Data.diffgram[0].DocumentElement[0]
                except AttributeError as e:
                    document_element = None
                except IndexError as e:
                    document_element = None

                if document_element is None:
                    print "No correct document element for this page!"
                    total_count += per_page
                    continue

                for item in document_element.results:
                    dict_item = list_report_response_to_dict(item)
                    dict_item['_ListName'] = result.ListName
                    dict_item['_ReportName'] = result.ReportName
                    extra_info_item = self.client.service.GetListEntry(
                        Sitename=self.source_definition['sitename'],
                        ListId=l.Key, EntryId=dict_item['id'][0])
                    dict_item['_Extra'] = list_entry_response_to_dict(
                        extra_info_item)
                    #yield 'application/json', json.dumps(dict_item)
                    yield_count += 1
                    result_count += 1
                total_count += result_count
                active_page_nr += 1
            print "%s -- total: %s, results %s, yielded %s" % (l.Value, total_count, result_count, yield_count,)
