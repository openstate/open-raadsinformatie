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
    meeting_type_to_dict)


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
