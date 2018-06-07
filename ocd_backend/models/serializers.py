from .property import Instance, StringProperty, IntegerProperty, DateTimeProperty, ArrayProperty, Relation, InlineRelation
from ocd_backend.utils.misc import iterate, str_to_datetime, datetime_to_unixstamp
from .exceptions import SerializerError, SerializerNotFound, RequiredProperty
from .definitions.namespaces import FOAF, NCAL, OPENGOV, ORG, COUNCIL, GOVID, META, OWL, \
    PERSON, SCHEMA, RDF, RDFS, DCTERMS, SKOS, BIO, BIBFRAME, ORI


def get_serializer(format=None):
    if not format:
        serializer = BaseSerializer
    elif format == 'json-ld':
        serializer = JsonLDSerializer
    elif format == 'json':
        serializer = JsonSerializer
    else:
        raise SerializerNotFound(format)

    return serializer


class BaseSerializer(object):
    def __init__(self, model):
        self.model = model
        self.namespaces = False

    def deflate(self, namespaces=True, props=True, rels=False):
        """ Returns a serialized value for each model definition """
        self.namespaces = namespaces

        props_list = dict()
        for name, definition in self.model.definitions(props=props, rels=rels):
            namespaced = name
            if namespaces:
                namespaced = definition.get_prefix_uri()

            value = self.model.__dict__.get(name, None)

            if value:
                props_list[namespaced] = self.serialize_prop(definition, value)
            elif definition.required:
                raise RequiredProperty("Property '%s' is required for %s" %
                                       (name, self.model.get_prefix_uri()))
        return props_list

    def serialize(self):
        raise NotImplementedError

    def serialize_prop(self, prop, value):
        if type(prop) == Instance:
            return value.get_prefix_uri()

        elif type(prop) == StringProperty:
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
                props.append(type(self)(item).deflate(namespaces=self.namespaces, props=True, rels=True))

            if len(props) == 1:
                return props[0]
            return props

        elif type(prop) == Relation:
            props = list()
            for _, item in iterate(value):
                props.append('%s:%s' % (ORI.prefix, item.get_ori_id()))
                #props.append(type(self)(item).deflate(namespaces=True, props=True, rels=True))

            if len(props) == 1:
                return props[0]
            return props

        else:
            raise SerializerError("")


class JsonLDSerializer(BaseSerializer):
    def get_context(self):
        context = {}
        for name, prop in self.model.definitions():
            context[name] = {
                '@id': prop.get_full_uri(),
                '@type': '@id',
            }

            # Temporary solution to include all namespaces in @context
            for ns in [FOAF, NCAL, OPENGOV, ORG, COUNCIL, GOVID, META, OWL, PERSON,
                       SCHEMA, RDF, RDFS, DCTERMS, SKOS, BIO, BIBFRAME]:
                context[ns.prefix] = {
                    '@id': ns.namespace,
                    '@type': '@id',
                }
        return context

    def serialize(self):
        deflated = self.deflate(namespaces=False, props=True, rels=True)
        deflated['@context'] = self.get_context()
        return deflated

    #def serialize_prop(self, prop, value):
    #    return super(JsonLDSerializer, self).serialize_prop(prop, value)


class JsonSerializer(BaseSerializer):
    def serialize(self):
        return self.deflate(namespaces=False, props=True, rels=True)

    def serialize_prop(self, prop, value):
        if type(prop) == Instance:
            return value.get_full_uri()

        elif type(prop) == StringProperty:
            return value

        elif type(prop) == IntegerProperty:
            return value

        elif type(prop) == DateTimeProperty:
            date_object = str_to_datetime(value)
            return datetime_to_unixstamp(date_object)

        elif type(prop) == ArrayProperty:
            return value

        elif type(prop) == Relation:
            props = list()
            for _, item in iterate(value):
                props.append(item.get_ori_id())

            if len(props) == 1:
                return props[0]
            return props

        else:
            raise SerializerError("")
