from ocd_backend.utils.misc import iterate, str_to_datetime, datetime_to_unixstamp


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

    def serialize(self, value, **kwargs):
        return value

    def __repr__(self):
        return '<%s %s>' % (self.get_prefix_uri(), self.__class__.__name__)


class Namespace(object):
    def __init__(self, namespace, prefix):
        self.namespace = namespace
        self.prefix = prefix

    def __str__(self):
        return self.prefix


class Property(PropertyBase):
    pass


class Instance(Property):
    def serialize(self, value, **kwargs):
        return value.get_prefix_uri()


class StringProperty(Property):
    def serialize(self, value, **kwargs):
        return unicode(value).strip()


class IntegerProperty(Property):
    pass


class DateTimeProperty(Property):
    def serialize(self, value, **kwargs):
        date_object = str_to_datetime(value)
        return datetime_to_unixstamp(date_object)


class ArrayProperty(Property):
    pass


class Relation(PropertyBase):
    def serialize(self, value, **kwargs):
        props = list()
        for _, item in iterate(value):
            if not item.__temporary__:
                # todo temporary fix for deflate recursion
                props.append(item.deflate(**kwargs))
            else:
                props.append(item.get_ori_id())

        if len(props) == 1:
            return props[0]
        return props
