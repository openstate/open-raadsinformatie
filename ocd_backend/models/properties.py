from .namespace import Namespace


class PropertyBase(object):
    def __init__(self, ns, local_name, required=False):
        if not isinstance(ns, Namespace):
            raise Exception("Not a valid Namespace")

        self.ns = ns
        self.local_name = local_name
        self.required = required

    def get_full_uri(self):
        return '%s%s' % (self.ns.namespace, self.local_name)

    def get_prefix_uri(self):
        return '%s:%s' % (self.ns.prefix, self.local_name)

    def get_name(self):
        return self.local_name

    @staticmethod
    def sanitize(value):
        return value

    def __repr__(self):
        return '<%s %s>' % (self.get_prefix_uri(), self.__class__.__name__)


class Property(PropertyBase):
    pass


class StringProperty(Property):
    @staticmethod
    def sanitize(value):
        return unicode(value).strip()


class IntegerProperty(Property):
    @staticmethod
    def sanitize(value):
        return int(value)


class DateTimeProperty(Property):
    pass


class ArrayProperty(Property):
    pass


class InlineRelation(Property):
    pass


class Relation(PropertyBase):
    pass


class OrderedRelation(Relation):
    pass
