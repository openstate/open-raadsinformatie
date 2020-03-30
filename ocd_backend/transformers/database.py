from collections import namedtuple
from copy import deepcopy

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.transformers import BaseTransformer
from ocd_backend.utils.misc import load_object
from ocd_backend.models.model import PostgresDatabase
from ocd_backend.models.serializers import PostgresSerializer

log = get_source_logger('database_transformer')


RelationPlaceholder = namedtuple('RelationPlaceholder', 'ori_id')


class DatabaseTransformer(BaseTransformer):
    """
    Base class for specific database transformers to inherit from.
    """

    def __init__(self, *args, **kwargs):
        super(DatabaseTransformer, self).__init__(*args, **kwargs)
        self.database = PostgresDatabase(serializer=PostgresSerializer)
        self.created_models = dict()
        self.processed_subresources = set()

    @staticmethod
    def get_model_class(properties):
        """
        Finds the "type" property in the list of properties and imports the model class of that name.
        """
        for _property in properties:
            if _property['predicate'] == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
                try:
                    return load_object('ocd_backend.models.%s' % _property['value'])
                except ImportError:
                    raise ImportError('Unable to import class "ocd_backend.models.%s"' % _property['value'])
        raise ValueError('Unable to get model class: Object contains no "type" property.')

    def get_supplier(self, ori_id):
        """
        Retrieves the supplier of the Resource with the given ORI ID from the database.
        """
        try:
            return self.database.get_supplier(ori_id)
        except ValueError:
            raise ValueError('Unable to get supplier for ori_id %d' % ori_id)

    def create_resource(self, resource, entity):
        """
        Creates the main resource with placeholders for relations.
        """
        model_class = self.get_model_class(resource['properties'])
        source_defaults = {
            'source': self.source_definition['key'],
            'supplier': self.get_supplier(resource['ori_id']),
            'collection': model_class.__name__.lower(),
        }
        item = model_class(entity, **source_defaults)
        item.ori_identifier = 'https://id.openraadsinformatie.nl/' + str(resource['ori_id'])

        # Reconstruct properties with RelationPlaceholders for references to subresources
        for _property in resource['properties']:
            # Ignore the "type" property
            if _property['predicate'] == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
                continue

            try:
                attr_name = self.match_predicate(_property, item._definitions)
            except ValueError:
                continue

            if _property['type'] == 'resource':
                attr_value = RelationPlaceholder(_property['value'])
            else:
                attr_value = _property['value']

            try:
                # If the attribute already exists, turn it into a list of attributes
                attr = getattr(item, attr_name)
                if not isinstance(attr, list):
                    setattr(item, attr_name, [attr,])
                getattr(item, attr_name).append(attr_value)
            except AttributeError:
                setattr(item, attr_name, attr_value)

        # Set the identifier_url for the enricher
        if item.values.get('original_url'):
            item.values['identifier_url'] = item.values.get('original_url')

        self.created_models[resource['ori_id']] = item
        return item

    def create_subresource(self, resource, entity, collection):
        """
        Creates all subresources (without properties).
        """
        if resource['ori_id'] in self.created_models:
            return self.created_models[resource['ori_id']]

        model_class = self.get_model_class(resource['properties'])
        source_defaults = {
            'source': self.source_definition['key'],
            'supplier': self.get_supplier(resource['ori_id']),
            'collection': collection,
        }
        item = model_class(entity, **source_defaults)
        item.ori_identifier = 'https://id.openraadsinformatie.nl/' + str(resource['ori_id'])

        self.created_models[resource['ori_id']] = item
        return item

    def add_subresource_properties(self, subresource, subresources):
        """
        Adds properties to the given subresource.
        """
        if subresource.ori_identifier.rsplit('/')[-1] in self.processed_subresources:
            return

        try:
            properties = subresources[int(subresource.ori_identifier.rsplit('/')[-1])][0]['properties']
        except KeyError:
            properties = subresources[subresource.ori_identifier.rsplit('/')[-1]][0]['properties']

        for _property in properties:
            # Ignore the "type" property
            if _property['predicate'] == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
                continue

            try:
                attr_name = self.match_predicate(_property, subresource._definitions)
            except ValueError:
                continue

            if _property['type'] == 'resource':
                attr_value = self.created_models[_property['value']]
            else:
                attr_value = _property['value']

            try:
                # If the attribute already exists, turn it into a list of attributes
                attr = getattr(subresource, attr_name)
                if not isinstance(attr, list):
                    setattr(subresource, attr_name, [attr,])
                getattr(subresource, attr_name).append(attr_value)
            except AttributeError:
                setattr(subresource, attr_name, attr_value)

        # Set the identifier_url for the enricher
        if subresource.values.get('original_url'):
            subresource.values['identifier_url'] = subresource.values.get('original_url')

        self.processed_subresources.add(subresource.ori_identifier.rsplit('/')[-1])

    @staticmethod
    def match_predicate(_property, definitions):
        """
        Matches the predicate of a property with the definition on a model class.
        """
        for definition in definitions.items():
            if definition[1].ns.uri + definition[1]._name == _property['predicate']:
                return definition[0]
        raise ValueError('No match found in model definitions for property with predicate "%s"' % _property['predicate'])


@celery_app.task(bind=True, base=DatabaseTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def database_item(self, content_type, raw_item, entity, source_item, **kwargs):
    self.source_definition = kwargs['source_definition']
    resource, subresources = raw_item

    # Create the main resource
    item = self.create_resource(resource, entity)

    # Create subresources (without properties)
    for subresource in subresources.items():
        self.create_subresource(subresource[1][0], subresource[1][1], subresource[1][2])

    # Add the main resource to the list of processed subresources to prevent overwriting of its properties
    self.processed_subresources.add(item.ori_identifier.rsplit('/')[-1])

    # Add properties to subresources
    for subresource in self.created_models.items():
        self.add_subresource_properties(subresource[1], subresources)

    # Replace relation placeholders on main resource
    for _property in item.values.items():
        if isinstance(_property[1], RelationPlaceholder):
            setattr(item, _property[0], self.created_models[_property[1].ori_id])
        elif isinstance(_property[1], list):
            nested_properties = deepcopy(_property[1])
            setattr(item, _property[0], [])
            for nested_property in nested_properties:
                getattr(item, _property[0]).append(self.created_models[nested_property.ori_id])

    return item
