from string import Formatter
import glob
import json

class MissingTemplateTag(KeyError):
    """Thrown when a template tag is missing in the configuration"""

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
