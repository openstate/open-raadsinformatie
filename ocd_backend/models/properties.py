from .misc import Namespace
from ocd_backend.utils.misc import str_to_datetime

class PropertyBase(object):
    """The base propery all properties and relations should inherit from."""

    def __init__(self, ns, name, required=False):
        assert issubclass(ns, Namespace)
        self.ns = ns
        self.required = required
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
        if value:
            return unicode(value).strip()


class IntegerProperty(Property):
    """A property which defines an int type."""

    @staticmethod
    def sanitize(value):
        """Force cast to int. This will fail by design if not castable to int"""
        if value:
            return int(value)


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


class ArrayProperty(Property):
    """A property which defines a list type."""
    pass


# Relations
class Relation(PropertyBase):
    """Defines a superclass for all relation types."""
    pass


class OrderedRelation(Relation):
    """A relation which defines an relation that has a specified order"""
    pass
