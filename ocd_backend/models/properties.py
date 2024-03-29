from ocd_backend.models.misc import Namespace, Uri, Url
from ocd_backend.utils.misc import str_to_datetime


class PropertyBase:
    """The base property all properties and relations should inherit from."""

    def __init__(self, ns, name, required=False, ignore_for_loader=None):
        assert issubclass(ns, Namespace)
        self.ns = ns
        self.required = required
        self.ignore_for_loader = ignore_for_loader

        if self.ignore_for_loader and not isinstance(self.ignore_for_loader, list):
            raise ValueError('ignore_for_loader should be a list of loader classes.')

        self._name = name

    def absolute_uri(self):
        """Returns a full uri."""
        return '{}{}'.format(self.ns.uri, self._name)

    def compact_uri(self):
        """Returns a prefixed uri like prefix:name."""
        return '{}:{}'.format(self.ns.prefix, self._name)

    # def term(self):
    #     """Returns the name of the property"""
    #     return self._name

    @staticmethod
    def sanitize(value):
        """This method is used to clean the value when initialized.

        The default is to do nothing and return. This method should be
        overrided in a subclass with subclass-specific behaviour.
        """
        return value

    def __repr__(self):
        return '<{} {}>'.format(self.compact_uri(), self.__class__.__name__)


# Properties
class Property(PropertyBase):
    """Defines a superclass for all property types."""
    pass


class StringProperty(Property):
    """A property which defines an (unicode) str type."""

    @staticmethod
    def sanitize(value):
        """Strip the value of spaces and make it unicode"""
        if isinstance(value, Uri) or isinstance(value, Url):
            return value

        if value:
            return str(value).strip()


class URLProperty(StringProperty):
    """A property which defines a URL."""
    pass


class IntegerProperty(Property):
    """A property which defines an int type."""

    @staticmethod
    def sanitize(value):
        """Force cast to int. This will fail by design if not castable to int"""
        if value:
            return int(value)


class FloatProperty(Property):
    """A property which defines an int type."""

    @staticmethod
    def sanitize(value):
        """Force cast to float. This will fail by design if not castable to int"""
        if value:
            return float(value)


class DateProperty(Property):
    """A property which defines a date type."""

    @staticmethod
    def sanitize(value):
        """Strip the value of spaces and make it unicode"""
        if value:
            return str_to_datetime(value)


class DateTimeProperty(Property):
    """A property which defines a datetime type."""

    @staticmethod
    def sanitize(value):
        """Strip the value of spaces and make it unicode"""
        if value:
            return str_to_datetime(value)


class NestedProperty(Property):
    """A property that will contain nested children"""
    pass


class ArrayProperty(Property):
    """A property which defines a list type."""
    pass


class JsonProperty(Property):
    """A property which contains a json string"""
    pass


# Relations
class Relation(PropertyBase):
    """Defines a superclass for all relation types."""
    pass


class OrderedRelation(Relation):
    """A relation which defines an relation that has a specified order"""
    pass
