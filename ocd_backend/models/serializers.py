from ocd_backend.utils.misc import iterate, str_to_datetime, datetime_to_unixstamp
from .property import StringProperty, IntegerProperty, DateTimeProperty, ArrayProperty, InlineRelation, Relation
from .exceptions import SerializerError, SerializerNotFound, RequiredProperty
from .definitions import FOAF, NCAL, OPENGOV, ORG, MEETING, MAPPING, META, OWL, \
    PERSON, SCHEMA, RDF, RDFS, DCTERMS, SKOS, BIO, BIBFRAME, ORI


def get_serializer_class(format=None):
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
            value = self.model.__dict__.get(name, None)
            if value:
                namespaced = self.model.get_uri(definition)
                props_list[namespaced] = self.serialize_prop(definition, value)
            elif definition.required and not self.model.Meta.skip_validation:
                raise RequiredProperty("Property '%s' is required for %s" %
                                       (name, self.model.get_prefix_uri()))
        return props_list

    def serialize(self):
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
                props.append(type(self)(item).deflate(namespaces=self.namespaces, props=True, rels=True))

            if len(props) == 1:
                return props[0]
            return props

        elif type(prop) == Relation:
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
    pass


class JsonLDSerializer(BaseSerializer):
    def get_context(self):
        context = {}
        for name, prop in self.model.definitions():
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

    def serialize(self):
        self.model.set_uri_format('name')
        deflated = self.deflate(props=True, rels=True)
        deflated['@context'] = self.get_context()
        return deflated

    #def serialize_prop(self, prop, value):
    #    return super(JsonLDSerializer, self).serialize_prop(prop, value)


class JsonSerializer(BaseSerializer):
    def serialize(self):
        self.model.set_uri_format('name')
        return self.deflate(props=True, rels=True)

    def serialize_prop(self, prop, value):
        # if type(prop) == Instance:
        #     return value.get_full_uri()

        if type(prop) == StringProperty:
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
                props.append(item.get_ori_identifier())

            if len(props) == 1:
                return props[0]
            return props

        else:
            raise SerializerError("")
