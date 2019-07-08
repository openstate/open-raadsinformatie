class BaseItem(object):

    def __init__(self, deserialized_item, entity, source_definition):
        self.original_item = deserialized_item
        self.entity = entity
        self.source_definition = source_definition

    def transform(self):
        raise NotImplementedError
