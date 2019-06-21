from sqlalchemy import create_engine, Column, Sequence, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ocd_backend import settings


connection_string = 'postgresql://%s:%s@%s/%s' % (
    settings.POSTGRES_USERNAME,
    settings.POSTGRES_PASSWORD,
    settings.POSTGRES_HOST,
    settings.POSTGRES_DATABASE)


engine = create_engine(connection_string)


Base = declarative_base()


class Source(Base):
    __tablename__ = 'source'

    id = Column(Integer, Sequence('source_id_seq'), primary_key=True)
    iri = Column(String, unique=True)

    resources = relationship("Resource", back_populates="source")


class Resource(Base):
    __tablename__ = 'resource'

    id = Column(Integer, Sequence('resource_id_seq'), primary_key=True)
    ori_id = Column(Integer, Sequence('ori_id_seq'))
    iri = Column(String)
    source_iri_id = Column(Integer, ForeignKey("source.id"), nullable=False)

    source = relationship("Source", back_populates="resources")


Base.metadata.create_all(engine)
