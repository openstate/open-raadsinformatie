# -*- coding: utf-8 -*-

import os
import re
from hashlib import sha1

from py2neo import Graph, ConstraintError

import property
from ocd_backend.settings import NEO4J_URL
from ocd_backend.utils.misc import iterate, load_object
from .exceptions import RequiredProperty, MissingProperty, \
    QueryResultError
from .serializers import get_serializer

graph = None


def get_graph():
    global graph
    if graph:
        return graph
    graph = Graph(NEO4J_URL)
    return graph


class ModelBaseMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        definitions = dict()
        for key, value in list(attrs.items()):
            if isinstance(value, property.PropertyBase):
                definitions[key] = value
                attrs.pop(key)
        attrs['__definitions__'] = definitions

        # Resolving namespace by module name
        namespace_string = 'ocd_backend.models.definitions.namespaces.%s' % \
                           attrs['__module__'].rpartition('.')[2].upper()
        try:
            attrs['__namespace__'] = load_object(namespace_string)
        except NameError:
            attrs['__namespace__'] = None

        # attr = getattr(self, key)
        # if not isinstance(attr, PropertyBase):
        #     raise ValueError('Predefined attribute \'%s\' of class %s is not a'
        #                      ' subclass of PropertyBase' % (key, type(attr).__name__))

        new_class = super(ModelBaseMetaclass, mcs).__new__(mcs, name, bases, attrs)

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

        return new_class


class ModelBase(object):
    __metaclass__ = ModelBaseMetaclass

    class Meta:
        namespace = None
        enricher_task = None
        legacy_type = None

    def get_object_hash(self, object_id=None):
        if not object_id:
            object_id = os.urandom(16).encode('hex')

        hash_content = '%s-%s' % (self.get_prefix_uri(), unicode(object_id))  # temporary fix
        return sha1(hash_content.decode('utf8')).hexdigest()

    def get_ori_id(self):
        return self.ori_identifier

    @classmethod
    def get_prefix_uri(cls):
        return '%s:%s' % (cls.Meta.namespace.prefix, cls.__name__)

    def get_popolo_type(self):
        if self.Meta.legacy_type:
            return self.Meta.legacy_type

        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', type(self).__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @classmethod
    def labels(cls):
        return [
            scls.get_prefix_uri()
            for scls in cls.mro()
            if issubclass(scls, ModelBase) and scls != ModelBase
        ]

    def properties(self, props=True, rels=True):
        """ Returns namespaced properties with their inflated values """
        props_list = list()
        for name, prop in iterate({k: v for k, v in self.__dict__.items() if k[0:2] != '__'}):
            definition = self.__definitions__[name]  # pylint: disable=no-member
            if (props and not isinstance(prop, ModelBase)) or (rels and isinstance(prop, ModelBase)):
                props_list.append((definition.get_prefix_uri(), prop,))
        return props_list

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
    def inflate(cls, props):
        # todo inflate needs inflate relations and models as well
        try:
            prefix_uri = cls.__definitions__['ori_identifier'].get_prefix_uri()
            identifier_value = props[prefix_uri]  # pylint: disable=no-member
        except KeyError:
            raise  # todo raise correct exception

        instance = cls('ori_identifier', identifier_value)

        for namespaced, value in props.items():
            ns_string, name = namespaced.split(':')

            for definition_name, definition_object in cls.definitions(props=True, rels=True):
                if name == definition_object.local_name and ns_string == definition_object.ns.prefix:
                    setattr(instance, definition_name, value)
                    break

        instance.__temporary__ = True
        return instance

    def __setattr__(self, key, value):
        # pylint: disable=no-member
        if key[0:2] != '__' and key not in self.__definitions__ and \
                (hasattr(self, '__temporary__') and not self.__temporary__):
            raise AttributeError("'%s' is not defined in %s" % (key, self.get_prefix_uri()))
        # pylint: enable=no-member

        super(ModelBase, self).__setattr__(key, value)

    def __init__(self, identifier_name=None, identifier_value=None, temporary=False, rel_params=None):
        self.__temporary__ = temporary
        self.__rel_params__ = rel_params

        if identifier_name and not identifier_value:
            raise MissingProperty("The identifier_value has not been given")

        if identifier_name:
            from .definitions.owl import Identifier
            identifier_object = Identifier()
            identifier_object.identifier = identifier_value
            #identifier_object.represent = load_object(identifier_name)
            self.identifier = [identifier_object]

        self.ori_identifier = self.get_object_hash(identifier_value)

    def __iter__(self):
        for key, value in self.__dict__.items():
            yield key, value

    def __getitem__(self, item):
        return self.__dict__[item]

    def __contains__(self, item):
        try:
            if self.__getattribute__(item) is not None:
                return True
        except AttributeError:
            pass
        return False

    def __repr__(self):
        return '<%s Model>' % self.get_prefix_uri()

    @classmethod
    def get_or_create(cls, **kwargs):
        if len(kwargs) < 1:
            raise TypeError('get() takes exactly 1 keyword-argument')

        definitions = dict(cls.definitions(props=True, rels=True))
        params = list()
        props = list()
        for name, value in kwargs.items():
            try:
                identifier = definitions[name].get_prefix_uri()
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
            instance = cls(*props[0])
            instance.__temporary__ = True
            return instance

        return cls.inflate({'govid:oriIdentifier': result[0]['n']})

    def save(self):
        self.replace()
        self.attach_recursive(self)
        return self

    @staticmethod
    def attach_recursive(model):
        for key, prop in model.properties(rels=True, props=False):
            model.attach(key, prop)
            model.attach_recursive(prop)

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
                query % {'labels': '`:`'.join(self.labels()), 'identifier_value': self.get_ori_id()},
                replace_params=get_serializer()(self).deflate(props=True, rels=False))
        except ConstraintError, e:
            # todo
            raise

        if len(result) != 1:
            raise QueryResultError('The number of results is more or less than one!')
        return result[0]['n']

    def attach(self, rel_type, other, rel_params=None):
        serializer = get_serializer()
        create_params = serializer(other).deflate(props=True, rels=True)
        rel_params = rel_params or other.__rel_params__ or {}

        if isinstance(rel_params, ModelBase):
            rel_params = serializer(rel_params).deflate(props=True, rels=True)

        query = 'MATCH (n :`%(labels)s` {`govid:oriIdentifier`: \'%(identifier_value)s\'}) ' % \
                {'labels': '`:`'.join(self.labels()), 'identifier_value': self.get_ori_id()}
        query += 'MERGE (m {`govid:oriIdentifier`: \'%(identifier_value)s\'}) ' % \
                 {'labels': '`:`'.join(other.labels()), 'identifier_value': other.get_ori_id()}
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
