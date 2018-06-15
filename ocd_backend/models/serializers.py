from ocd_backend.utils.misc import iterate, str_to_datetime, datetime_to_unixstamp
from .properties import StringProperty, IntegerProperty, DateTimeProperty, ArrayProperty, InlineRelation, Relation, OrderedRelation
from .exceptions import SerializerError, SerializerNotFound, RequiredProperty
from .definitions import FOAF, NCAL, OPENGOV, ORG, MEETING, MAPPING, META, OWL, \
    PERSON, SCHEMA, RDF, RDFS, DCTERMS, SKOS, BIO, BIBFRAME, ORI
from rdflib import Literal, URIRef, Graph, BNode
from rdflib.collection import Collection
from rdflib.namespace import XSD, Namespace, NamespaceManager


def get_serializer_class(format=None):
    if not format:
        serializer = BaseSerializer()
    elif format == 'json-ld':
        serializer = JsonLDSerializer()
    elif format == 'json':
        serializer = JsonSerializer()
    else:
        raise SerializerNotFound(format)

    return serializer


class BaseSerializer(object):
    def __new__(cls):
        """Implement BaseSerializer as a Singleton"""
        if not hasattr(cls, 'instance') or not isinstance(cls.instance, cls):
            cls.instance = super(BaseSerializer, cls).__new__(cls)
        return cls.instance

    def __init__(self, uri_format='name'):
        self.uri_format = None
        self.set_uri_format(uri_format)

    def get_uri(self, klass):
        if self.uri_format == 'full':
            return klass.get_full_uri()
        elif self.uri_format == 'prefix':
            return klass.get_prefix_uri()
        elif self.uri_format == 'name':
            return klass.get_name()

        raise ValueError("Not a valid uri_format. Choose 'full', 'prefix' or 'name'")

    def set_uri_format(self, uri_format):
        if uri_format not in ['full', 'prefix', 'name']:
            raise ValueError("Not a valid uri_format. Choose 'full', 'prefix' or 'name'")
        self.uri_format = uri_format

    def labels(self, model_class):
        from .model import Model
        if isinstance(model_class, Model):
            model_class = type(model_class)

        from .model import Model, Individual
        return [
            self.get_uri(scls) for scls in model_class.mro()
            if issubclass(scls, Model) and scls != Model and scls != Individual
        ]

    def deflate(self, model_object, props, rels):
        """ Returns a serialized value for each model definition """
        props_list = dict()
        for name, definition in model_object.definitions(props=props, rels=rels):
            value = model_object.__dict__.get(name, None)
            if value:
                namespaced = self.get_uri(definition)
                props_list[namespaced] = self.serialize_prop(definition, value)
            elif definition.required and not model_object.Meta.skip_validation:
                raise RequiredProperty("Property '%s' is required for %s" %
                                       (name, model_object.get_prefix_uri()))
        return props_list

    def serialize(self, model_object):
        raise NotImplementedError

    def serialize_prop(self, prop, value):
        # if type(prop) == Instance:
        #     return value.get_prefix_uri()

        if type(prop) == StringProperty:
            return value

        elif type(prop) == IntegerProperty:
            return value

        elif type(prop) == DateTimeProperty:
            date_object = str_to_datetime(value)
            return datetime_to_unixstamp(date_object)

        elif type(prop) == ArrayProperty:
            return value

        elif type(prop) == InlineRelation:
            props = list()
            for _, item in iterate(value):
                #props.append('%s:%s' % (ORI.prefix, item.get_ori_identifier()))
                props.append(self.deflate(item, props=True, rels=True))

            if len(props) == 1:
                return props[0]
            return props

        elif type(prop) == Relation or type(prop) == OrderedRelation:
            props = list()
            for _, item in iterate(value):
                from .model import Relationship
                if isinstance(item, Relationship):
                    item = item.model

                props.append('%s:%s' % (ORI.prefix, item.get_ori_identifier()))
                #props.append(type(self)(item).deflate(namespaces=True, props=True, rels=True))

            if len(props) == 1:
                return props[0]
            return props

        else:
            raise SerializerError("")


class Neo4jSerializer(BaseSerializer):
    def __init__(self):
        super(Neo4jSerializer, self).__init__('full')

    def serialize(self, model_object=None):
        pass


class RDFSerializer(BaseSerializer):
    def deflate(self, model_object, props, rels):
        """ Returns a serialized value for each model definition """
        namespace_manager = NamespaceManager(self.g)
        namespace_manager.bind(ORI.prefix, Namespace(ORI.namespace), override=False)
        namespace_manager.bind(model_object.__namespace__.prefix, Namespace(model_object.__namespace__.namespace), override=False)

        s = URIRef('%s%s' % (ORI.namespace, model_object.get_ori_identifier()))
        p = URIRef('%stype' % RDF.namespace)
        o = URIRef(model_object.get_full_uri())
        self.g.add((s, p, o,))

        for name, definition in model_object.definitions(props=props, rels=rels):
            value = model_object.__dict__.get(name, None)
            if value:
                p = URIRef(definition.get_full_uri())
                o = self.serialize_prop(definition, value)

                namespace_manager.bind(definition.ns.prefix, Namespace(definition.ns.namespace), override=False)
                if type(o) != list:
                    self.g.add((s, p, o,))
                else:
                    for oo in o:
                        self.g.add((s, p, oo,))
            elif definition.required and not model_object.Meta.skip_validation:
                raise RequiredProperty("Property '%s' is required for %s" %
                                       (name, model_object.get_prefix_uri()))

    def serialize(self, model_object, format='turtle'):
        self.g = Graph()
        self.deflate(model_object, props=True, rels=True)
        return self.g.serialize(format=format)

    def serialize_prop(self, prop, value):
        serialized = super(RDFSerializer, self).serialize_prop(prop, value)

        if type(prop) == StringProperty:
            return Literal(serialized, datatype=XSD.string)

        elif type(prop) == IntegerProperty:
            return Literal(serialized, datatype=XSD.integer)

        elif type(prop) == DateTimeProperty:
            return Literal(serialized, datatype=XSD.dateTime)

        elif type(prop) == ArrayProperty:
            return Literal(serialized)  # todo?

        elif type(prop) == InlineRelation or type(prop) == Relation or type(prop) == OrderedRelation:
            props = list()
            o = BNode()
            for _, item in iterate(value):
                from .model import Relationship
                if isinstance(item, Relationship):
                    item = item.model
                self.deflate(item, props=True, rels=True)
                props.append(URIRef('%s%s' % (ORI.namespace, item.get_ori_identifier())))

            if type(prop) == OrderedRelation:
                Collection(self.g, o, props)
                return o
            return props
        else:
            raise SerializerError("")


class JsonLDSerializer(BaseSerializer):
    @staticmethod
    def get_context(model_object):
        context = {}
        for name, prop in model_object.definitions():
            context[name] = {
                '@id': prop.get_full_uri(),
                '@type': '@id',
            }

            # Temporary solution to include all namespaces in @context
            for ns in [FOAF, NCAL, OPENGOV, ORG, MEETING, MAPPING, META, OWL, PERSON,
                       SCHEMA, RDF, RDFS, DCTERMS, SKOS, BIO, BIBFRAME]:
                context[ns.prefix] = {
                    '@id': ns.namespace,
                    '@type': '@id',
                }
        return context

    def serialize(self, model_object):
        self.set_uri_format('name')
        deflated = self.deflate(model_object, props=True, rels=True)
        deflated['@context'] = self.get_context(model_object)
        return deflated


class JsonSerializer(BaseSerializer):
    def serialize(self, model_object):
        self.set_uri_format('name')
        return self.deflate(model_object, props=True, rels=True)
