import datetime
from .exceptions import ValidationError
from .settings import enforce_restrictions
#from ocd_backend.utils.misc import load_object


class PropertyBase(object):
    def __repr__(self):
        return '<%s object %s>' % (self.__class__.__name__, str(self))

    def validate_property(self, value):
        pass

    def validate(self, value):
        return value

    def transform(self, value):
        return value

    @property
    def default(self):
        # For now let everything default to list for compatibility
        return list()

    def __str__(self):
        return 'test'


class Id(PropertyBase):
    def __init__(self):
        self.name = '@id'

    def __json__(self, value):
        return self.name, value,


class Type(PropertyBase):
    def __init__(self, ns):
        if not isinstance(ns, Namespace):
            raise Exception("Not a valid Namespace")

        self.name = '@type'
        self.ns = ns

    # def __str__(self): !!
    #     return '%s:%s' % (self.ns, self.value)

    def __json__(self, value):
        return self.name, '%s:%s' % (self.ns, value),


class Namespace(object):
    def __init__(self, namespace, short):
        self.namespace = namespace
        self.short = short

    def __str__(self):
        return self.short

    #def __get__(self):
    #    return self.namespace


class Property(PropertyBase):
    def __init__(self, ns, name):
        if not isinstance(ns, Namespace):
            raise Exception("Not a valid Namespace")

        self.ns = ns
        self.name = name

    # def __set__(self, instance, value):
    #     self.value = value

    def __json__(self, value):
        return '%s:%s' % (self.ns, self.name), value,

    # def __str__(self):
    #     try:
    #         return '%s:%s' % (self.ns, self.value)
    #     except:
    #         raise Exception('Not yet assigned')


class Instance(Property):
    pass


class Date(object):
    def to_python(self, value):
        if not value:
            return None

        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value

        raise ValidationError("Value of type %s is no valid date" % type(value))
        #also need to validate Some

    def __json__(self, value):
        return '%s:%s' % (self.ns, self.name), value, #.isoformat(),


class String(object):
    def to_python(self, value):
        if not value:
            return None

        if isinstance(value, basestring):
            return value.strip()

        raise ValidationError("Value of type %s is no valid string" % type(value))


class Integer(object):
    def to_python(self, value):
        raise NotImplemented()


class Restriction(PropertyBase):

    def __init__(self, ns, name, relation):
        self.ns = ns
        self.name = name
        self.relation = relation

        super(Restriction, self).__init__()

    # def __setitem__(self, key, value):
    #     if not hasattr(self, 'value'):
    #         self.value = list()
    #     elif type(self.value) != list:
    #         raise ValueError("Trying to set a list item while already something else")
    #     self.append(value)

    #def __getitem__(self, item):
    #    return self

    #def __str__(self):
    def serialize(self, value):
        print self.name, value
        if not value:
            raise ValueError("Value cannot be empty")

        # from ocd_backend.models.model_base import ModelBase
        # if isinstance(self.relation, ModelBase):
        #     if type(value) == list:
        #         return [v.get_relative_url() for v in value]
        #
        #     return value.get_relative_url()

        return value

        #except IndexError:
        #    raise ValueError('Not yet assigned')


    def context(self):
        return '%s:%s' % (self.ns, self.name), {'@type': '@id'},

    def validate_property(self, value):
        if enforce_restrictions:
            value = self.to_python(value)
            #value = self.transform(value)
            return self.validate(value)
        else:
            try:
                value = self.to_python(value)
                return self.validate(value)
            except ValidationError, e:
                print 'Setting enforce_restriction is set to False, caught ValidationError: %s' % e
                return False

    def to_python(self, value):
        if not value:
            return None

        if isinstance(self.relation, basestring):
            #self.relation = load_object('ocd_backend.models.%s' % self.relation)
            return ''

        if isinstance(value, self.relation):
            return value

        raise ValidationError("%s should be a subclass of %s.%s, got: %s" %
                              (self.name, self.relation.__module__, self.relation.__name__, type(value).__name__))

    def __json__(self, value):
        if not value:
            return None

        if not isinstance(value, basestring):
            value = self.serialize(value)
        return '%s:%s' % (self.ns, self.name), value,


class Some(Restriction):
    def __init__(self, ns, name, relation):
        super(Some, self).__init__(ns, name, relation)


class Min(Restriction):
    def __init__(self, ns, name, cardinality, relation):
        self.cardinality = cardinality
        super(Min, self).__init__(ns, name, relation)

    def validate(self, value):
        if not value:
            raise ValidationError('Min restriction on %s enforces to supply a minimum of 1 values' % self.name)


class Max(Restriction):
    def __init__(self, ns, name, cardinality, relation):
        self.cardinality = cardinality
        super(Max, self).__init__(ns, name, relation)

    def validate(self, value):
        if not value:
            return

        if not type(value) == list or len(value) >= self.cardinality:
            raise ValidationError('Max restriction on %s enforces to supply a maximum of %i values' % (self.name, self.cardinality,))


class Exactly(Restriction):
    def __init__(self, ns, name, cardinality, relation):
        self.cardinality = cardinality
        super(Exactly, self).__init__(ns, name, relation)

    def validate(self, value):
        #print 'val', value, self.cardinality
        if not type(value) == list or len(value) != self.cardinality:
            raise ValidationError('Exactly or Only restriction on %s enforces to supply exactly %i value(s)' % (self.name, self.cardinality,))


class Only(Exactly):
    def __init__(self, ns, name, relation):
        super(Only, self).__init__(ns, name, 1, relation)

    def append(self, value):
        raise NotImplemented("Only can have just one property and can therefore not append")


class SomeString(String, Some):
    #type = 'xsd:string'

    def __init__(self, ns, name):
        super(SomeString, self).__init__(ns, name, str)


class SomeDate(Date, Some):
    #type = 'xsd:dateTime'

    def __init__(self, ns, name):
        super(SomeDate, self).__init__(ns, name, None)


class OnlyDate(Date, Only):
    #type = 'xsd:dateTime'

    def __init__(self, ns, name):
        super(OnlyDate, self).__init__(ns, name, None)


class OnlyString(String, Only):
    #type = 'xsd:string'

    def __init__(self, ns, name):
        super(OnlyString, self).__init__(ns, name, None)


class OnlyInteger(Integer, Only):

    def __init__(self, ns, name):
        super(OnlyInteger, self).__init__(ns, name, None)


class MaxString(String, Max):

    def __init__(self, ns, name, cardinality):
        self.cardinality = cardinality
        super(MaxString, self).__init__(ns, name, cardinality, None)
