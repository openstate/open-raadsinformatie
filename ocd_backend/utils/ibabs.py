def _ibabs_to_dict(o, fields, excludes=None):
    """
    Converts an iBabs SOAP response to a JSON serializable dict
    """
    if excludes is None:
        excludes = []
    output = {}
    for f in fields.keys():
        if f in excludes:
            continue
        v = getattr(o, f)
        if fields[f] is not None:
            if v is not None:
                output[f] = fields[f](v)
            else:
                output[f] = v
        else:
            output[f] = v
    return output


def vote_to_dict(v):
    """
    Converts an IBabs vote records to a JSON object.
    """

    fields = {
        'EntryId': lambda x: unicode(x),
        'GroupId': lambda x: unicode(x),
        'GroupName': lambda x: unicode(x),
        'UserId': lambda x: unicode(x),
        'UserName': lambda x: unicode(x),
        'Vote': None,
    }

    return _ibabs_to_dict(v, fields)


def votes_to_dict(vs):
    """
    Converts an array of IBabs votes to json objects.
    """

    return [vote_to_dict(v) for v in vs]


def document_to_dict(d):
    """
    Converts an iBabsDocument SOAP response to a JSON serializable dict
    """
    fields = {
        'Id': lambda x: unicode(x),
        'FileName': lambda x: unicode(x),
        'DisplayName': lambda x: unicode(x),
        'Confidential': None,
        'PublicDownloadURL': lambda x: unicode(x),
        'FileSize': lambda x: int(x) if x is not None else None
    }
    return _ibabs_to_dict(d, fields)


def meeting_to_dict(m, excludes=None):
    """
    Converts an iBabsMeeting to a JSON serializable dict
    """
    # TODO: add list items?
    if excludes is None:
        excludes = []
    fields = {
        'Id': None,
        'MeetingtypeId': None,
        'MeetingDate': lambda x: x.isoformat(),
        'StartTime': lambda x: unicode(x),
        'EndTime': lambda x: unicode(x),
        'Location': lambda x: unicode(x),
        'Chairman': lambda x: unicode(x),
        'Invitees': lambda x: [
            user_to_dict(y) if y is not None else [] for y in x[0]],
        'Attendees': lambda x: [
            user_to_dict(y) if y is not None else [] for y in x[0]],
        'Explanation': None,
        'PublishDate': lambda x: x.isoformat(),
        'MeetingItems': lambda x: [
            meeting_item_to_dict(y) if y is not None else [] for y in x[0]],
        'Documents': lambda x: [
            document_to_dict(y) if y is not None else [] for y in x[0]],
        'Webcast': lambda x: unicode(x['Code']),
    }
    return _ibabs_to_dict(m, fields, excludes)


def list_entry_to_dict(l):
    """
    Converts an iBabsListEntryBasic to a JSON serializable dict
    """
    fields = {
        'EntryId': lambda x: unicode(x),
        'EntryTitle': lambda x: unicode(x),
        'ListCanVote': None,
        'ListId': lambda x: unicode(x),
        'ListName': lambda x: unicode(x),
        'VoteResult': None,
        'VotesAgainst': None,
        'VotesInFavour': None,
    }
    return _ibabs_to_dict(l, fields)


def user_to_dict(u):
    """
    Converts an iBabsUserBasic to a JSON serializable dict
    """
    fields = {
        'UniqueId': lambda x: unicode(x),
        'Name': lambda x: unicode(x),
        'Emailaddress': lambda x: unicode(x),
    }
    return _ibabs_to_dict(u, fields)


def meeting_item_to_dict(m):
    """
    Converts an iBabsMeetingItem to a JSON serializable dict
    """
    fields = {
        'Id': None,
        'Features': None,
        'Title': None,
        'Explanation': None,
        'Confidential': None,
        'ListEntries': lambda x: [list_entry_to_dict(y) for y in (x[0] or [])],
        'Documents': lambda x: [
            document_to_dict(y) if y is not None else [] for y in x[0]]
    }
    return _ibabs_to_dict(m, fields)


def _list_response_field_to_val(r):
    if isinstance(r, list):
        return [unicode(l) for l in r]
    else:
        return unicode(r)


def list_report_response_to_dict(r):
    """
    Converts the output given by a row in the report to a JSON serializable
    dict
    """
    return {k[0]: _list_response_field_to_val(k[1]) for k in r}


# json.dumps(meeting_to_dict(m.Meetings[0][0]))


def list_entry_response_to_dict(m):
    """
    Converts an iBabsMeetingItem to a JSON serializable dict
    """
    fields = {
        'Message': None,
        'Status': None,
        'Documents': lambda x: [document_to_dict(y) if y is not None else [] for y in x.iBabsDocument],
        'Values': lambda x: {
            unicode(y.Key): unicode(y.Value) if y.Value is not None else None for y in x.KeyValueOfstringstring
        }
    }
    return _ibabs_to_dict(m, fields)
