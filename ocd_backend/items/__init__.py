class BaseItem(object):

    def __init__(self, original_item, source_definition):
        self.original_item = original_item
        self.source_definition = source_definition

    def transform(self):
        raise NotImplementedError
