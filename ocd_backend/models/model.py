# -*- coding: utf-8 -*-
import sys

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from ocd_backend.models.definitions import Mapping, Ori
from ocd_backend.models.exceptions import MissingProperty
from ocd_backend.models.properties import PropertyBase, Property, Relation
from ocd_backend.models.serializers import PostgresSerializer
from ocd_backend.models.misc import Namespace, Uri
from ocd_backend.utils.misc import iterate
from ocd_backend.log import get_source_logger
from ocd_backend.utils.misc import slugify
from ocd_backend.models.postgres_database import PostgresDatabase

log = get_source_logger('model')


class ModelMetaclass(type):
    serializer = PostgresSerializer()
    database = PostgresDatabase(serializer)

    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        definitions = dict()
        for key, value in list(attrs.items()):
            if isinstance(value, PropertyBase):
                definitions[key] = value
                attrs.pop(key)

        if len(bases) > 1 and not issubclass(bases[0], Namespace):
            raise ValueError('First argument of a Model subclass'
                             'should be a Namespace')

        new_class = super(ModelMetaclass, mcs).__new__(mcs, name, bases, attrs)

        # Walk through the MRO.
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, '_definitions'):
                # noinspection PyProtectedMember
                definitions.update(base._definitions)

        new_class._definitions = definitions
        new_class.serializer = mcs.serializer
        new_class.db = mcs.database
        return new_class


class Model(object, metaclass=ModelMetaclass):
    enricher_task = []

    def absolute_uri(self):
        return '%s%s' % (self.uri, self.verbose_name())

    def compact_uri(self):
        return '%s:%s' % (self.prefix, self.verbose_name())

    def verbose_name(self):
        # if hasattr(cls, 'verbose_name'):
        #     return cls.verbose_name
        return type(self).__name__

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
            return cls._definitions[name]  # pylint: disable=no-member
        except KeyError:
            raise MissingProperty("The definition %s has not been defined" %
                                  name)

    @classmethod
    def inflate(cls, **deflated_props):
        instance = cls()
        for absolute_uri, value in deflated_props.items():
            definitions_mapping = {v.absolute_uri(): k for k, v in cls.definitions()}
            try:
                prop_name = definitions_mapping[absolute_uri]
                setattr(instance, prop_name, value)
            except KeyError:
                raise  # todo raise correct exception

        return instance

    def __init__(self, source_id=None, source=None, supplier=None, collection=None,
                 cached_path=None, canonical_iri=None):
        # Set defaults
        self.skip_validation = None
        self.values = dict()
        self.enricher_task = self.enricher_task

        self.canonical_id = source_id
        self.cached_path = cached_path

        try:
            # if canonical_iri is a lambda function
            self.canonical_iri = canonical_iri(self)
        except TypeError:
            self.canonical_iri = canonical_iri

        # https://argu.co/voc/mapping/<organization>/<source>/<source_id_key>/<source_id>
        # i.e. https://argu.co/voc/mapping/nl/ggm/vrsnummer/6655476
        if source_id:
            assert source
            assert supplier
            assert collection
            self.source_iri = Uri(
                Mapping,
                '{}/{}/{}/{}'.format(
                    source,
                    supplier,
                    collection,
                    slugify(source_id)
                )
            )

    def __getattr__(self, item):
        try:
            return self.__dict__['values'][item]
        except KeyError:
            try:
                return self.__dict__[item]
            except KeyError:
                raise AttributeError(item)

    def __setattr__(self, key, value):
        try:
            definition = self.definition(key)
        except MissingProperty:
            definition = None

        if definition:
            value = definition.sanitize(value)
            self.values[key] = value
            return

        super(Model, self).__setattr__(key, value)

    def __contains__(self, item):
        try:
            if self.__getattribute__(item) is not None:
                return True
        except AttributeError:
            pass
        return False

    def __repr__(self):
        try:
            identifier = self.get_short_identifier()
        except Exception:
            identifier = '()'
        return '<%s %s>' % (self.compact_uri(), identifier)

    def get_ori_identifier(self):
        try:
            return self.ori_identifier
        except AttributeError:
            pass

        try:
            self.ori_identifier = self.db.get_ori_identifier(iri=self.source_iri)
        except AttributeError:
            return None

        return self.ori_identifier

    def get_short_identifier(self):
        ori_identifier = self.get_ori_identifier()
        if not ori_identifier:
            return None

        _, _, identifier = ori_identifier.partition(Ori.uri)
        assert len(identifier) > 0
        return identifier

    def properties(self, props=True, rels=True):
        """ Returns namespaced properties with their inflated values """
        props_list = list()
        for name, prop in iterate({k: v for k, v in self.values.items() if k[0:1] != '_'}):
            definition = self.definition(name)
            if not definition:
                continue

            if (props and not isinstance(prop, Model)) or (rels and isinstance(prop, Model)):
                props_list.append((self.serializer.uri_format(definition), prop,))  # pylint: disable=no-member
        return props_list

    saving_flag = False

    def traverse(self):
        """Returns all associated models that been attached to this model as properties"""
        rels = {}

        def inner(model):
            identifier = model.source_iri

            # Prevent circular recursion
            if identifier in rels.keys():
                return

            rels[identifier] = model

            for _, prop in iterate(model.values):
                if isinstance(prop, Model):
                    inner(prop)

        inner(self)
        return rels.values()

    def save(self):
        if self.saving_flag:
            return
        self.saving_flag = True

        try:
            self.db.save(self)  # pylint: disable=no-member
            # Recursive saving of related models
            for rel_type, value in self.properties(rels=True, props=False):
                if isinstance(value, Model):
                    value.save()
        except:
            log.info(f"Generic error occurred for save in Model, error class is {sys.exc_info()[0]}, {sys.exc_info()[1]}")
            log.info(vars(self))
            # Re-raise everything
            raise
        finally:
            self.saving_flag = False
