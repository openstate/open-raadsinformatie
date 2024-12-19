import os
import magic
from ocd_backend.models.postgres_database import PostgresDatabase
from ocd_backend.models.postgres_models import StoredDocument
from ocd_backend.models.serializers import PostgresSerializer
from ocd_backend.settings import DATA_DIR_PATH


class DocumentStorage():
    def __init__(self, temp_path, file_name, file_size, resource_ori_id):
        self.temp_path = temp_path
        self.file_name = file_name
        self.file_size = file_size
        self.resource_ori_id = resource_ori_id

        database = PostgresDatabase(serializer=PostgresSerializer)
        self.session = database.Session()

    def store(self):
        self.store_in_db()
        self.store_on_disk()

    def store_in_db(self):
        self.stored_document = self.session.query(StoredDocument).filter(StoredDocument.resource_ori_id == self.resource_ori_id).first()
        if not self.stored_document:
            content_type = magic.from_file(self.temp_path, mime=True)
            self.stored_document = StoredDocument(resource_ori_id=self.resource_ori_id, content_type=content_type, size = self.file_size)
            self.session.add(self.stored_document)
            self.session.commit()
            self.session.flush()

    def store_on_disk(self):
        destination_path = self.full_name()
        file = open(destination_path, mode="w+b")
        # TODO

    @classmethod
    def _id_partitioned(cls, id):
        thousands = id//1000
        thousands_as_string = str(thousands).zfill(9)
        return f"{thousands_as_string[0:3]}/{thousands_as_string[3:6]}/{thousands_as_string[6:]}"
    
    def full_name(self, id, name):
        extension = os.path.splitext(self.file_name)
        return f"{DATA_DIR_PATH}/{self._id_partitioned(self.stored_document.id)}/{self.resource_ori_id}{extension}"
