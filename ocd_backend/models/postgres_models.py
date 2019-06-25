from sqlalchemy import Column, Sequence, Integer, String, Text, ForeignKey, Boolean, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy_utils.types import UUIDType


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
    properties = relationship("Property", back_populates="resource", foreign_keys="Property.resource_id")


class Property(Base):
    __tablename__ = 'property'

    id = Column(UUIDType(), primary_key=True)
    resource_id = Column(Integer, ForeignKey("resource.id"), nullable=False)
    predicate = Column(String, nullable=False)
    prop_resource = Column(Integer, ForeignKey("resource.id"), nullable=True)
    prop_bool = Column(Boolean, nullable=True)
    prop_string = Column(String, nullable=True)
    prop_text = Column(Text, nullable=True)
    prop_datetime = Column(DateTime, nullable=True)
    prop_integer = Column(BigInteger, nullable=True)

    resource = relationship("Resource", back_populates="properties", foreign_keys=resource_id)
