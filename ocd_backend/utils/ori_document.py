import os
import shutil
import magic
import uuid
from ocd_backend.models.postgres_database import PostgresDatabase
from ocd_backend.models.postgres_models import StoredDocument
from ocd_backend.models.serializers import PostgresSerializer
from ocd_backend.settings import DATA_DIR_PATH
from ocd_backend.log import get_source_logger

log = get_source_logger('document_storage')

class OriDocument():
    def __init__(self, temp_path, item):
        self.temp_path = temp_path
        self.file_name = item.file_name
        self.file_size = item.size_in_bytes
        self.resource_ori_id = item.get_short_identifier()
        self.last_changed_at = self.get_last_changed_at(item)
        self.source, self.supplier = self.get_source_and_supplier(item)
        # RVD TODO use tesseract if no text was extracted

        database = PostgresDatabase(serializer=PostgresSerializer)
        self.session = database.Session()

    def store(self):
        with self.session.begin():
            self.store_in_db()
            self.store_on_disk()

    def store_in_db(self):
        self.stored_document = self.session.query(StoredDocument).filter(StoredDocument.resource_ori_id == self.resource_ori_id).first()
        if self.stored_document:
            self.stored_document.last_changed_at=self.last_changed_at
        else:
            content_type = magic.from_file(self.temp_path, mime=True)
            self.stored_document = StoredDocument(
                uuid=uuid.uuid1(),
                resource_ori_id=self.resource_ori_id,
                source=self.source,
                supplier=self.supplier,
                last_changed_at=self.last_changed_at,
                content_type=content_type,
                size=self.file_size
            )
            self.session.add(self.stored_document)

    def store_on_disk(self):
        destination_path = self.full_name()
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        shutil.move(self.temp_path, destination_path)

    def get_last_changed_at(self, item):
        """
        Notubiz returns a `last_modified` for documents, which gets stored in `date_modified`
        For other suppliers use the `last_discussed_at` (which is the best we can do here)
        """
        if hasattr(item, 'date_modified'):
            return item.date_modified
        elif hasattr(item, 'last_discussed_at'):
            return item.last_discussed_at
        else:
            return None

    def get_source_and_supplier(self, item):
        if item.source_iri:
            components = item.source_iri.split('/')
            return components[-4], components[-3]
        else:
            log.info(f"Error: no source_iri present for item {item.original_url}")

    @classmethod
    def _id_partitioned(cls, id):
        thousands = id//1000
        thousands_as_string = str(thousands).zfill(9)
        return f"{thousands_as_string[0:3]}/{thousands_as_string[3:6]}/{thousands_as_string[6:]}"
    
    def full_name(self):
        extension = os.path.splitext(self.file_name)[1]
        return f"{DATA_DIR_PATH}/{self._id_partitioned(self.stored_document.id)}/{self.resource_ori_id}{extension}"
