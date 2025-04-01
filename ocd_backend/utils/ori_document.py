import json
import os
import shutil
import magic
import uuid
import datetime
import sqlalchemy as sa
from ocd_backend.models.postgres_database import PostgresDatabase
from ocd_backend.models.postgres_models import StoredDocument
from ocd_backend.models.serializers import PostgresSerializer
from ocd_backend.settings import DATA_DIR_PATH
from ocd_backend.log import get_source_logger

log = get_source_logger('document_storage')

class OriDocument():
    def __init__(self, temp_path, item, metadata, ocr_used = None):
        self.temp_path = temp_path
        self.file_name = item.file_name if hasattr(item, 'file_name') else None
        self.md_text = item.md_text
        self.file_size = item.size_in_bytes
        self.resource_ori_id = item.get_short_identifier()
        self.last_changed_at = self.get_last_changed_at(item)
        self.source, self.supplier = self.get_source_and_supplier(item)
        self.ocr_used = ocr_used
        self.metadata = metadata

        self.metadata['content_type'] = item.content_type
        self.metadata['size'] = self.file_size
        self.metadata['filename'] = self.file_name
        self.metadata['last_changed_at'] = self.last_changed_at.isoformat() if self.last_changed_at else ''
        self.metadata['original_url'] = item.original_url if hasattr(item, 'original_url') else ''
        self.metadata['ocr_used'] = ocr_used if ocr_used else ''

        database = PostgresDatabase(serializer=PostgresSerializer)
        self.session = database.Session()

    def store(self):
        try:
            with self.session.begin():
                self.stored_document = self.session.query(StoredDocument).filter(StoredDocument.resource_ori_id == self.resource_ori_id).first()
                if self.exists_and_not_changed():
                    log.info(f"Document exists and has not changed - not storing {self.resource_ori_id} {self.metadata['original_url']}")
                    return
                self.store_in_db()
                self.store_on_disk()
                self.store_markdown_on_disk()
                self.store_metadata_on_disk()
        except sa.exc.IntegrityError as e:
            log.info(f"IntegrityError in OriDocument when saving stored_document: {str(e)}")
            self.session.rollback()
            raise e

    def exists_and_not_changed(self):
        if not self.stored_document:
            return False

        # Check whether database values changed
        if self.stored_document.last_changed_at != self.last_changed_at or \
            self.stored_document.file_size != self.file_size or \
            self.stored_document.ocr_used != self.ocr_used or \
            self.stored_document.file_size != self.file_size:
            return False

        # Check whether markdown values changed
        text_array = self.md_text if self.md_text is not None else []
        md_text = ''.join([f"{page}\n" for page in text_array])
        if self.file_contents_changed(self.full_markdown_name(), md_text):
            return False

        # Check whether metadata values changed
        metadata = json.dumps(self.metadata, indent=2)
        if self.file_contents_changed(self.full_metadata_name(), metadata):
            return False

        return True

    def file_contents_changed(self, filename, new_contents):
        if not os.path.exists(filename):
            changed = new_contents is not None
            return changed

        with open(filename, "r") as f:
            contents = f.read()
            if new_contents != contents:
                return True

        return False

    def store_in_db(self):
        time_now = datetime.datetime.now(tz=datetime.timezone.utc)
        if self.stored_document:
            self.stored_document.last_changed_at = self.last_changed_at
            self.stored_document.file_size = self.file_size
            self.stored_document.ocr_used = self.ocr_used
            self.stored_document.updated_at = time_now
        else:
            content_type = magic.from_file(self.temp_path, mime=True)
            self.stored_document = StoredDocument(
                uuid=uuid.uuid1(),
                resource_ori_id=self.resource_ori_id,
                source=self.source,
                supplier=self.supplier,
                last_changed_at=self.last_changed_at,
                content_type=content_type,
                file_size=self.file_size,
                ocr_used=self.ocr_used,
                created_at=time_now,
                updated_at=time_now
            )
            self.session.add(self.stored_document)
            # Flush session to set autoincrement id in self.stored_document before commit
            self.session.flush()

    def store_on_disk(self):
        destination_path = self.full_name()
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        shutil.move(self.temp_path, destination_path)

    def store_markdown_on_disk(self):
        if self.md_text is None:
            return
        
        with open(self.full_markdown_name(), "w", errors="surrogatepass") as f:
            for page in self.md_text:
                f.write(f"{page}\n")

    def store_metadata_on_disk(self):
        with open(self.full_metadata_name(), "w", errors="surrogatepass") as f:
            f.write(json.dumps(self.metadata, indent=2))

    def get_last_changed_at(self, item):
        """
        Notubiz returns a `last_modified` for documents, which gets stored in `date_modified`
        For other suppliers use the `last_discussed_at` (which is the best we can do here)
        Convert to UCT and remove tzinfo so that this date can be compared to date stored in database in exists_and_not_changed()
        """
        if hasattr(item, 'date_modified'):
            return item.date_modified.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        elif hasattr(item, 'last_discussed_at'):
            return item.last_discussed_at.astimezone(datetime.timezone.utc).replace(tzinfo=None)
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
        extension = os.path.splitext(self.file_name)[1] if self.file_name else ""
        return f"{self._base_name()}{extension}"
    
    def full_markdown_name(self):
        return f"{self._base_name()}.md"
    
    def full_metadata_name(self):
        return f"{self._base_name()}.metadata"

    def _base_name(self):
        return f"{DATA_DIR_PATH}/{self._id_partitioned(self.stored_document.id)}/{self.resource_ori_id}"
