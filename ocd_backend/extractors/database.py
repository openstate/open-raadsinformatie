from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger
from ocd_backend.models.model import PostgresDatabase
from ocd_backend.models.serializers import PostgresSerializer
from ocd_backend.models.postgres_models import Source, Property


log = get_source_logger('database_extractor')


class DatabaseBaseExtractor(BaseExtractor):
    """
    Base class for specific database extractors to inherit from.
    """

    def run(self):
        pass

    def __init__(self, *args, **kwargs):
        super(DatabaseBaseExtractor, self).__init__(*args, **kwargs)
        database = PostgresDatabase(serializer=PostgresSerializer)
        self.session = database.Session()
        self.unloaded_subresources = list()
        self.loaded_subresources = dict()

    def load_resource(self, resource_id):
        """
        Load a resource from the database.
        """
        resource = dict()
        resource['ori_id'] = resource_id
        resource['properties'] = []
        for resource_property in self.session.query(Property).filter(Property.resource_id == resource_id).order_by(
                    Property.predicate, Property.order):
            resource['properties'].append(self.flatten_property(resource_property))
            entity = resource_property.resource.sources[0].iri.rsplit('/')[-1]
        return resource, entity

    def load_subresources(self, subresource_ids, first):
        """
        Load all unloaded subresources from the database.
        """
        subresources = {}
        # Add the main resource to the dictionary to avoid endless loops
        subresources[first[0]['ori_id']] = first
        for subresource_id in subresource_ids:
            subresources[subresource_id] = self.load_subresource(subresource_id)
        return subresources

    def load_subresource(self, subresource_id):
        """
        Loads a subresource from the database. If the subresource has already been loaded, return it from the
        loaded_subresources cache.
        """

        if subresource_id in self.loaded_subresources:
            return self.loaded_subresources[subresource_id][0], \
                   self.loaded_subresources[subresource_id][1], \
                   self.loaded_subresources[subresource_id][2]
        else:
            subresource = dict()
            subresource['ori_id'] = subresource_id
            subresource['properties'] = []

            for resource_property in self.session.query(Property).filter(Property.resource_id == subresource_id).order_by(
                    Property.predicate, Property.order):
                try:
                    subresource['properties'].append(self.flatten_property(resource_property))
                    entity = resource_property.resource.sources[0].iri.rsplit('/')[-1]
                    collection = resource_property.resource.sources[0].iri.rsplit('/')[-2]
                except ValueError as e:
                    log.warning(e)

            self.loaded_subresources[subresource_id] = (subresource, entity, collection)
            return subresource, entity, collection

    def flatten_property(self, resource_property):
        """
        Takes the database row of a Property and flattens it to a dictionary with predicate, order (optional),
        property type and value.
        """

        flattened_property = dict()
        flattened_property['predicate'] = resource_property.predicate
        flattened_property['order'] = resource_property.order or None
        flattened_property['type'], flattened_property['value'] = self.get_property_type_and_value(resource_property)
        return flattened_property

    def get_property_type_and_value(self, resource_property):
        """
        Checks all columns of a database row of a Property and returns the type and value of the first non-empty
        column.
        """

        if resource_property.prop_resource:
            self.unloaded_subresources.append(resource_property.prop_resource)
            return 'resource', resource_property.prop_resource
        elif resource_property.prop_string:
            return 'string', resource_property.prop_string
        elif resource_property.prop_datetime:
            return 'datetime', resource_property.prop_datetime
        elif resource_property.prop_integer:
            return 'integer', resource_property.prop_integer
        elif resource_property.prop_url:
            return 'url', resource_property.prop_url
        elif resource_property.prop_json:
            return 'json', resource_property.prop_json
        else:
            raise ValueError('Unable to flatten property %s of resource ID %d: No value found in prop columns' %
                    (resource_property.predicate, resource_property.resource_id))


class DatabaseMeetingsExtractor(DatabaseBaseExtractor):
    """
    Extracts meetings from the database.
    """

    def run(self):
        collection = 'meeting'

        # Get the IDs of all Resources matching the key, supplier and collection. Since one Resource can have
        # multiple Sources we use a set to avoid duplicates.
        resource_ids = set()
        for source in self.session.query(Source).filter(Source.iri.contains('%s/%s/%s' %
                (self.source_definition['key'], self.source_definition['supplier'], collection))):
            resource_ids.add(source.resource_ori_id)

        meeting_count = 0
        for resource_id in resource_ids:
            meeting, entity = self.load_resource(resource_id)
            subresources = self.load_subresources(self.unloaded_subresources, first=(meeting, entity, collection))
            yield 'tuple', (meeting, subresources), entity, 'source_item_dummy'
            meeting_count += 1

        log.info(f'[{self.source_definition["key"]}] Extracted total of {meeting_count} meetings from database.')
        self.session.close()
