import os

from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.loaders import JsonLDLoader
from ocd_backend.log import get_source_logger
from ocd_backend.utils import json_encoder

log = get_source_logger('loader')


class FileLoader(JsonLDLoader, HttpRequestMixin):
    def load_item(self, combined_object_id, object_id, combined_index_doc, doc,
                  doc_type):
        path = "/opt/ori/dumps/%s/%ss" % \
               (self.source_definition['index_name'], doc_type)
        print path
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError, e:  # Guard against race condition
                print "File path error", e

        try:
            file = open(path + '/' + object_id, "w")
            # print doc
            print "Write file %s/%s" % (path, object_id)
            file.write(json_encoder.encode(doc))
            file.close()
            return True
        except Exception, e:
            print "FILE LOADER ERROR: ", e
            return False
