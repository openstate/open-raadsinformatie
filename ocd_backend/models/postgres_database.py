import uuid

from sqlalchemy import create_engine, Sequence
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from ocd_backend import settings
from ocd_backend.models.postgres_models import Source, Resource, Property
from ocd_backend.models.definitions import Ori
from ocd_backend.models.properties import StringProperty, IntegerProperty, DateProperty, DateTimeProperty, \
    ArrayProperty, Relation, OrderedRelation
from ocd_backend.models.misc import Uri


class PostgresDatabase(object):

    def __init__(self, serializer):
        self.serializer = serializer
        self.connection_string = 'postgresql://%s:%s@%s/%s' % (
                                    settings.POSTGRES_USERNAME,
                                    settings.POSTGRES_PASSWORD,
                                    settings.POSTGRES_HOST,
                                    settings.POSTGRES_DATABASE)
        self.engine = create_engine(self.connection_string)
        self.Session = sessionmaker(bind=self.engine)

    def get_ori_identifier(self, iri):
        """
        Retrieves a Resource-based ORI identifier from the database. If no corresponding Resource exists,
        a new one is created.
        """

        session = self.Session()
        try:
            resource = session.query(Resource).join(Source).filter(Source.iri == iri).one()
            return Uri(Ori, resource.ori_id)
        except MultipleResultsFound:
            raise MultipleResultsFound('Multiple resources found for IRI %s' % iri)
        except NoResultFound:
            return self.generate_ori_identifier(iri=iri)
        finally:
            session.close()

    def get_mergeable_resource_identifier(self, model_object, **kwargs):
        """
        Queries the database to find the ORI identifier of the Resource linked to the Property with the given
        predicate and value.

        TODO: Currently only works for values that are in the `prop_string` field.
        """

        if len(kwargs) != 1:
            raise TypeError('get_mergeable_resource_identifier takes exactly 1 keyword argument')

        filter_key, filter_value = kwargs.items()[0]
        definition = model_object.definition(filter_key)

        session = self.Session()
        try:
            # TODO: This currently only works if the filter_value is in the prop_string field.
            resource_property = session.query(Property).filter(Property.predicate == definition.absolute_uri(),
                                                               Property.prop_string == filter_value).one()
            return resource_property.resource.iri
        except MultipleResultsFound:
            raise MultipleResultsFound('Multiple properties found for predicate %s with value %s' %
                                       (filter_key, filter_value))
        except NoResultFound:
            raise NoResultFound('No property found for predicate %s with value %s' %
                                (filter_key, filter_value))
        finally:
            session.close()

    def generate_ori_identifier(self, iri):
        """
        Generates a Resource with an ORI identifier and adds the IRI as a Source if it does not already exist.
        """

        session = self.Session()
        new_id = self.engine.execute(Sequence('ori_id_seq'))
        new_identifier = Uri(Ori, new_id)

        try:
            # If the resource already exists, create the source as a child of the resource
            resource = session.query(Source).filter(Source.iri == iri).one().resource
            resource.sources.append(Source(iri=iri))
            session.flush()
        except NoResultFound:
            # If the resource does not exist, create resource and source together
            resource = Resource(ori_id=new_id, iri=new_identifier, sources=[Source(iri=iri)])
            session.add(resource)
            session.commit()
        finally:
            session.close()

        return new_identifier

    def save(self, model_object):
        if not model_object.values.get('had_primary_source'):
            # If the item is an Individual, like EventConfirmed, we "save" it by setting an ORI identifier
            iri = self.serializer.label(model_object)
            if not model_object.values.get('ori_identifier'):
                model_object.ori_identifier = self.get_ori_identifier(iri=iri)
        else:
            if not model_object.values.get('ori_identifier'):
                model_object.ori_identifier = self.get_ori_identifier(iri=model_object.values.get('had_primary_source'))

            serialized_properties = self.serializer.deflate(model_object, props=True, rels=True)

            session = self.Session()
            resource = session.query(Resource).filter(Resource.ori_id == model_object.ori_identifier.partition(Ori.uri)[2]).one()

            # Delete properties that are about to be updated
            predicates = [predicate for predicate, _ in serialized_properties.iteritems()]
            session.query(Property).filter(Property.resource_id==resource.ori_id,
                                           Property.predicate.in_(predicates)
                                           ).delete(synchronize_session='fetch')
            session.commit()

            # Save new properties
            for predicate, value_and_property_type in serialized_properties.iteritems():
                new_property = (Property(id=uuid.uuid4(), predicate=predicate))
                setattr(new_property, self.map_column_type(value_and_property_type), value_and_property_type[0])
                resource.properties.append(new_property)
            session.commit()

            session.close()

    @staticmethod
    def map_column_type(value_and_property_type):
        """Maps the property type to a column."""
        value = value_and_property_type[0]
        property_type = value_and_property_type[1]

        if property_type in (StringProperty, ArrayProperty):
            return 'prop_string'
        elif property_type is IntegerProperty:
            return 'prop_integer'
        elif property_type in (DateProperty, DateTimeProperty):
            return 'prop_datetime'
        elif property_type in (Relation, OrderedRelation):
            # Slight hack to intercept Individuals that have no ORI identifier
            try:
                int(value)
                return 'prop_resource'
            except (ValueError, TypeError):
                return 'prop_string'
        else:
            raise ValueError('Unable to map property of type %s to a column.' % property_type)
