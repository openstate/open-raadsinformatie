from rdflib import Literal, URIRef, Graph, BNode
from rdflib.collection import Collection
from rdflib.namespace import XSD, Namespace, NamespaceManager

from ocd_backend.models.definitions import ALL, Rdf, Ori
from ocd_backend.models.exceptions import SerializerError, SerializerNotFound, \
    RequiredProperty, MissingProperty
from ocd_backend.models.properties import StringProperty, IntegerProperty, \
    DateProperty, DateTimeProperty, ArrayProperty, Relation, OrderedRelation
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

    def __init__(self, uri_format_type='term'):
        """Initialize the serializer with a specified format.

        Options for uri_format_type are:
          - 'full': Fully quantified URI (ie. http://schema.org/example)
          - 'prefix': A property that is prefixed (ie. schema:example)
          - 'name': Just the name of the property
        """
        if uri_format_type not in ['absolute', 'compact', 'term']:
            raise ValueError(
                "Not a valid uri_format. Choose 'absolute', 'compact' or 'term'"
            )
        self.uri_format_type = uri_format_type

    def uri_format(self, model_object):
        """Uses `klass` as an interface to return the specified uri_format."""
        if self.uri_format_type == 'absolute':
            return model_object.absolute_uri()
        elif self.uri_format_type == 'compact':
            return model_object.compact_uri()
        elif self.uri_format_type == 'term':
            return

    def label(self, model_object):
        """Returns the `uri_format` of class name for `model_class`."""
        return self.uri_format(model_object)

    def deflate(self, model_object, props, rels):
        """Returns a recurive serialized value for each model definition."""
        props_list = dict()
        for name, definition in model_object.definitions(props=props, rels=rels):
            value = model_object.values.get(name, None)
            if value:
                uri = self.uri_format(definition) or name
                try:
                    props_list[uri] = self.serialize_prop(definition, value)
                except MissingProperty:
                    raise
            elif definition.required and not model_object.skip_validation:
                raise RequiredProperty("Property '{}' is required for {}".format(
                    name, model_object.compact_uri()))
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

        elif type(prop) == DateProperty or type(prop) == DateTimeProperty:
            try:
                return value.isoformat()
            except:
                pass

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
        super(Neo4jSerializer, self).__init__('absolute')

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
        super(RdfSerializer, self).__init__('absolute')

    def deflate(self, model_object, props, rels):
        """Overrides the `BaseSerializer` method to add graph logic."""
        namespace_manager = NamespaceManager(self.g)
        namespace_manager.bind(
            Ori.prefix,
            Namespace(Ori.uri),
            override=False
        )
        namespace_manager.bind(
            model_object.prefix,
            Namespace(model_object.uri),
            override=False
        )

        s = URIRef('{}{}'.format(Ori.uri,
                                 model_object.get_ori_identifier()))
        p = URIRef('{}type'.format(Rdf.uri))
        o = URIRef(self.uri_format(model_object))
        self.g.add((s, p, o,))

        for name, definition in model_object.definitions(props=props, rels=rels):
            value = model_object.values.get(name, None)
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
            elif definition.required and not model_object.skip_validation:
                raise RequiredProperty("Property '{}' is required for {}".format(
                    name, model_object.compact_uri())
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
        super(JsonSerializer, self).__init__('term')

    def serialize(self, model_object):
        return self.deflate(model_object, props=True, rels=True)

    def serialize_prop(self, prop, value):
        """Serializes `Relation` and `OrderedRelation` references as a prefix.

        For all other properties the super method is called as a fallback.
        """
        if type(prop) == Relation or type(prop) == OrderedRelation:
            props = list()
            for _, item in iterate(value):
                from .model import Relationship, Individual
                if isinstance(item, Relationship):
                    item = item.model

                if isinstance(item, Individual):
                    if self.uri_format_type == 'compact':
                        props.append(item.compact_uri())
                    else:
                        props.append(item.absolute_uri())
                else:
                    props.append(self.ori_uri(item))

            if len(props) == 1:
                return props[0]
            return props

        return super(JsonSerializer, self).serialize_prop(prop, value)

    def ori_uri(self, item):
        """Creates a full uri to an ori resource since json doesn't do prefixes.
        """
        return str(item.get_ori_identifier())


class JsonLDSerializer(JsonSerializer):
    """The `JsonLDSerializer` behaves like `JsonSerializer but adds @context."""

    def serialize(self, model_object):
        """Serializes `model_object` to JsonLD and adds @context."""
        context = dict()
        for name, definition in model_object.definitions(props=False, rels=True):
            context[name] = {
                '@id': definition.absolute_uri(),
                '@type': '@id',
            }

        for name, definition in model_object.definitions(props=True, rels=False):
            context[name] = {
                '@id': definition.absolute_uri(),
            }

        deflated = self.deflate(model_object, props=True, rels=True)
        deflated['@context'] = {k: v for k, v in context.items() if k in deflated}
        deflated['@context']['@base'] = Ori.uri
        deflated['@context'][model_object.verbose_name()] = model_object.absolute_uri()
        deflated['@type'] = model_object.verbose_name()
        return deflated

    # def ori_uri(self, item):
    #     """Returns a non-prefixed uri to an ori resource. Needs to be a string
    #     in order to be expanded to a full uri by @base in JsonLD.
    #     """
    #     return str(item.get_ori_identifier())

    def ori_uri(self, item):
        """Creates a full uri to an ori resource since json doesn't do prefixes.
        """
        return item.get_short_identifier()
