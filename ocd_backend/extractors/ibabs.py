import json
import re

from zeep.client import Client, Settings
from zeep.helpers import serialize_object

from ocd_backend import settings
from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.utils.http import HttpRequestMixin
from ocd_backend.utils.ibabs import (
    meeting_to_dict, list_report_response_to_dict,
    list_entry_response_to_dict, votes_to_dict)

log = get_source_logger('extractor')


class IBabsBaseExtractor(BaseExtractor):
    """
    A base extractor for the iBabs SOAP service. Instantiates the client
    and configures the right port tu use.
    """

    def run(self):
        pass

    def __init__(self, *args, **kwargs):
        super(IBabsBaseExtractor, self).__init__(*args, **kwargs)

        try:
            ibabs_wsdl = self.source_definition['wsdl']
        except Exception as e:
            ibabs_wsdl = settings.IBABS_WSDL

        soap_settings = Settings(extra_http_headers={'User-Agent': settings.USER_AGENT})
        self.client = Client(ibabs_wsdl,
                             port_name='BasicHttpsBinding_IPublic',
                             settings=soap_settings)


class IBabsCommitteesExtractor(IBabsBaseExtractor):
    """
    Extracts committees from the iBabs SOAP service. This is done by checking
    if the meeting type contains the word 'commissie' or a custom 'committee_designator'
    which can be defined in the source file.
    """

    def run(self):
        committee_designator = self.source_definition.get(
            'committee_designator', 'commissie')
        log.debug("[%s] Getting ibabs committees with designator: %s" %
                  (self.source_definition['index_name'], committee_designator))
        meeting_types = self.client.service.GetMeetingtypes(
            self.source_definition['sitename']
        )

        if meeting_types.Meetingtypes:
            total_count = 0
            for mt in meeting_types.Meetingtypes['iBabsMeetingtype']:
                if committee_designator in mt.Meetingtype.lower():
                    committee = serialize_object(mt, dict)
                    yield 'application/json', \
                          json.dumps(committee), \
                          committee['Id'], \
                          'used_file_placeholder'
                    total_count += 1
            log.info("[%s] Extracted total of %d ibabs committees." % (self.source_definition['index_name'], total_count))
        else:
            log.warning('[%s] SOAP service error: %s' % (self.source_definition['index_name'], meeting_types.Message))


class IBabsMeetingsExtractor(IBabsBaseExtractor):
    """
    Extracts meetings from the iBabs SOAP service. The source definition should
    state which kind of meetings should be extracted.
    """

    def _meetingtypes_as_dict(self):
        meeting_types = self.client.service.GetMeetingtypes(self.source_definition['sitename'])

        if meeting_types.Meetingtypes:
            for o in meeting_types.Meetingtypes['iBabsMeetingtype']:
                include_regex = self.source_definition.get('include', None)
                if include_regex and not re.search(include_regex, o.Description):
                    continue

                exclude_regex = self.source_definition.get('exclude', None)
                if exclude_regex and re.search(exclude_regex, o.Description):
                    continue

                meeting_types[o.Id] = o.Description
            return meeting_types
        else:
            log.warning('[%s] SOAP service error: %s' % (self.source_definition['index_name'], meeting_types.Message))

    def run(self):
        meeting_count = 0
        meetings_skipped = 0
        for start_date, end_date in self.interval_generator():
            log.debug("[%s] Now processing meetings from %s to %s" % (
                self.source_definition['sitename'], start_date, end_date,))

            meetings = self.client.service.GetMeetingsByDateRange(
                Sitename=self.source_definition['sitename'],
                StartDate=start_date.strftime('%Y-%m-%dT%H:%M:%S'),
                EndDate=end_date.strftime('%Y-%m-%dT%H:%M:%S'),
                MetaDataOnly=False)

            meeting_types = self._meetingtypes_as_dict()

            if meetings.Meetings:
                for meeting in meetings.Meetings['iBabsMeeting']:

                    meeting_dict = serialize_object(meeting, dict)
                    # Convert unserializable keys to text
                    meeting_dict['PublishDate'] = meeting_dict['PublishDate'].isoformat()
                    meeting_dict['MeetingDate'] = meeting_dict['MeetingDate'].isoformat()

                    # sometimes a meeting type is not actually a meeting for some
                    # reason. Let's ignore these for now
                    if meeting_dict['MeetingtypeId'] not in meeting_types:
                        meetings_skipped += 1
                        continue

                    meeting_dict['Meetingtype'] = meeting_types[meeting_dict['MeetingtypeId']]
                    yield 'application/json', \
                          json.dumps(meeting_dict), \
                          meeting_dict['Id'], \
                          meeting_dict

                    meeting_count += 1

        log.info("[%s] Extracted total of %d ibabs meetings. Also skipped %d meetings in total." %
                 (self.source_definition['sitename'], meeting_count, meetings_skipped,))


class IBabsReportsExtractor(IBabsBaseExtractor):
    """
    Extracts reports from the iBabs SOAP Service. The source definition should
    state which kind of reports should be extracted.
    """

    def run(self):
        lists = self.client.service.GetLists(Sitename=self.source_definition['sitename'])

        if len(lists) < 1:
            log.info("[%s] No ibabs reports defined" % (self.source_definition['sitename'],))
            return

        selected_lists = []
        for l in lists:
            include_regex = self.source_definition.get('include', None) or self.source_definition['regex']
            if not re.search(include_regex, l.Value.lower()):
                continue
            exclude_regex = self.source_definition.get('exclude', None) or r'^$'
            if re.search(exclude_regex, l.Value.lower()):
                continue
            selected_lists.append(l)

        total_yield_count = 0
        for l in selected_lists:
            reports = self.client.service.GetListReports(Sitename=self.source_definition['sitename'], ListId=l.Key)
            report = reports[0]
            if len(reports) > 1:
                try:
                    report = [
                        r for r in reports if r.Value == l.Value][0]
                except IndexError as e:
                    pass

            active_page_nr = 0
            max_pages = self.source_definition.get('max_pages', 1)
            per_page = self.source_definition.get('per_page', 100)
            result_count = per_page
            total_count = 0
            yield_count = 0
            while (active_page_nr < max_pages) and (result_count == per_page):
                try:
                    result = self.client.service.GetListReport(
                        Sitename=self.source_definition['sitename'],
                        ListId=l.Key, ReportId=report.Key,
                        ActivePageNr=active_page_nr, RecordsPerPage=per_page)
                except Exception as e:  # most likely an XML parse problem
                    log.warning("[%s] Could not parse page %s correctly!: %s" % (
                        self.source_definition['sitename'], active_page_nr, e.message))
                    result = None
                result_count = 0
                # log.debug("* %s: %s/%s - %d/%d" % (
                #     self.source_definition['sitename'],
                #     result.ListName, result.ReportName,
                #     active_page_nr, max_pages,))

                if result is not None:
                    try:
                        document_element = result.Data.diffgram[0].DocumentElement[0]
                    except AttributeError as e:
                        document_element = None
                    except IndexError as e:
                        document_element = None
                else:
                    document_element = None

                if document_element is None:
                    log.debug("[%s] No correct document element for this page!" % self.source_definition['sitename'])
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
                    # if dict_item['kenmerk'][0].startswith('2018 M67'):
                    #     log.debug(dict_item)
                    # try:
                    #     # this should be the motion's unique identifier
                    #     log.debug(full_normalized_motion_id(
                    #         dict_item['_Extra']['Values'][u'Onderwerp']))
                    # except (KeyError, AttributeError) as e:
                    #     pass
                    yield 'application/json', json.dumps(dict_item), dict_item['id'][0], dict_item
                    yield_count += 1
                    total_yield_count += 1
                    result_count += 1
                total_count += result_count
                active_page_nr += 1
            log.debug("[%s] Report: %s -- total %s, results %s, yielded %s" % (
                self.source_definition['sitename'], l.Value, total_count, result_count, yield_count))

        log.info("[%s] Extracted total of %s ibabs reports yielded" % (
            self.source_definition['sitename'], total_yield_count))


class IbabsPersonsExtractor(IBabsBaseExtractor):
    """
    Extracts person profiles from the iBabs SOAP service.
    """

    def run(self):
        users = self.client.service.GetUsers(
            self.source_definition['sitename']
        )

        if users.Users:
            total_count = 0
            for user in users.Users['iBabsUserBasic']:
                identifier = user['UniqueId']

                user_details = self.client.service.GetUser(
                    self.source_definition['sitename'],
                    identifier
                )

                profile = serialize_object(user_details.User.PublicProfile, dict)
                # Picture can't be JSON-encoded so we delete it
                del profile['Picture']

                yield 'application/json', json.dumps(profile), profile['UserId'], profile
                total_count += 1

            log.info("[%s] Extracted total of %s ibabs persons" % (self.source_definition['index_name'], total_count))

        elif users.Message == 'No users found!':
            log.info('[%s] No ibabs persons were found' % self.source_definition['index_name'])
        else:
            log.warning('[%s] SOAP service error: %s' % (self.source_definition['index_name'], users.Message))


class IBabsVotesMeetingsExtractor(IBabsBaseExtractor):
    """
    Extracts meetings with vote information from the iBabs SOAP service. The
    source definition should state which kind of meetings should be extracted.
    """

    def _meetingtypes_as_dict(self):
        return {
            o.Id: o.Description for o in
            self.client.service.GetMeetingtypes(self.source_definition['sitename']).Meetingtypes[0]
        }

    def valid_meeting(self, meeting):
        """
        Is the meeting valid?
        """
        return True

    def process_meeting(self, meeting):
        """
        Process the meeting and return array of objects.
        """
        return [meeting]

    @staticmethod
    def filter_out_processed_meeting(meeting):
        """
        Should the processed result be filtered out? Return false if not.
        """
        return False

    def run(self):
        dates = [x for x in self.interval_generator()]
        if self.source_definition.get('reverse_chronological', False):
            dates.reverse()

        meeting_count = 0
        vote_count = 0
        passed_vote_count = 0

        for start_date, end_date in dates:
            meetings = self.client.service.GetMeetingsByDateRange(
                Sitename=self.source_definition['sitename'],
                StartDate=start_date,
                EndDate=end_date,
                MetaDataOnly=False)

            meeting_types = self._meetingtypes_as_dict()
            meeting_sorting_key = self.source_definition.get(
                'meeting_sorting', 'MeetingDate')

            if meetings.Meetings is not None:
                sorted_meetings = sorted(
                    meetings.Meetings[0],
                    key=lambda m: getattr(m, meeting_sorting_key))
            else:
                sorted_meetings = []

            processed = []
            for meeting in sorted_meetings:
                meeting_dict = meeting_to_dict(meeting)
                # Getting the meeting type as a string is easier this way ...
                # log.debug(meeting_dict['Id'])
                meeting_dict['Meetingtype'] = meeting_types[
                    meeting_dict['MeetingtypeId']]

                kv = self.client.factory.create('ns0:iBabsKeyValue')  # pylint: disable=no-member
                kv.Key = 'IncludeMeetingItems'
                kv.Value = True

                kv2 = self.client.factory.create('ns0:iBabsKeyValue')  # pylint: disable=no-member
                kv2.Key = 'IncludeListEntries'
                kv2.Value = True

                kv3 = self.client.factory.create('ns0:iBabsKeyValue')  # pylint: disable=no-member
                kv3.Key = 'IncludeMeetingItems'
                kv3.Value = True

                params = self.client.factory.create('ns0:ArrayOfiBabsKeyValue')  # pylint: disable=no-member
                params.iBabsKeyValue.append(kv)
                params.iBabsKeyValue.append(kv2)
                params.iBabsKeyValue.append(kv3)

                vote_meeting = self.client.service.GetMeetingWithOptions(
                    Sitename=self.source_definition['sitename'],
                    MeetingId=meeting_dict['Id'],
                    Options=params)
                meeting_dict_short = meeting_to_dict(vote_meeting.Meeting)
                # log.debug(meeting_dict_short['MeetingDate'])
                if meeting_dict_short['MeetingItems'] is None:
                    continue
                for mi in meeting_dict_short['MeetingItems']:
                    if mi['ListEntries'] is None:
                        continue
                    for le in mi['ListEntries']:
                        votes = self.client.service.GetListEntryVotes(
                            Sitename=self.source_definition['sitename'],
                            EntryId=le['EntryId'])
                        if votes.ListEntryVotes is None:
                            votes = []
                        else:
                            votes = votes_to_dict(votes.ListEntryVotes[0])
                        # log.debug(votes)
                        result = {
                            'meeting': meeting_dict,
                            'entry': le,
                            'votes': votes
                        }
                        vote_count += 1
                        if self.valid_meeting(result):
                            processed += self.process_meeting(result)
                meeting_count += 1

            # log.debug(processed)
            for result in processed:
                yield 'application/json', json.dumps(result), 'entity_placeholder', result
                passed_vote_count += 1
            log.debug("[%s] Now processing meetings from %s to %s" % (self.source_definition['index_name'], start_date, end_date,))

        log.info("[%s] Extracted total of %d ibabs meetings and passed %s out of %d voting rounds." % (
            self.source_definition['index_name'], meeting_count, passed_vote_count, vote_count,))


class IBabsMostRecentCompleteCouncilExtractor(IBabsVotesMeetingsExtractor, HttpRequestMixin, FrontendAPIMixin):
    """
    Gets a voting record where the number of voters is complete ...
    """

    def valid_meeting(self, meeting):
        if meeting['votes'] is not None:
            try:
                return (
                        len(meeting['votes']) ==
                        int(self.source_definition['council_members_count']))
            except ValueError:
                pass
        return False

    def process_meeting(self, meeting):
        meeting_count = getattr(self, 'meeting_count', 0)
        max_meetings = self.source_definition.get('max_processed_meetings', 1)
        entity_type = self.source_definition.get(
            'vote_entity', 'organizations')
        result = None
        if (max_meetings <= 0) or (meeting_count < max_meetings):
            setattr(self, 'meeting_count', meeting_count + 1)
            log.debug("[%s] Processing meeting %d" % (self.source_definition['sitename'], meeting_count,))
            council = self.api_request(
                self.source_definition['index_name'], 'organizations',
                classification=u'Council')
            groups = {
                v['GroupId']: {
                    'id': v['GroupId'],
                    'classification': 'Party',
                    'name': v['GroupName'],
                    'identifiers': [
                        {
                            'id': u'id-g-%s' % (v['GroupId'],),
                            'identifier': v['GroupId'],
                            'scheme': u'iBabs'
                        }
                    ],
                    'meta': {
                        '_type': 'organizations'
                    }
                } for v in meeting['votes']}
            if council is None:
                groups.update(
                    {u'council': {
                        'id': 'council',
                        'classification': 'Council',
                        'name': u'Gemeenteraad',
                        'identifiers': [
                        ],
                        'meta': {
                            '_type': 'organizations'
                        }
                    }})
            else:
                groups[u'council'] = council[0]
            persons = {
                v['UserId']: {
                    'id': v['UserId'],
                    'name': v['UserName'],
                    'identifiers': [
                        {
                            'id': u'id-p-%s' % (v['UserId'],),
                            'identifier': v['UserId'],
                            'scheme': u'iBabs'
                        }
                    ],
                    'meta': {
                        '_type': 'persons'
                    }
                } for v in meeting['votes']}
            if entity_type == 'organizations':
                # process parties
                unique_groups = list(set(groups.keys()))
                for g in unique_groups:
                    # log.debug(meeting['votes'])
                    groups[g]['memberships'] = [
                        {
                            'person_id': v['UserId'],
                            'person': persons[v['UserId']],
                            'organization_id': g,
                            'organization': {
                                'id': g,
                                'classification': 'Party',
                                'name': groups[g]['name'],
                                'identifiers': [
                                    {
                                        'id': u'id-g-%s' % (g,),
                                        'identifier': g,
                                        'scheme': u'iBabs'
                                    }
                                ]
                            }
                        }
                        for v in meeting['votes'] if ((v['GroupId'] == g) or (g == u'council'))]
                result = groups.values()
            elif entity_type == 'persons':
                # process persons
                for v in meeting['votes']:
                    p = v['UserId']
                    persons[p]['memberships'] = [
                        {
                            'person_id': p,
                            'person': {
                                'id': p,
                                'name': persons[p]['name'],
                                'identifiers': [
                                    {
                                        'id': u'id-p-%s' % (p,),
                                        'identifier': p,
                                        'scheme': u'iBabs'
                                    }
                                ]
                            },
                            'organization_id': v['GroupId'],
                            'organization': groups[v['GroupId']]
                        }]
                result = persons.values()
            return result
        else:
            return []
