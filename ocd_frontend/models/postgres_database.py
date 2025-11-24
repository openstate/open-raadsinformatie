import json
import os
from utils.pdf_naming import PdfNaming
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.pool import StaticPool

from ocd_frontend import settings
from ocd_frontend.models.postgres_models import Source, StoredDocument

class FrontendPostgresDatabase:
    connection_string = 'postgresql://%s:%s@%s/%s' % (
                                settings.POSTGRES_USERNAME,
                                settings.POSTGRES_PASSWORD,
                                settings.POSTGRES_HOST,
                                settings.POSTGRES_DATABASE)
    engine = create_engine(connection_string, poolclass=StaticPool)
    Session = sessionmaker(bind=engine)

    def _process_stored_document(self, stored_document, format):
        if not stored_document:
            return None, None, None

        # Get filename from metadata
        metadata_filename = PdfNaming.full_metadata_name_cls(settings.DATA_DIR_PATH, stored_document.id, stored_document.resource_ori_id)
        with open(metadata_filename, 'r') as f:
            metadata = json.load(f)
            filename = metadata['filename']

        if format == PdfNaming.FORMAT_MARKDOWN:
            markdown_filename = PdfNaming.full_markdown_name_cls(settings.DATA_DIR_PATH, stored_document.id, stored_document.resource_ori_id)
            return 'text/plain', f"{filename}.md", markdown_filename
        elif format == PdfNaming.FORMAT_METADATA:
            return 'text/plain', f"{filename}.metadata", metadata_filename
        else:
            content_type = metadata['content_type']
            extension = os.path.splitext(filename)[1] if filename else ""
            basename = PdfNaming.original_name_cls(settings.DATA_DIR_PATH, stored_document.id, stored_document.resource_ori_id)
            return content_type, filename, f"{basename}{extension}"

    
    def get_fullpath_from_canonical_id(self, canonical_id, format):
        session = self.Session()
        try:
            stored_document = session \
                .query(StoredDocument) \
                .join(Source, StoredDocument.resource_ori_id == Source.resource_ori_id) \
                .filter(Source.canonical_id == str(canonical_id)).first()
            return self._process_stored_document(stored_document, format)

        except MultipleResultsFound:
            raise MultipleResultsFound(f'Multiple stored_documents found for canonical_id{canonical_id}')
        except NoResultFound:
            return None, None, None
        finally:
            session.close()

    def get_fullpath_from_canonical_iri(self, canonical_iri, format):
        session = self.Session()
        try:
            stored_document = session \
                .query(StoredDocument) \
                .join(Source, StoredDocument.resource_ori_id == Source.resource_ori_id) \
                .filter(Source.canonical_iri == str(canonical_iri)).first()
            return self._process_stored_document(stored_document, format)

        except MultipleResultsFound:
            raise MultipleResultsFound(f'Multiple stored_documents found for canonical_iri {canonical_iri}')
        except NoResultFound:
            return None, None, None
        finally:
            session.close()

    def get_fullpath_from_canonical_iri_like(self, canonical_iri, format):
        session = self.Session()
        try:
            stored_document = session \
                .query(StoredDocument) \
                .join(Source, StoredDocument.resource_ori_id == Source.resource_ori_id) \
                .filter(Source.canonical_iri.like(f"{canonical_iri}%")).first()
            return self._process_stored_document(stored_document, format)

        except MultipleResultsFound:
            raise MultipleResultsFound(f'Multiple stored_documents found for canonical_iri {canonical_iri}')
        except NoResultFound:
            return None, None, None
        finally:
            session.close()
