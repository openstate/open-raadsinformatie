# -*- coding: utf-8 -*-

import re

from ocd_backend import celery_app
from ocd_backend.models.database import Neo4jDatabase
from ocd_backend.models.definitions import Mapping, Prov
from ocd_backend.models.exceptions import MissingProperty, ValidationError, \
    QueryResultError
from ocd_backend.models.properties import PropertyBase, Property, \
    StringProperty, IntegerProperty, Relation
from ocd_backend.models.serializers import Neo4jSerializer
from ocd_backend.models.misc import Namespace
from ocd_backend.utils.misc import iterate


class ModelMetaclass(type):
    database_class = Neo4jDatabase
    serializer_class = Neo4jSerializer

    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        definitions = dict()
        for key, value in list(attrs.items()):
            if isinstance(value, PropertyBase):
                definitions[key] = value
                attrs.pop(key)

        namespace = None
        if len(bases) > 1:
            assert issubclass(bases[0], Namespace)
            namespace = bases[0]
            bases = bases[1:]

        new_class = super(ModelMetaclass, mcs).__new__(mcs, name, bases, attrs)

        # Walk through the MRO.
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, '_definitions'):
                # noinspection PyProtectedMember
                definitions.update(base._definitions)

        new_class._definitions = definitions
        new_class.ns = namespace
        new_class.serializer = mcs.serializer_class()
        new_class.db = mcs.database_class(new_class)
        return new_class


class Model(object):
    __metaclass__ = ModelMetaclass

    # Top-level definitions
    ori_identifier = IntegerProperty(Mapping, 'ori/identifier')
    source_locator = StringProperty(Mapping, 'ori/sourceLocator')
    was_derived_from = StringProperty(Prov, 'wasDerivedFrom')

    @classmethod
    def name(cls):
        if hasattr(cls, 'verbose_name'):
            return cls.verbose_name
        return cls.__name__

    @classmethod
    def prefix_uri(cls):
        return '%s:%s' % (cls.ns.prefix, cls.name())

    @classmethod
    def full_uri(cls):
        return '%s%s' % (cls.ns.uri, cls.name())

    @classmethod
    def definitions(cls, props=True, rels=True):
        """ Return properties and relations objects from model definitions """
        props_list = list()
        for name, definition in cls._definitions.items():  # pylint: disable=no-member
            if (props and isinstance(definition, Property) or
                    (rels and isinstance(definition, Relation))):
                props_list.append((name, definition,))
        return props_list

    @classmethod
    def definition(cls, name):
        try:
            return cls._definitions[name]
        except KeyError:
            return

    @classmethod
    def inflate(cls, **deflated_props):
        instance = cls()
        for full_uri, value in deflated_props.items():
            definitions_mapping = {v.full_uri(): k for k, v in cls.definitions()}
            try:
                prop_name = definitions_mapping[full_uri]
                setattr(instance, prop_name, value)
            except KeyError:
                raise  # todo raise correct exception

        return instance

    def __init__(self, source=None, source_id=None, organization=None):
        if source:
            setattr(self, 'source_locator', source_id)
            setattr(self, 'was_derived_from', source)

    def __setattr__(self, key, value):
        definition = self.definition(key)

        # pylint: disable=no-member
        if key[0:2] != '__' and not definition:
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
        return '<%s Model>' % self.prefix_uri()

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

        # self.source_locator = '%s/%s/%s' % (organization, identifier_class.__name__, source_id)

    def get_ori_identifier(self):
        if not hasattr(self, 'ori_identifier'):
            try:
                self.ori_identifier = self.db.get_identifier_by_source_id(self, self.source_locator)
            except QueryResultError:
                raise MissingProperty('OriIdentifier is not present, has the '
                                      'model been saved?')
        return self.ori_identifier

    def generate_ori_identifier(self):
        self.ori_identifier = celery_app.backend.increment("ori_identifier_autoincrement")
        return self.ori_identifier

    def get_popolo_type(self):
        if hasattr(self, 'legacy_type'):
            return self.legacy_type

        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', type(self).get_name())
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def properties(self, props=True, rels=True):
        """ Returns namespaced properties with their inflated values """
        props_list = list()
        for name, prop in iterate({k: v for k, v in self.__dict__.items() if k[0:2] != '__'}):
            definition = self.definition(name)
            if (props and not isinstance(prop, Model)) or \
                    (rels and (isinstance(prop, Model) or isinstance(prop, Relationship))):
                props_list.append((self.serializer.uri_format(definition), prop,))
        return props_list

    def save(self):
        self.db.replace(self)
        self.attach_recursive()

    def attach_recursive(self):
        attach = list()
        for rel_type, other_object in self.properties(rels=True, props=False):

            self.db.replace(other_object)
            attach.append(self.db.attach(self, other_object, rel_type))

            # End the recursive loop when self-referencing
            if self != other_object:
                attach.extend(other_object.attach_recursive())

        self.db.copy_relations()
        return attach


class Individual(Model):
    __metaclass__ = ModelMetaclass

    @classmethod
    def set_source(cls, identifier_class, source_id, organization):
        # software / org / resource class / id
        # software / org / resource class / software id
        # utrecht/vergaderingen/357
        # utrecht/ibabsMeetingIdentifier/357
        # org / software / resource class / id

        instance = cls()

        instance.__rel_params__ = None  # todo temp

        if not organization or not identifier_class or not source_id:
            raise ValidationError("Invalid source locator specified", organization, identifier_class, source_id)

        if type(identifier_class) != ModelMetaclass:
            raise ValidationError("The 'identifier_class' is not a metaclass of ModelMetaclass: %s", identifier_class)

        instance.source_locator = '%s/%s/%s' % (organization, identifier_class.__name__, source_id)
        return instance


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
