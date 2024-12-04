from ocd_backend.shared_access import SharedAccess
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
        To avoid race conditions where multiple Source records are created for the same iri, use a lock.
        """
  
        SharedAccess.acquire_lock(iri)

        session = self.Session()

        try:
            # If the resource already exists, return existing ori_id
            resource = session.query(Source).filter(Source.iri == iri).one().resource
            return Uri(Ori, resource.ori_id)
        except NoResultFound:
            # If the resource does not exist, create resource (and possibly source)
            try:
                source = session.query(Source).filter(Source.iri == iri).one()
            except NoResultFound:
                source = Source(iri=iri)
            except MultipleResultsFound as e:
                log.info(f"MultipleResultsFound for {iri} when getting source")
                raise e

            new_id = self.engine.execute(Sequence('ori_id_seq'))
            new_identifier = Uri(Ori, new_id)
            resource = Resource(ori_id=new_id, iri=new_identifier, sources=[source])
            session.add(resource)
            session.commit()
            session.flush()
            return new_identifier
        except MultipleResultsFound as e:
            log.info(f"MultipleResultsFound for {iri} when getting resource")
            raise e
        finally:
            session.close()
            SharedAccess.release_lock(iri)


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
                    # The 'No matching scenario 2 while updating Source for resource' error occurs now and then
                    # due to race conditions. A simply retry here solves it.
                    try:
                        self.update_source(model_object)
                    except ValueError as e:
                        log.warning(f'Unable to update source, failed second time as well: {str(e)}')


            serialized_properties = self.serializer.deflate(model_object, props=True, rels=True)

            session = self.Session()
            resource = session.query(Resource).filter(Resource.ori_id == model_object.ori_identifier.partition(Ori.uri)[2]).one()

            # Delete properties that are about to be updated
            # TODO: maybe put the predicates in a temporary table so we can
            # perform a join on that table since that is faster
            # sometimes 11 or more predicates
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
                        setattr(new_property, self.map_column_type((item, value_and_property_type[1]), predicate), item)
                        resource.properties.append(new_property)
                else:
                    new_property = (Property(predicate=predicate))
                    setattr(new_property, self.map_column_type(value_and_property_type), value_and_property_type[0])
                    resource.properties.append(new_property)

            session.commit()
            session.close()

    @staticmethod
    def map_column_type(value_and_property_type, list_predicate = None):
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
        elif property_type is ArrayProperty:
            # Arrays of text from pdfs may contain something like "223\n" which would result in prop_resource being
            # returned (and a ForeignKeyViolation error on Resource or a link to a wrong Resource). Prevent this by
            # returning prop_string for all entries in an Array of type http://schema.org/text
            if list_predicate == 'http://schema.org/text':
                return 'prop_string'
            try:
                int(value)
                return 'prop_resource'
            except (ValueError, TypeError):
                return 'prop_string'
        elif property_type in (Relation, OrderedRelation):
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
            # To avoid race conditions where multiple Source records are created for the same iri, use a lock.
            SharedAccess.acquire_lock(model_object.source_iri)
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
                log.error(f'Error creating Source record: {str(e)}: {model_object.ori_identifier} - {model_object.source_iri}')
                # raise ValueError('No matching scenario 1 while updating Source for resource %s with IRI %s' %
                #                  (model_object.ori_identifier, model_object.source_iri))
            finally:
                SharedAccess.release_lock(model_object.source_iri)

        # Scenario 2
        elif (hasattr(model_object, 'canonical_id') and model_object.canonical_id is not None) and not \
                (hasattr(model_object, 'canonical_iri') and model_object.canonical_iri is not None):

            # Scenario 2A
            try:
                source = session.query(Source).filter(Source.resource_ori_id == resource.ori_id,
                                                      Source.iri == model_object.source_iri,
                                                      Source.canonical_id == str(model_object.canonical_id),
                                                      Source.canonical_iri == None).with_for_update().one()
                # Nothing needs to be updated
                return
            except MultipleResultsFound:
                raise ValueError('Multiple 2A/ID+X Source records found for resource %s with IRI %s' %
                                 (model_object.ori_identifier, model_object.source_iri))
            except NoResultFound:
                # Continue to next scenario
                pass
            finally:
                session.close()

            # Scenario 2B
            try:
                source = session.query(Source).filter(Source.resource_ori_id == resource.ori_id,
                                                      Source.iri == model_object.source_iri,
                                                      Source.canonical_id == None,
                                                      Source.canonical_iri == None).with_for_update().one()
                source.canonical_id = str(model_object.canonical_id)
                session.commit()
                return
            except MultipleResultsFound:
                raise ValueError('Multiple 2B/X+X Source records found for resource %s with IRI %s' %
                                 (model_object.ori_identifier, model_object.source_iri))
            except NoResultFound:
                # Continue to next scenario
                pass
            finally:
                session.close()

            # Scenario 2C
            try:
                source = session.query(Source).filter(Source.resource_ori_id == resource.ori_id,
                                                      Source.iri == model_object.source_iri,
                                                      Source.canonical_id == str(model_object.canonical_id),
                                                      Source.canonical_iri != None).with_for_update().one()
                # Nothing needs to be updated
                return
            except MultipleResultsFound:
                # TODO - Decide how to handle this
                return
            except NoResultFound:
                raise ValueError('No matching scenario 2 while updating Source for resource %s with IRI %s' %
                                 (model_object.ori_identifier, model_object.source_iri))
            finally:
                session.close()

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
