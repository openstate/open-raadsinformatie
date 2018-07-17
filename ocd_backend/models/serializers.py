from rdflib import Literal, URIRef, Graph, BNode
from rdflib.collection import Collection
from rdflib.namespace import XSD, Namespace, NamespaceManager

from ocd_backend.models.definitions import ALL, Rdf, Ori
from ocd_backend.models.exceptions import SerializerError, SerializerNotFound, \
    RequiredProperty, MissingProperty
from ocd_backend.models.properties import StringProperty, IntegerProperty, \
    DateTimeProperty, ArrayProperty, Relation, OrderedRelation
from ocd_backend.utils.misc import iterate, str_to_datetime, datetime_to_unixstamp


def get_serializer_class(format=None):
    """Convenience function returns serializer or raises SerializerNotFound."""
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
    """The base serializer where all serializer should inherit from."""

    def __init__(self, uri_format_type='name'):
        """Initialize the serializer with a specified format.

        Options for uri_format_type are:
          - 'full': Fully quantified URI (ie. http://schema.org/example)
          - 'prefix': A property that is prefixed (ie. schema:example)
          - 'name': Just the name of the property
        """
        if uri_format_type not in ['full', 'prefix', 'name']:
            raise ValueError(
                "Not a valid uri_format. Choose 'full', 'prefix' or 'name'"
            )
        self.uri_format_type = uri_format_type

    def uri_format(self, klass):
        """Uses `klass` as an interface to return the specified uri_format."""
        if self.uri_format_type == 'full':
            return klass.full_uri()
        elif self.uri_format_type == 'prefix':
            return klass.prefix_uri()
        elif self.uri_format_type == 'name':
            return klass.name()

    def label(self, model_class):
        """Returns the `uri_format` of class name for `model_class`."""
        from .model import Model
        if isinstance(model_class, Model):
            model_class = type(model_class)

        return self.uri_format(model_class)

    def deflate(self, model_object, props, rels):
        """Returns a recurive serialized value for each model definition."""
        props_list = dict()
        for name, definition in model_object.definitions(props=props, rels=rels):
            value = model_object.__dict__.get(name, None)
            if value:
                namespaced = self.uri_format(definition)
                try:
                    props_list[namespaced] = self.serialize_prop(definition,
                                                                 value)
                except MissingProperty:
                    raise
            elif definition.required and not model_object.Meta.skip_validation:
                raise RequiredProperty("Property '{}' is required for {}".format(
                    name, model_object.prefix_uri()))
        return props_list

    def serialize(self, model_object):
        """High-level method that serializes the given `model_object`.

        Needs to be overriden by every subclass to enable serializer subclass
        specific behaviour. See this method in subclasses for more information.
        """
        raise NotImplementedError

    def serialize_prop(self, prop, value):
        """The actual serialization of the `value` on the provided property.

        This `BaseSerializer` method provides defaults which overridden subclass
        methods should call too. If there is no matching `prop`, it will raise
        an SerializerError.
        """
        if type(prop) == StringProperty:
            return value

        elif type(prop) == IntegerProperty:
            return value

        elif type(prop) == DateTimeProperty:
            date_object = str_to_datetime(value)
            return datetime_to_unixstamp(date_object)

        elif type(prop) == ArrayProperty:
            return value

        else:
            raise SerializerError(
                "Cannot serialize the property of type '{}'".format(type(prop))
            )


class Neo4jSerializer(BaseSerializer):
    """The `Neo4jSerializer` is just a basic subclass of the `BaseSerializer`.

    This serializer is used to turn the models in full URI properties that can
    be inserted in Neo4j.
    """

    def __init__(self):
        """Currently all properties in the Neo4j are fully qualified."""
        super(Neo4jSerializer, self).__init__('full')

    def serialize(self, model_object=None):
        """No high-level serialize method available, use `deflate` instead."""
        pass


class RdfSerializer(BaseSerializer):
    """The `Rdfserializer` create a graph and add the properties as Rdf triples.

    This uses rdflib to create a graph which can be serialized to the various
    formats that rdflib supports."""

    def __init__(self):
        """Set all properties in the Neo4j to be fully qualified."""
        self.g = Graph()
        super(RdfSerializer, self).__init__('full')

    def deflate(self, model_object, props, rels):
        """Overrides the `BaseSerializer` method to add graph logic."""
        namespace_manager = NamespaceManager(self.g)
        namespace_manager.bind(
            Ori.prefix,
            Namespace(Ori.uri),
            override=False
        )
        namespace_manager.bind(
            model_object.ns.prefix,
            Namespace(model_object.ns.uri),
            override=False
        )

        s = URIRef('{}{}'.format(Ori.uri,
                                 model_object.get_ori_identifier()))
        p = URIRef('{}type'.format(Rdf.uri))
        o = URIRef(self.uri_format(model_object))
        self.g.add((s, p, o,))

        for name, definition in model_object.definitions(props=props, rels=rels):
            value = model_object.__dict__.get(name, None)
            if value:
                p = URIRef(self.uri_format(definition))
                try:
                    o = self.serialize_prop(definition, value)
                except MissingProperty:
                    raise

                namespace_manager.bind(
                    definition.ns.prefix,
                    Namespace(definition.ns.uri),
                    override=False
                )
                if type(o) != list:
                    self.g.add((s, p, o,))
                else:
                    for oo in o:
                        self.g.add((s, p, oo,))
            elif definition.required and not model_object.Meta.skip_validation:
                raise RequiredProperty("Property '{}' is required for {}".format(
                    name, model_object.prefix_uri())
                )

    def serialize(self, model_object, format='turtle'):
        """Serializes `model_object` to a  Rdf `format`, defaults to 'turtle'.
        """
        self.deflate(model_object, props=True, rels=True)
        return self.g.serialize(format=format)

    def serialize_prop(self, prop, value):
        """Calls the super method and applies rdflib specific logic on it.

        Most properties will returned as a rdflib `Literal`. Relations will be
        iterated and returned as `URIRef`.
        """
        serialized = super(RdfSerializer, self).serialize_prop(prop, value)

        if type(prop) == StringProperty:
            return Literal(serialized, datatype=XSD.string)

        elif type(prop) == IntegerProperty:
            return Literal(serialized, datatype=XSD.integer)

        elif type(prop) == DateTimeProperty:
            return Literal(serialized, datatype=XSD.dateTime)

        elif type(prop) == ArrayProperty:
            return Literal(serialized)  # todo tests?

        elif type(prop) == Relation or type(prop) == OrderedRelation:
            props = list()
            o = BNode()
            for _, item in iterate(value):
                from .model import Relationship
                if isinstance(item, Relationship):
                    item = item.model
                self.deflate(item, props=True, rels=True)
                props.append(URIRef('{}{}'.format(Ori.uri,
                                                  item.get_ori_identifier())))

            if type(prop) == OrderedRelation:
                Collection(self.g, o, props)
                return o
            return props
        else:
            raise SerializerError(
                "Cannot serialize the property of type '{}'".format(type(prop))
            )


class JsonSerializer(BaseSerializer):
    """The `JsonSerializer` converts models to basic json data."""

    def __init__(self):
        super(JsonSerializer, self).__init__('name')

    def serialize(self, model_object):
        return self.deflate(model_object, props=True, rels=True)

    def serialize_prop(self, prop, value):
        """Serializes `Relation` and `OrderedRelation` references as a prefix.

        For all other properties super is called.
        """
        if type(prop) == Relation or type(prop) == OrderedRelation:
            props = list()
            for _, item in iterate(value):
                from .model import Relationship
                if isinstance(item, Relationship):
                    item = item.model

                props.append('{}:{}'.format(Ori.prefix, item.get_ori_identifier()))

            if len(props) == 1:
                return props[0]
            return props

        return super(JsonSerializer, self).serialize_prop(prop, value)


class JsonLDSerializer(JsonSerializer):
    """The `JsonLDSerializer` behaves like `JsonSerializer but adds @context."""

    def serialize(self, model_object):
        """Serializes `model_object` to JsonLD and adds @context."""
        context = {}
        for name, prop in model_object.definitions():
            context[name] = {
                '@id': prop.full_uri(),
                '@type': '@id',
            }

            # Temporary solution to include all namespaces in @context
            for ns in ALL:
                context[ns.prefix] = {
                    '@id': ns.uri,
                    '@type': '@id',
                }

        deflated = self.deflate(model_object, props=True, rels=True)
        deflated['@context'] = context
        return deflated
