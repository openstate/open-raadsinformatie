# -*- coding: utf-8 -*-

import os
import re
from hashlib import sha1

from py2neo import Graph, ConstraintError
from .cypher import cypher_escape, cypher_repr

import property
from ocd_backend.settings import NEO4J_URL
from ocd_backend.utils.misc import iterate, load_object
from ocd_backend import celery_app
from .exceptions import RequiredProperty, MissingProperty, QueryResultError, ValidationError
from .property import StringProperty, IntegerProperty, Relation
from .definitions import MAPPING, PROV
from .serializers import get_serializer_class

graph = None


def get_graph():
    global graph
    if graph:
        return graph
    graph = Graph(NEO4J_URL)
    return graph


class ModelMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        definitions = dict()
        for key, value in list(attrs.items()):
            if isinstance(value, property.PropertyBase):
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


class ModelBase(object):
    __metaclass__ = ModelMetaclass
    __uri_format__ = 'name'

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
        return '%s:%s' % (cls.__namespace__.namespace, cls.get_name())

    @classmethod
    def get_uri(cls, klass=None):
        if not klass:
            klass = cls

        if cls.__uri_format__ == 'full':
            return klass.get_full_uri()
        elif cls.__uri_format__ == 'prefix':
            return klass.get_prefix_uri()
        else:
            return klass.get_name()

    @classmethod
    def set_uri_format(cls, uri_format):
        if uri_format not in ['full', 'prefix', 'name']:
            raise ValueError("Not a valid uri_format. Choose 'full', 'prefix' or 'name'")
        cls.__uri_format__ = uri_format

    @classmethod
    def get_or_create(cls, identifier_object, **kwargs):
        if len(kwargs) < 1:
            raise TypeError('get() takes exactly 1 keyword-argument')

        definitions = dict(cls.definitions(props=True, rels=True))
        params = list()
        props = list()
        for name, value in kwargs.items():
            try:
                identifier = definitions[name].get_prefix_uri() #todo get_uri()
                props.append((name, value,))
                params.append(
                    '`%(key)s`: \'%(value)s\'' % {
                        'key': identifier,
                        'value': value,
                    }
                )
            except KeyError:
                raise MissingProperty("Cannot query '%s' since it's not defined in %s" % (name, cls.__name__))

        # todo lazy returning only the id, instead everything must be inflated
        query = 'MATCH (n {%s}) RETURN n.`govid:oriIdentifier` AS n' % ', '.join(params)
        try:
            result = get_graph().data(query)
        except ConstraintError, e:
            raise

        if len(result) > 1:
            raise QueryResultError('The number of results is greater than one!')

        if len(result) < 1:
            instance = cls()
            return instance

        return cls.inflate({'govid:oriIdentifier': result[0]['n']})

    @classmethod
    def labels(cls):
        return [
            scls.get_uri()
            for scls in cls.mro()
            if issubclass(scls, ModelBase) and scls != ModelBase and scls != Individual
        ]

    @classmethod
    def definitions(cls, props=True, rels=True):
        """ Return properties and relations objects from model definitions """
        props_list = list()
        for name, definition in cls.__definitions__.items():  # pylint: disable=no-member
            if (props and isinstance(definition, property.Property) or
                    (rels and isinstance(definition, property.Relation))):
                props_list.append((name, definition,))
        return props_list

    @classmethod
    def get_definition(cls, name):
        try:
            return cls.__definitions__[name]
        except KeyError:
            return

    @classmethod
    def inflate(cls, deflated_props):
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

    def __init__(self, identifier_class=None, source_id=None, organization=None):
        self.__temporary__ = None
        self.__rel_params__ = None #todo

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

        super(ModelBase, self).__setattr__(key, value)

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
            definition = self.__definitions__[name]  # pylint: disable=no-member
            if (props and not isinstance(prop, ModelBase)) or (rels and isinstance(prop, ModelBase)):
                props_list.append((self.get_uri(definition), prop,))
        return props_list

    def save(self):
        # if not hasattr(self, 'source_locator'):
        #     raise RequiredProperty("Required property 'source_locator' has not been set")
        self.update()
        #self.replace()
        self.attach_recursive(self)
        return self

    @staticmethod
    def attach_recursive(model):
        for key, prop in model.properties(rels=True, props=False):
            model.attach(key, prop)

            # End the recursive loop when self-referencing
            if model != prop:
                model.attach_recursive(prop)

    @classmethod
    def get(cls, **kwargs):
        if len(kwargs) < 1:
            raise TypeError('get() takes exactly 1 keyword-argument')

        property_map = dict()
        for name, value in kwargs.items():
            try:
                identifier = cls.get_definition(name).get_full_uri()
                property_map[identifier] = value
            except KeyError:
                raise MissingProperty("Cannot query '%s' since it's not defined in %s" % (name, cls.__name__))

        label_string = ":".join(cypher_escape(label) for label in cls.labels())

        clauses = list()
        clauses.append("MATCH (n :%s %s) RETURN n" % (label_string, cypher_repr(property_map)))

        statement = "\n".join(clauses)

        tx = get_graph().begin()
        cursor = tx.run(statement)
        tx.commit()

        result = cursor.data()

        if len(result) > 1:
            raise QueryResultError('The number of results is greater than one!')

        inflated = cls.inflate({k: v for k, v in result[0]['n'].items()})
        print

    def update(self):
        label_string = ":".join(cypher_escape(label) for label in self.labels())

        #self.get(ori_identifier=135)

        #identifier = self.get_definition('ori_identifier').get_prefix_uri()
        #property_map = {identifier: self.get_ori_identifier()}
        property_map = get_serializer_class()(self).deflate(namespaces='full', props=True, rels=False)

        clauses = list()
        clauses.append("MERGE (n :%s %s)" % (label_string, cypher_repr(property_map)))
        #clauses.append("MERGE (m :%s %s)" % (label_string, ''))
        #clauses.append("MERGE (n)-[:delta]->(m)")

        statement = "\n".join(clauses)

        tx = get_graph().begin()
        res = tx.run(statement)
        tx.commit()

        print

    def replace(self):
        query = '''
        MERGE (n :`%(labels)s` {`govid:oriIdentifier`: '%(identifier_value)s'})
        SET n = $replace_params
        WITH n
        OPTIONAL MATCH (n)-[r]->()
        DELETE r
        WITH n
        RETURN DISTINCT n
        '''

        try:
            result = get_graph().data(
                query % {'labels': '`:`'.join(self.labels()), 'identifier_value': self.get_ori_identifier()},
                replace_params=get_serializer_class()(self).deflate(props=True, rels=False))
        except ConstraintError, e:
            # todo
            raise

        if len(result) != 1:
            raise QueryResultError('The number of results is more or less than one!')
        return result[0]['n']

    def attach(self, rel_type, other):
        rel_params = dict()
        if isinstance(other, Relationship):
            rel_params = other.rel
            other = other.model

        serializer = get_serializer_class()
        create_params = serializer(other).deflate(namespaces='full', props=True, rels=True)

        if isinstance(rel_params, ModelBase):
            rel_params = serializer(rel_params).deflate(namespaces='full', props=True, rels=True)

        self_label_string = ":".join(cypher_escape(label) for label in self.labels())

        identifier = self.get_uri(self.get_definition('ori_identifier'))
        self_property_map = {identifier: self.get_ori_identifier()}

        other_label_string = ":".join(cypher_escape(label) for label in other.labels())
        other_property_map = {identifier: self.get_ori_identifier()}

        clauses = list()
        clauses.append("MATCH (n :%s %s)" % (self_label_string, cypher_repr(self_property_map)))
        clauses.append("MERGE (m %s)" % cypher_repr(other_property_map))
        clauses.append("MERGE (n)-[r :%s]->(m)" % rel_type)
        clauses.append("ON CREATE SET m += $create_params")
        clauses.append("ON MATCH SET m += $create_params")
        clauses.append("SET m:%s" % other_label_string)
        clauses.append("RETURN n")

        statement = "\n".join(clauses)

        query = 'MATCH (n :`%(labels)s` {`govid:oriIdentifier`: \'%(identifier_value)s\'}) ' % \
                {'labels': '`:`'.join(self.labels()), 'identifier_value': self.get_ori_identifier()}
        query += 'MERGE (m {`govid:oriIdentifier`: \'%(identifier_value)s\'}) ' % \
                 {'labels': '`:`'.join(other.labels()), 'identifier_value': other.get_ori_identifier()}
        query += '''MERGE (n)-[r :`%(rel_type)s`]->(m)
        ON CREATE SET m += $create_params
        ON MATCH SET m += $create_params
        SET m:`%(labels)s`
        SET r = $rel_params
        RETURN n
        ''' % {'rel_type': rel_type, 'labels': '`:`'.join(other.labels())}

        try:
            result = get_graph().data(
                query,
                create_params=create_params,
                rel_params=rel_params
            )
        except ConstraintError, e:
            raise

        return result


class Individual(ModelBase):
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
