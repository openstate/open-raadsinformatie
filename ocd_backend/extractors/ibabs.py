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
    meeting_type_to_dict, list_report_response_to_dict)


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
        meetings = self.client.service.GetMeetingsByDateRange(
            Sitename=self.source_definition['sitename'],
            StartDate='2015-06-01T00:00:00', EndDate='2016-07-01T00:00:00',
            MetaDataOnly=False)

        meeting_types = self._meetingtypes_as_dict()

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


class IBabsReportsExtractor(IBabsBaseExtractor):
    """
    Extracts reports from the iBabs SOAP Service. The source definition should
    state which kind of reports should be extracted.
    """

    def run(self):
        lists = self.client.service.GetLists(
            Sitename=self.source_definition['sitename'])

        selected_lists = []
        for l in lists.iBabsKeyValue:
            if not re.match(self.source_definition['regex'], l.Value.lower()):
                continue
            selected_lists.append(l)

        for l in selected_lists:
            reports = self.client.service.GetListReports(
                Sitename=self.source_definition['sitename'], ListId=l.Key)
            if len(reports.iBabsKeyValue) <= 1:
                report = reports.iBabsKeyValue[0]
            else:
                report = [
                    r for r in reports.iBabsKeyValue if r.Value == l.Value][0]
            # TODO: pagination for this?
            result = self.client.service.GetListReport(
                Sitename=self.source_definition['sitename'], ListId=l.Key,
                ReportId=report.Key, ActivePageNr=0, RecordsPerPage=100
            )
            for item in result.Data.diffgram[0].DocumentElement[0].results:
                dict_item = list_report_response_to_dict(item)
                dict_item['_ListName'] = result.ListName
                dict_item['_ReportName'] = result.ReportName
                print "%s: %s/%s - %s" % (
                    self.source_definition['sitename'],
                    dict_item['_ListName'], dict_item['_ReportName'],
                    dict_item['id'],)
                yield 'application/json', json.dumps(dict_item)
