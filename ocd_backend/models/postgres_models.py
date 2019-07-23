from sqlalchemy import Column, Sequence, String, ForeignKey, DateTime, BigInteger, func, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy_utils.types import UUIDType


Base = declarative_base()


class Source(Base):
    __tablename__ = 'source'

    id = Column(BigInteger, Sequence('source_id_seq'), primary_key=True)
    iri = Column(String)
    resource_ori_id = Column(BigInteger, ForeignKey("resource.ori_id"), nullable=False)
    entity_type = Column(String)
    entity = Column(String)
    used_file = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())

    resource = relationship("Resource", back_populates="sources")


class Resource(Base):
    __tablename__ = 'resource'

    ori_id = Column(BigInteger, Sequence('ori_id_seq'), primary_key=True)
    iri = Column(String)

    sources = relationship("Source", back_populates="resource")
    properties = relationship("Property", back_populates="resource", foreign_keys="Property.resource_id")


class Property(Base):
    __tablename__ = 'property'
    __table_args__ = (
        CheckConstraint('NOT(prop_resource IS NULL AND '
                        'prop_string IS NULL AND '
                        'prop_datetime IS NULL AND '
                        'prop_integer IS NULL AND '
                        'prop_url IS NULL'),
    )

    id = Column(UUIDType(), primary_key=True)
    resource_id = Column(BigInteger, ForeignKey("resource.ori_id"), nullable=False)
    predicate = Column(String, nullable=False)
    order = Column(BigInteger, nullable=True)
    prop_resource = Column(BigInteger, ForeignKey("resource.ori_id"), nullable=True)
    prop_string = Column(String, nullable=True)
    prop_datetime = Column(DateTime, nullable=True)
    prop_integer = Column(BigInteger, nullable=True)
    prop_url = Column(String, nullable=True)

    resource = relationship("Resource", back_populates="properties", foreign_keys=resource_id)
