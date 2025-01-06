import datetime
import glob
import importlib
import re
import json
import codecs
from hashlib import sha1
from string import Formatter
from urllib.parse import urlparse
from functools import reduce

import pytz
import iso8601
# noinspection PyUnresolvedReferences
import translitcodec  # used for encoding, search 'translit'
from dateutil.parser import parse

from ocd_backend.exceptions import MissingTemplateTag, InvalidDatetime
from ocd_backend.settings import TIMEZONE

class ExtendedFormatter(Formatter):
    """An extended format string formatter
    Formatter with extended conversion symbol
    See: https://stackoverflow.com/a/46160537/5081021
    """

    def convert_field(self, value, conversion):
        """ Extend conversion symbol
        Following additional symbol has been added
        * c: convert to string and capitalize
        * l: convert to string and low case
        * u: convert to string and up case

        default are:
        * s: convert with str()
        * r: convert with repr()
        * a: convert with ascii()
        """

        if conversion == "c":
            return str(value).capitalize()
        elif conversion == "u":
            return str(value).upper()
        elif conversion == "l":
            return str(value).lower()
        # Do the default conversion or raise error if no matching conversion found
        super(ExtendedFormatter, self).convert_field(value, conversion)

        # return for None case
        return value


def load_sources_config(path):
    """Loads a JSON file(s) containing the configuration of the available
    sources.

    :param path: the path of the JSON file(s) wildcards * enabled.
    :type path: str.
    """

    def sort_source_keys(key_name):
        """Sort importance of specified key"""
        try:
            if key_name[0] == 'key':
                return int(0)
            if str(key_name[1]).startswith('{key'):
                return int(1)
            if type(key_name[1]) == list or type(key_name[1]) == dict:
                return int(4)
            if '{' in str(key_name[1]):
                return int(2)
        except AttributeError:
            pass
        return int(3)

    def replace_tags(data, chain=None):
        """Replace tags by higher level defined values in yaml files."""
        if type(data) == dict:
            if not chain or 'key' in data:
                chain = dict()
            chain.update(data)

            new_data = dict()
            for key, value in sorted(data.items(), key=sort_source_keys):
                if key[0:1] == '_':
                    continue

                if isinstance(value, str):
                    try:
                        new_data[key] = ExtendedFormatter().format(value, **chain)
                        chain[key] = new_data[key]
                    except KeyError as e:
                        raise MissingTemplateTag('Missing template tag %s in configuration for key \'%s\'' % (e, key))
                else:
                    chain[key] = value
                    new_data[key] = replace_tags(value, chain)
            return new_data
        elif type(data) == list:
            new_data = list()
            for value in data:
                new_data.append(replace_tags(value, chain))
            return new_data
        else:
            return data

    from yaml import load
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    result = {}
    for filename in glob.glob(path):
        try:
            ext = filename[-4:]
            with open(filename) as f:
                if ext == 'yaml':
                    loaded_data = load(f, Loader=Loader)
                    loaded_data = replace_tags(loaded_data)

                    for data_key, entry in loaded_data.items():
                        result[data_key] = entry
                elif ext == 'json':
                    for entry in json.load(f):
                        result[entry['id']] = entry

        except IOError as e:
            e.strerror = 'Unable to load sources configuration file (%s)' % (
                e.strerror,)
            raise

    return result


def load_object(path):
    """Load an object given it's absolute object path, and return it.

    The object can be a class, function, variable or instance.

    :param path: absolute object path (i.e. 'ocd_backend.extractor.BaseExtractor')
    :type path: str.
    """
    try:
        dot = path.rindex('.')
    except ValueError:
        raise ValueError("Error loading object '%s': not a full path" % path)

    m, name = path[:dot], path[dot + 1:]
    try:
        mod = importlib.import_module(m)
    except ImportError as e:
        raise ImportError("Error loading object '%s': %s" % (path, e))

    try:
        obj = getattr(mod, name)
    except AttributeError:
        raise NameError("Module '%s' doesn't define any object named '%s'" % (
            m, name))

    return obj


def parse_date(regexen, date_str):
    """
        Parse a messy string into a granular date

        `regexen` is of the form [ (regex, (granularity, groups -> datetime)) ]
    """
    if date_str:
        for reg, (gran, dater) in regexen:
            m = re.match(reg, date_str)
            if m:
                try:
                    return gran, dater(m.groups())
                except ValueError:
                    return 0, None
    return 0, None


def parse_date_span(regexen, date1_str, date2_str):
    """
        Parse a start & end date into a (less) granular date

        `regexen` is of the form [ (regex, (granularity, groups -> datetime)) ]
    """
    date1_gran, date1 = parse_date(regexen, date1_str)
    date2_gran, date2 = parse_date(regexen, date2_str)

    if date2:
        # TODO: integrate both granularities
        if (date1_gran, date1) == (date2_gran, date2):
            return date1_gran, date1
        if (date2 - date1).days < 5 * 365:
            return 4, date1
        if (date2 - date1).days < 50 * 365:
            return 3, date1
        if (date2 - date1).days >= 50 * 365:
            return 2, date1
    else:
        return date1_gran, date1


class DatetimeJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder that can handle ``datetime.datetime``, ``datetime.date`` and
    ``datetime.timedelta`` objects.
    """

    def default(self, o):  # pylint: disable=method-hidden
        if isinstance(o, datetime.datetime) or isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.timedelta):
            return (datetime.datetime.min + o).time().isoformat()
        else:
            return super(DatetimeJSONEncoder, self).default(o)


json_encoder = DatetimeJSONEncoder()

class HashUtils:
    def create_hash_key(self, provider, site_name, item_type, id):
        h = sha1()
        hash_key = "%s|%s|%s|%s" % (provider, site_name, item_type, id)
        h.update(hash_key.encode('ascii', 'replace'))
        return h.hexdigest()

hash_utils = HashUtils()

_punct_re = re.compile(r'[\t\r\n !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim='-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(str(text).lower()):
        word = codecs.encode(word, 'translit/long')
        if word:
            result.append(word)
    return delim.join(result)


def propagate_chain_get(terminal_node, timeout=None):
    current_node = terminal_node

    parents = list()
    while current_node.parent:
        current_node = current_node.parent
        parents.append(current_node)

    for node in reversed(parents):
        try:
            node.get(propagate=True, timeout=timeout)
        except Exception:
            pass


def iterate(item, parent=None):
    if isinstance(item, dict):
        for key, dict_item in item.items():
            for value in iterate(dict_item, key):
                yield value
    elif isinstance(item, list):
        for list_item in item:
            for value in iterate(list_item, parent):
                yield value
    elif isinstance(item, tuple):
        for tuple_item in item:
            for value in iterate(tuple_item, parent):
                yield value
    else:
        yield parent, item,


def str_to_datetime(date_str):
    """
    Convert a string to a datetime without knowing what
    kind of formatting to expect
    :param date_str: some form of date string
    :return: datetime
    """
    if isinstance(date_str, datetime.datetime):
        # It appears to be a datetime object
        return date_str

    try:
        # Try to parse most forms with dateutil
        # fuzzy will ignore weird characters
        date_object = parse(date_str, fuzzy=True)
        return localize_datetime(date_object)
    except ValueError:
        pass

    try:
        # Try to parse it as a unix timestamp
        utc = datetime.datetime.utcfromtimestamp(float(date_str))
        return utc.replace(tzinfo=pytz.utc)
    except (TypeError, ValueError):
        pass

    # If this point is reached then we could not convert it
    raise InvalidDatetime("Cannot convert '%s' to datetime", date_str)


def localize_datetime(date):
    if date.tzinfo:
        return date

    tz = pytz.timezone(TIMEZONE)
    return tz.localize(date)


def strip_scheme(url):
    parsed = urlparse(url)
    scheme = "%s://" % parsed.scheme
    return parsed.geturl().replace(scheme, '', 1)


def deep_get(item, *keys):
    """Based on https://stackoverflow.com/a/36131992/5081021"""

    def inner(d, key):
        try:
            return d[key]
        except (KeyError, IndexError, TypeError):
            return None

    return reduce(inner, keys, item)


def compare_insensitive(a, b):
    """Compares insensitive if a contains b"""
    if a is None or b is None:
        return

    return b.lower() in a.lower()

def is_valid_iso8601_date(s):
    if s is None:
        return False
    if not isinstance(s, str):
        return False
    result = True
    try:
        iso8601.parse_date(s)
    except iso8601.iso8601.ParseError as e:
        result = False
    return result
