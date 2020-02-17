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
        'EntryId': lambda x: str(x),
        'GroupId': lambda x: str(x),
        'GroupName': lambda x: str(x),
        'UserId': lambda x: str(x),
        'UserName': lambda x: str(x),
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
        'Id': lambda x: str(x),
        'FileName': lambda x: str(x),
        'DisplayName': lambda x: str(x),
        'Confidential': None,
        'PublicDownloadURL': lambda x: str(x),
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
        'StartTime': lambda x: str(x),
        'EndTime': lambda x: str(x),
        'Location': lambda x: str(x),
        'Chairman': lambda x: str(x),
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
        'Webcast': lambda x: str(x['Code']),
    }
    return _ibabs_to_dict(m, fields, excludes)


def list_entry_to_dict(l):
    """
    Converts an iBabsListEntryBasic to a JSON serializable dict
    """
    fields = {
        'EntryId': lambda x: str(x),
        'EntryTitle': lambda x: str(x),
        'ListCanVote': None,
        'ListId': lambda x: str(x),
        'ListName': lambda x: str(x),
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
        'UniqueId': lambda x: str(x),
        'Name': lambda x: str(x),
        'Emailaddress': lambda x: str(x),
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
        return [str(l) for l in r]
    else:
        return str(r)


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
            str(y.Key): str(y.Value) if y.Value is not None else None for y in x.KeyValueOfstringstring
        }
    }
    return _ibabs_to_dict(m, fields)


def translate_position(position):
    """
    Returns the position as a float if it is castable to float. If the position is not castable to float,
    removes all non-digits from the string and casts to float, and also returns the original position as the
    second return value so it can be stored as raw_position.

    If the position is not castable to float even after removing all non-digits, returns None and the original
    position as the second return value so it can be stored as raw_position.

    If the input position is None, returns None for both return values.

    Examples:
        '1'    -> 1.0, None
        '1.1'  -> 1.1, None
        '1A'   -> 1.0, '1A'
        '1.4C' -> 1.4, '1.4C'
        'A'    -> None, 'A'
        None   -> None, None
    """
    if position is None:
        return None, None

    try:
        return float(position), None
    except ValueError:
        try:
            return float(''.join([c for c in position if c.isdigit() or c == "."])), position
        except ValueError:
            return None, position
