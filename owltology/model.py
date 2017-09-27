from hashlib import sha1
import json
import re
from json import JSONEncoder
import datetime
import property


class ModelBaseMetaclass(type):
    # DO CHECKING FOR PROPERTYBASE SUBCLASSING IN NEW
    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        fields = dict()
        for key, value in list(attrs.items()):
            if isinstance(value, property.PropertyBase):
                fields[key] = value
                #attrs.pop(key)
        attrs['fields'] = fields

        # attr = getattr(self, key)
        # if not isinstance(attr, PropertyBase):
        #     raise ValueError('Predefined attribute \'%s\' of class %s is not a'
        #                      ' subclass of PropertyBase' % (key, type(attr).__name__))

        new_class = super(ModelBaseMetaclass, mcs).__new__(mcs, name, bases, attrs)

        # Walk through the MRO.
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, 'fields'):
                fields.update(base.fields)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in fields:
                    fields.pop(attr)

        new_class.fields = fields

        return new_class

class ModelBase(object):
    __metaclass__ = ModelBaseMetaclass
    fields = dict()

    NAMESPACE = None

    _id = property.Id()  # _id is serialized to @id

    def get_object_id(self, object_id):
        hash_content = u'%ss-%s' % (self, object_id)
        return sha1(hash_content.decode('utf8')).hexdigest()

    def plural(self):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self._type)
        return u'%ss' % re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def get_relative_url(self):
        return u'../%s/%s' % (self.plural(), self._id)

    def encode(self):
        return self.get_relative_url()

    def __setattr__(self, key, value):
        #print self.fields
        #print self.__class__.__dict__.keys()
        if key not in self.fields:
            raise AttributeError('\'%s\' object has no predefined attribute %s'
                                % (self.__class__.__name__, key,))

        super(ModelBase, self).__setattr__(key, value)

    def __init__(self, object_id=None, hidden=False):
        # Setting defaults for all fields
        for key, field in self.fields.items():
            self.__dict__[key] = field.default

        object_id = self.get_object_id(object_id)
        if not object_id:
            object_id = 'abc'

        self._id = object_id
        self._type = self.__class__.__name__
        self._hidden = hidden
        self.oriIdentifier = object_id

    def __iter__(self):
        self.validate()
        context = dict()
        for key, field in self.fields.items():
            if key in self.__dict__: # !!
                obj = getattr(type(self), key)

                try:
                    value = self.__dict__[key]
                    if value:
                        if hasattr(obj, 'ns'):
                            context[obj.ns.short] = obj.ns.namespace

                        if hasattr(obj, 'context'):
                            k, v = obj.context()
                            context[k] = v

                        yield obj.__json__(value)
                except ValueError, e:
                    print '__json__ value error skipping: ', e
                    continue

        yield '@context', context,

    def to_json(self):
        return ModelJSONEncoder().encode(dict(self))

    def validate(self):
        for key, field in self.fields.items():
            obj = getattr(type(self), key)
            value = self.__dict__.get(key, None)

            obj.validate_property(value)
        return True


class ModelJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime) or isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.timedelta):
            return (datetime.datetime.min + o).time().isoformat()
        elif isinstance(o, ModelBase):
            #return o.__json__()
            return o.encode()
        # Let the base class default method raise the TypeError
        return JSONEncoder.default(self, o)