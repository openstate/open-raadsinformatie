import iso8601
from dateutil.parser import parse
from datetime import datetime


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

    def serialize(self, value):
        return value

    def __repr__(self):
        return '<%s %s>' % (self.get_prefix_uri(), self.__class__.__name__)

# class Id(PropertyBase):
#     def __init__(self):
#         self.name = '@id'
#         super(Id, self).__init__()
#
#
# class Type(PropertyBase):
#     def __init__(self, ns):
#         if not isinstance(ns, Namespace):
#             raise Exception("Not a valid Namespace")
#         self.ns = ns
#         super(Type, self).__init__()


class Namespace(object):
    def __init__(self, namespace, prefix):
        self.namespace = namespace
        self.prefix = prefix

    def __str__(self):
        return self.prefix


class Property(PropertyBase):
    pass


class Instance(Property):
    pass


class StringProperty(Property):
    pass


class IntegerProperty(Property):
    pass


class DateTimeProperty(Property):

    def serialize(self, value):
        if isinstance(value, datetime):
            return value.strftime("%s")

        try:
            return parse(value).strftime("%s")
        except: pass

        try:
            return iso8601.parse_date(value).strftime("%s")
        except iso8601.ParseError: pass

        try:
            datetime.fromtimestamp(float(value))
            return value
        except: pass

        raise


class ArrayProperty(Property):

    def serialize(self, value):
        return value.deflate(namespaces=True, props=True, rels=True)


class Relation(PropertyBase):
    pass
