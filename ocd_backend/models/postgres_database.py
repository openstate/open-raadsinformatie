from sqlalchemy import create_engine, Sequence
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.pool import StaticPool

from ocd_backend import settings
from ocd_backend.log import get_source_logger
from ocd_backend.models.definitions import Ori
from ocd_backend.models.misc import Uri
from ocd_backend.models.postgres_models import Source, Resource, Property
from ocd_backend.models.properties import StringProperty, URLProperty, IntegerProperty, FloatProperty, \
    DateProperty, JsonProperty, DateTimeProperty, ArrayProperty, Relation, OrderedRelation

log = get_source_logger('postgres_database')


class PostgresDatabase:

    def __init__(self, serializer):
        self.serializer = serializer
        self.connection_string = 'postgresql://%s:%s@%s/%s' % (
                                    settings.POSTGRES_USERNAME,
                                    settings.POSTGRES_PASSWORD,
                                    settings.POSTGRES_HOST,
                                    settings.POSTGRES_DATABASE)
        self.engine = create_engine(self.connection_string, poolclass=StaticPool)
        self.Session = sessionmaker(bind=self.engine)

    def get_ori_identifier(self, iri):
        """
        Retrieves a Resource-based ORI identifier from the database. If no corresponding Resource exists,
        a new one is created.
        """

        session = self.Session()
        try:
            resource = session.query(Resource).join(Source).filter(Source.iri == iri).first()
            if not resource:
                raise NoResultFound
            return Uri(Ori, resource.ori_id)
        except MultipleResultsFound:
            raise MultipleResultsFound('Multiple resources found for IRI %s' % iri)
        except NoResultFound:
            return self.generate_ori_identifier(iri=iri)
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

    def get_mergeable_resource_identifier(self, model_object, predicate, column, value):
        """
        Queries the database to find the ORI identifier of the Resource linked to the Property with the given
        predicate and value in the specified column.
        """

        definition = model_object.definition(predicate)

        session = self.Session()
        try:
            query_result = session.query(Property).filter(Property.predicate == definition.absolute_uri())
            if column == 'prop_resource':
                query_result = query_result.filter(Property.prop_resource == value)
            elif column == 'prop_string':
                query_result = query_result.filter(Property.prop_string == value)
            elif column == 'prop_datetime':
                query_result = query_result.filter(Property.prop_datetime == value)
            elif column == 'prop_integer':
                query_result = query_result.filter(Property.prop_integer == value)
            elif column == 'prop_float':
                query_result = query_result.filter(Property.prop_float == value)
            elif column == 'prop_url':
                query_result = query_result.filter(Property.prop_url == value)
            else:
                raise ValueError('Invalid column type "%s" specified for merge_into' % column)
            resource_property = query_result.one()
            return resource_property.resource.iri
        except MultipleResultsFound:
            raise MultipleResultsFound('Multiple resources found for predicate "%s" with value "%s" in column "%s"' %
                                       (predicate, value, column))
        except NoResultFound:
            raise NoResultFound('No resource found for predicate "%s" with value "%s" in column "%s"' %
                                (predicate, value, column))
        finally:
            session.close()

    def save(self, model_object):
        if not model_object.source_iri:
            # If the item is an Individual, like EventConfirmed, we "save" it by setting an ORI identifier
            iri = self.serializer.label(model_object)
            if not model_object.values.get('ori_identifier'):
                model_object.ori_identifier = self.get_ori_identifier(iri=iri)
        else:
            if not model_object.values.get('ori_identifier'):
                model_object.ori_identifier = self.get_ori_identifier(iri=model_object.source_iri)

            # Handle canonical IRI or ID
            if (hasattr(model_object, 'canonical_id') and model_object.canonical_id is not None) or \
                    (hasattr(model_object, 'canonical_iri') and model_object.canonical_iri is not None):
                try:
                    self.update_source(model_object)
                except ValueError as e:
                    log.warning(f'Unable to update source: {str(e)}')

            serialized_properties = self.serializer.deflate(model_object, props=True, rels=True)

            session = self.Session()
            resource = session.query(Resource).filter(Resource.ori_id == model_object.ori_identifier.partition(Ori.uri)[2]).one()

            # Delete properties that are about to be updated
            predicates = serialized_properties.keys()
            session.query(Property).filter(Property.resource_id == resource.ori_id,
                                           Property.predicate.in_(predicates)
                                           ).delete(synchronize_session='fetch')

            # Save new properties
            for predicate, value_and_property_type in serialized_properties.items():
                if isinstance(value_and_property_type[0], list):
                    # Create each item as a separate Property with the same predicate, and save the order to
                    # the `order` column
                    for order, item in enumerate(value_and_property_type[0], start=1):
                        new_property = (Property(predicate=predicate, order=order))
                        setattr(new_property, self.map_column_type((item, value_and_property_type[1])), item)
                        resource.properties.append(new_property)
                else:
                    new_property = (Property(predicate=predicate))
                    setattr(new_property, self.map_column_type(value_and_property_type), value_and_property_type[0])
                    resource.properties.append(new_property)

            session.commit()
            session.close()

    @staticmethod
    def map_column_type(value_and_property_type):
        """Maps the property type to a column."""
        value = value_and_property_type[0]
        property_type = value_and_property_type[1]

        if property_type == StringProperty:
            return 'prop_string'
        elif property_type is URLProperty:
            return 'prop_url'
        elif property_type is IntegerProperty:
            return 'prop_integer'
        elif property_type is FloatProperty:
            return 'prop_float'
        elif property_type in (DateProperty, DateTimeProperty):
            return 'prop_datetime'
        elif property_type is JsonProperty:
            return 'prop_json'
        elif property_type in (ArrayProperty, Relation, OrderedRelation):
            try:
                int(value)
                return 'prop_resource'
            except (ValueError, TypeError):
                return 'prop_string'
        else:
            raise ValueError('Unable to map property of type "%s" to a column.' % property_type)

    def update_source(self, model_object):
        """Updates the canonical IRI or ID field of the Source of the corresponding model object.

        Scenarios:
        1) Canonical ID and IRI both set on model object:
            A) Check for Source record with matching ID and IRI set and do nothing
            B) Check for Source record with only matching ID set and add IRI
            C) Check for empty Source record and set ID and IRI
            D) Create new Source record with new ID and IRI
        2) Only canonical ID set on model object:
            A) Check for Source record with only matching ID set and do nothing
            B) Check for empty Source record and set ID
            C) Check for Source record with matching ID and non-empty IRI set and do nothing
        """

        session = self.Session()
        resource = session.query(Resource).get(model_object.get_short_identifier())

        # Scenario 1
        if (hasattr(model_object, 'canonical_id') and model_object.canonical_id is not None) and \
                (hasattr(model_object, 'canonical_iri') and model_object.canonical_iri is not None):

            # Scenario 1A
            try:
                source = session.query(Source).filter(Source.resource_ori_id == resource.ori_id,
                                                      Source.iri == model_object.source_iri,
                                                      Source.canonical_id == str(model_object.canonical_id),
                                                      Source.canonical_iri == model_object.canonical_iri).one()
                # Nothing needs to be updated
                session.close()
                return
            except MultipleResultsFound:
                raise ValueError('Multiple 1A/ID+IRI Source records found for resource %s with IRI %s' %
                                 (model_object.ori_identifier, model_object.source_iri))
            except NoResultFound:
                # Continue to next scenario
                pass

            # Scenario 1B
            try:
                source = session.query(Source).filter(Source.resource_ori_id == resource.ori_id,
                                                      Source.iri == model_object.source_iri,
                                                      Source.canonical_id == str(model_object.canonical_id),
                                                      Source.canonical_iri == None).one()
                source.canonical_iri = model_object.canonical_iri
                session.commit()
                session.close()
                return
            except MultipleResultsFound:
                raise ValueError('Multiple 1B/ID+X Source records found for resource %s with IRI %s' %
                                 (model_object.ori_identifier, model_object.source_iri))
            except NoResultFound:
                # Continue to next scenario
                pass

            # Scenario 1C
            try:
                source = session.query(Source).filter(Source.resource_ori_id == resource.ori_id,
                                                      Source.iri == model_object.source_iri,
                                                      Source.canonical_id == None,
                                                      Source.canonical_iri == None).one()
                source.canonical_id = str(model_object.canonical_id)
                source.canonical_iri = model_object.canonical_iri
                session.commit()
                session.close()
                return
            except MultipleResultsFound:
                raise ValueError('Multiple 1C/X+X Source records found for resource %s with IRI %s' %
                                 (model_object.ori_identifier, model_object.source_iri))
            except NoResultFound:
                # Continue to next scenario
                pass

            # Scenario 1D
            try:
                source = Source(resource=resource,
                                iri=model_object.source_iri,
                                canonical_id=str(model_object.canonical_id),
                                canonical_iri=model_object.canonical_iri)
                session.add(source)
                session.commit()
                session.close()
                return
            except Exception as e:
                session.close()
                log.error(f'{str(e)}: {model_object.ori_identifier} - {model_object.source_iri}')
                # raise ValueError('No matching scenario 1 while updating Source for resource %s with IRI %s' %
                #                  (model_object.ori_identifier, model_object.source_iri))

        # Scenario 2
        elif (hasattr(model_object, 'canonical_id') and model_object.canonical_id is not None) and not \
                (hasattr(model_object, 'canonical_iri') and model_object.canonical_iri is not None):

            # Scenario 2A
            try:
                source = session.query(Source).filter(Source.resource_ori_id == resource.ori_id,
                                                      Source.iri == model_object.source_iri,
                                                      Source.canonical_id == str(model_object.canonical_id),
                                                      Source.canonical_iri == None).one()
                # Nothing needs to be updated
                session.close()
                return
            except MultipleResultsFound:
                raise ValueError('Multiple 2A/ID+X Source records found for resource %s with IRI %s' %
                                 (model_object.ori_identifier, model_object.source_iri))
            except NoResultFound:
                # Continue to next scenario
                pass

            # Scenario 2B
            try:
                source = session.query(Source).filter(Source.resource_ori_id == resource.ori_id,
                                                      Source.iri == model_object.source_iri,
                                                      Source.canonical_id == None,
                                                      Source.canonical_iri == None).one()
                source.canonical_id = str(model_object.canonical_id)
                session.commit()
                session.close()
                return
            except MultipleResultsFound:
                raise ValueError('Multiple 2B/X+X Source records found for resource %s with IRI %s' %
                                 (model_object.ori_identifier, model_object.source_iri))
            except NoResultFound:
                # Continue to next scenario
                pass

            # Scenario 2C
            try:
                source = session.query(Source).filter(Source.resource_ori_id == resource.ori_id,
                                                      Source.iri == model_object.source_iri,
                                                      Source.canonical_id == str(model_object.canonical_id),
                                                      Source.canonical_iri != None).one()
                # Nothing needs to be updated
                session.close()
                return
            except MultipleResultsFound:
                # TODO - Decide how to handle this
                session.close()
                return
            except NoResultFound:
                session.close()
                raise ValueError('No matching scenario 2 while updating Source for resource %s with IRI %s' %
                                 (model_object.ori_identifier, model_object.source_iri))

        else:

            session.close()
            raise ValueError('update_source for Resource %s with IRI %s must be called with either canonical ID+IRI '
                             'or canonical ID only' % (model_object.ori_identifier, model_object.source_iri))

    def get_supplier(self, ori_id):
        """
        Retrieves the supplier portion of the IRI of the Resource with the given ORI ID.
        """

        session = self.Session()
        try:
            resource = session.query(Source).filter(Source.resource_ori_id == ori_id).first()
            return resource.iri.split('/')[6]
        except NoResultFound:
            raise ValueError('No Source found for Resource with ID %d' % ori_id)
        finally:
            session.close()
