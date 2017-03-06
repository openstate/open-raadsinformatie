import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin


class GemeenteOplossingenBaseExtractor(BaseExtractor, HttpRequestMixin):
    """
    A base extractor for the GemeenteOplossingen API. This base extractor just
    configures the base url to use for accessing the API.
    """

    def __init__(self, *args, **kwargs):
        super(GemeenteOplossingenBaseExtractor, self).__init__(*args, **kwargs)

        self.base_url = self.source_definition['base_url']


class GemeenteOplossingenCommitteesExtractor(GemeenteOplossingenBaseExtractor):
    """
    Extracts committees from the GemeenteOplossingen API.
    """

    def run(self):
        resp = self.http_session.get(
            u'%s/dmus' % self.base_url)

        if resp.status_code == 200:
            static_json = json.loads(resp.content)
            self.total = len(static_json)

            for dmu in static_json:
                yield 'application/json', json.dumps(dmu)


class GemeenteOplossingenMeetingsExtractor(GemeenteOplossingenBaseExtractor):
    """
    Extracts meetings from the GemeenteOplossingen API.
    """

    def run(self):
        months = 1  # Max 1 months intervals by default
        if 'months_interval' in self.source_definition:
            months = self.source_definition['months_interval']

        # by default only start for the latest period
        current_start = datetime.today() - relativedelta(months=months)
        if 'start_date' in self.source_definition:
            current_start = parse(self.source_definition['start_date'])

        end_date = datetime.today()  + relativedelta(months=months)  # End 1M+
        if 'end_date' in self.source_definition:
            end_date = parse(self.source_definition['end_date'])


        print "Getting all meetings for %s to %s" % (current_start, end_date,)

        meeting_count = 0
        while True:
            current_end = current_start + relativedelta(months=months)

            # If next current_end exceeds end_date then stop at end_date
            if current_end > end_date:
                current_end = end_date
                print "Next interval exceeds %s, months_interval not used" % end_date

            resp = self.http_session.get(
                u'%s/meetings?date_from=%i&date_to=%i' % (self.base_url, (current_start - datetime(1970, 1, 1)).total_seconds(), (current_end - datetime(1970, 1, 1)).total_seconds()))

            if resp.status_code == 200:
                static_json = json.loads(resp.content)
                self.total = len(static_json)

                for meeting in static_json:
                    yield 'application/json', json.dumps(meeting)
                    meeting_count += 1

            print "Now processing meetings %s months from %s to %s" % (months, current_start, current_end,)
            print "Extracted total of %d meetings." % (
                meeting_count)

            current_start = current_end + relativedelta(seconds=1)
            if current_start > end_date:  # Stop while loop if exceeded end_date
                break


class GemeenteOplossingenMeetingItemsExtractor(
        GemeenteOplossingenBaseExtractor):
    """
    Extracts meeting items from the GemeenteOplossingen API.
    """

    def run(self):
        current_start = datetime(2000, 1, 1)  # Start somewhere by default
        if 'start_date' in self.source_definition:
            current_start = parse(self.source_definition['start_date'])

        end_date = datetime.today()  # End today by default
        if 'end_date' in self.source_definition:
            end_date = parse(self.source_definition['end_date'])

        months = 6  # Max 6 months intervals by default
        if 'months_interval' in self.source_definition:
            months = self.source_definition['months_interval']

        print "Getting all meetingitems for %s to %s" % (current_start, end_date,)

        meeting_count = 0
        while True:
            current_end = current_start + relativedelta(months=months)

            # If next current_end exceeds end_date then stop at end_date
            if current_end > end_date:
                current_end = end_date
                print "Next interval exceeds %s, months_interval not used" % end_date

            resp = self.http_session.get(
                u'%s/meetings?date_from=%i&date_to=%i' % (self.base_url, (current_start - datetime(1970, 1, 1)).total_seconds(), (current_end - datetime(1970, 1, 1)).total_seconds()))

            if resp.status_code == 200:
                static_json = json.loads(resp.content)
                self.total = len(static_json)

                for meeting in static_json:
                    if 'items' in meeting:
                        for item in meeting['items']:

                            # Temporary hack to inherit meetingitem date from meeting
                            if 'date' not in item:
                                item['date'] = meeting['date']

                            kv = {meeting['id']: item}
                            yield 'application/json', json.dumps(kv)
                            meeting_count += 1

            print "Now processing meetingitems %s months from %s to %s" % (months, current_start, current_end,)
            print "Extracted total of %d meetingsitems." % (
                meeting_count)

            current_start = current_end + relativedelta(seconds=1)
            if current_start > end_date:  # Stop while loop if exceeded end_date
                break
