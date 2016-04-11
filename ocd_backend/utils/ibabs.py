import re
import datetime


def _ibabs_to_dict(o, fields):
    """
    Converts an iBabs SOAP response to a JSON serializable dict
    """
    output = {}
    for f in fields.keys():
        v = getattr(o, f)
        if fields[f] is not None:
            if v is not None:
                output[f] = fields[f](v)
            else:
                output[f] = v
        else:
            output[f] = v
    return output


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


def meeting_to_dict(m):
    """
    Converts an iBabsMeeting to a JSON serializable dict
    """
    # TODO: add list items?
    fields = {
        'Id': None,
        'MeetingtypeId': None,
        'MeetingDate': lambda x: x.isoformat(),
        'StartTime': lambda x: unicode(x),
        'EndTime': lambda x: unicode(x),
        'Location': None,
        'Chairman': None,
        'Explanation': None,
        'PublishDate': lambda x: x.isoformat(),
        'MeetingItems': lambda x: [
            meeting_item_to_dict(y) if y is not None else [] for y in x[0]],
        'Documents': lambda x: [
            document_to_dict(y) if y is not None else [] for y in x[0]]
    }
    return _ibabs_to_dict(m, fields)


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
        'Documents': lambda x: [
            document_to_dict(y) if y is not None else [] for y in x[0]]
    }
    return _ibabs_to_dict(m, fields)


def meeting_type_to_dict(mt):
    """
    Converts an iBabsMeetingType to a JSON serializable dict
    """
    fields = {
        'Id': None,
        'Meetingtype': None,
        'Abbreviation': None,
    }
    return _ibabs_to_dict(mt, fields)


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
        'Documents': lambda x: [
            document_to_dict(y) if y is not None else [] for y in x[0]],
        'Values': lambda x: {
            unicode(y.Key): unicode(y.Value) if y.Value is not None else None for y in x}
    }
    return _ibabs_to_dict(m, fields)
