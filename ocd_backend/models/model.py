# -*- coding: utf-8 -*-

import re

import properties
from ocd_backend.settings import NEO4J_URL
from ocd_backend.utils.misc import iterate, load_object
from ocd_backend import celery_app
from .exceptions import RequiredProperty, MissingProperty, ValidationError
from .properties import StringProperty, IntegerProperty, Relation
from .definitions import MAPPING, PROV
from .database import Neo4jDatabase
from .serializers import Neo4jSerializer


class ModelMetaclass(type):
    db_class = Neo4jDatabase
    serializer_class = Neo4jSerializer

    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        definitions = dict()
        for key, value in list(attrs.items()):
            if isinstance(value, properties.PropertyBase):
                definitions[key] = value
                attrs.pop(key)
        attrs['__definitions__'] = definitions

        # Resolving namespace by module name
        namespace_string = 'ocd_backend.models.definitions.%s' % \
                           attrs['__module__'].rpartition('.')[2].upper()
        try:
            attrs['__namespace__'] = load_object(namespace_string)
        except NameError:
            attrs['__namespace__'] = None

        # attr = getattr(self, key)
        # if not isinstance(attr, PropertyBase):
        #     raise ValueError('Predefined attribute \'%s\' of class %s is not a'
        #                      ' subclass of PropertyBase' % (key, type(attr).__name__))

        new_class = super(ModelMetaclass, mcs).__new__(mcs, name, bases, attrs)

        new_class.serializer = mcs.serializer_class()
        new_class.db = mcs.db_class(new_class)


        # Walk through the MRO.
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, '__definitions__'):
                definitions.update(base.__definitions__)

            # Meta field shadowing.
            for attr, value in base.__dict__.items():
                if attr == 'Meta':
                    for key, val in value.__dict__.items():
                        if key[0:2] != '__' and key not in new_class.Meta.__dict__:
                            setattr(new_class.Meta, key, val)

        new_class.__definitions__ = definitions

        if not new_class.__namespace__:
            try:
                new_class.__namespace__ = new_class.Meta.namespace
            except:
                pass

        return new_class


class Model(object):
    __metaclass__ = ModelMetaclass

    # Top-level definitions
    ori_identifier = IntegerProperty(MAPPING, 'ori/identifier')
    source_locator = StringProperty(MAPPING, 'ori/sourceLocator')
    was_derived_from = Relation(PROV, 'wasDerivedFrom')

    class Meta:
        namespace = None
        enricher_task = None
        legacy_type = None
        verbose_name = None
        skip_validation = None

    @classmethod
    def get_name(cls):
        if cls.Meta.verbose_name:
            return cls.Meta.verbose_name
        return cls.__name__

    @classmethod
    def get_prefix_uri(cls):
        return '%s:%s' % (cls.__namespace__.prefix, cls.get_name())

    @classmethod
    def get_full_uri(cls):
        return '%s%s' % (cls.__namespace__.namespace, cls.get_name())

    @classmethod
    def definitions(cls, props=True, rels=True):
        """ Return properties and relations objects from model definitions """
        props_list = list()
        for name, definition in cls.__definitions__.items():  # pylint: disable=no-member
            if (props and isinstance(definition, properties.Property) or
                    (rels and isinstance(definition, properties.Relation))):
                props_list.append((name, definition,))
        return props_list

    @classmethod
    def get_definition(cls, name):
        try:
            return cls.__definitions__[name]
        except KeyError:
            return

    @classmethod
    def inflate(cls, **deflated_props):
        properties = dict()
        for full_uri, value in deflated_props.items():
            definitions_mapping = {v.get_full_uri(): k for k, v in cls.definitions()}
            try:
                prop_name = definitions_mapping[full_uri]
                properties[prop_name] = value
            except KeyError:
                raise  # todo raise correct exception

        instance = cls(**properties)

        # for namespaced, value in props.items():
        #     ns_string, name = namespaced.split(':')
        #
        #     for definition_name, definition_object in cls.definitions(props=True, rels=True):
        #         if name == definition_object.local_name and ns_string == definition_object.ns.prefix:
        #             setattr(instance, definition_name, value)
        #             break

        #instance.__temporary__ = True
        return instance

    # def serializer(self):
    #     if not self.__serializer__:
    #         self.__serializer__ = type(self).serializer_class(self)
    #
    #     return self.__serializer__

    def __init__(self, identifier_class=None, source_id=None, organization=None):
        self.__temporary__ = None
        self.__rel_params__ = None #todo
        self.__serializer__ = None

        #self.db = type(self).db_class(self)

        if identifier_class and (not source_id or not organization):
            raise MissingProperty("The identifier_value has not been given")

        if identifier_class:
            identifier_object = identifier_class(identifier_class, source_id, organization)
            #setattr(self, 'was_derived_from', [identifier_object])

        #self.set_source_locator(organization, identifier_class, source_id)

        self.get_ori_identifier()

    def __getitem__(self, item):
        return self.__dict__[item]

    def __setattr__(self, key, value):
        definition = self.get_definition(key)

        # pylint: disable=no-member
        if key[0:2] != '__' and not definition and \
                (hasattr(self, '__temporary__') and not self.__temporary__):
            raise AttributeError("'%s' is not defined in %s" % (key, self.get_prefix_uri()))
        # pylint: enable=no-member

        if definition:
            value = definition.sanitize(value)

        super(Model, self).__setattr__(key, value)

    def __iter__(self):
        for key, value in self.__dict__.items():
            yield key, value

    def __contains__(self, item):
        try:
            if self.__getattribute__(item) is not None:
                return True
        except AttributeError:
            pass
        return False

    def __repr__(self):
        return '<%s Model>' % self.get_prefix_uri()

    def set_source_locator(self, organization, identifier_class, source_id):
        # software / org / resource class / id
        # software / org / resource class / software id
        # utrecht/vergaderingen/357
        # utrecht/ibabsMeetingIdentifier/357
        # org / software / resource class / id

        if not organization or not identifier_class or not source_id:
            raise ValidationError("Invalid source locator specified", organization, identifier_class, source_id)

        if type(identifier_class) != ModelMetaclass:
            raise ValidationError("The 'identifier_class' is not a metaclass of ModelMetaclass: %s", identifier_class)

        #self.source_locator = '%s/%s/%s' % (organization, identifier_class.__name__, source_id)

    def get_ori_identifier(self):
        if not hasattr(self, 'ori_identifier'):
            self.ori_identifier = celery_app.backend.increment("ori_identifier_autoincrement")
        return self.ori_identifier

    def get_popolo_type(self):
        if self.Meta.legacy_type:
            return self.Meta.legacy_type

        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', type(self).get_name())
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def properties(self, props=True, rels=True):
        """ Returns namespaced properties with their inflated values """
        props_list = list()
        for name, prop in iterate({k: v for k, v in self.__dict__.items() if k[0:2] != '__'}):
            definition = self.get_definition(name)
            if (props and not isinstance(prop, Model)) or \
                    (rels and (isinstance(prop, Model) or isinstance(prop, Relationship))):
                props_list.append((self.serializer.get_uri(definition), prop,))
        return props_list

    def deflate(self, props=True, rels=False):
        """ Returns a serialized value for each model definition """
        props_list = dict()
        for name, definition in self.definitions(props=props, rels=rels):
            value = self.__dict__.get(name, None)
            if value:
                namespaced = self.serializer.get_uri(definition)
                props_list[namespaced] = self.serializer.serialize_prop(definition, value)
            elif definition.required and not self.Meta.skip_validation:
                raise RequiredProperty("Property '%s' is required for %s" %
                                       (name, self.get_prefix_uri()))
        return props_list

    def save(self):
        db = type(self).db_class(self)
        db.replace(self)
        db.attach_recursive(self)

    #def replace(self):
    #    self.db.replace(self.get_ori_identifier())


class Individual(Model):
    __metaclass__ = ModelMetaclass

    def __init__(self, identifier_class, source_id, organization):
        # software / org / resource class / id
        # software / org / resource class / software id
        # utrecht/vergaderingen/357
        # utrecht/ibabsMeetingIdentifier/357
        # org / software / resource class / id

        self.__rel_params__ = None #todo temp

        if not organization or not identifier_class or not source_id:
            raise ValidationError("Invalid source locator specified", organization, identifier_class, source_id)

        if type(identifier_class) != ModelMetaclass:
            raise ValidationError("The 'identifier_class' is not a metaclass of ModelMetaclass: %s", identifier_class)

        self.source_locator = '%s/%s/%s' % (organization, identifier_class.__name__, source_id)


class Relationship(object):
    """
    The Relationship model is used to explicitly specify one or more
    object model relations and describe what the relationship is about. The
    `rel` parameter is used to point to a object model that describes the
    relation, in a graph this is the edge between nodes. Note that not all
    serializers will make use of this.

    Relationship can have multiple arguments in order to specify multiple
    relations at once. Arguments of Relationship always relate to the property
    the Relationship is assigned to, and not to each other.

    ``
    # Basic way to assign relations
    object_model.parent = [a, b]

    # Relationship adds a way to describe the relation
    object_model.parent = Relationship(a, b, rel=c)

    # Under water this is translated to a list
    object_model.parent = [Relationship(a, rel=c), Relationship(b, rel=c)]
    ``
    """
    def __new__(cls, *args, **kwargs):
        if len(args) == 1:
            return super(Relationship, cls).__new__(cls)

        rel_list = list()
        for arg in args:
            rel_list.append(Relationship(arg, **kwargs))
        return rel_list

    def __init__(self, *args, **kwargs):
        self.model = args[0]
        self.rel = kwargs['rel']
