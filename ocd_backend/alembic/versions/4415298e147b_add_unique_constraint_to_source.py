"""add unique constraint to Source

Revision ID: 4415298e147b
Revises: 7392493a0768
Create Date: 2020-01-02 16:41:03.424945

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4415298e147b'
down_revision = '7392493a0768'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint('ori_id_canonical_fields', 'source', ['resource_ori_id', 'canonical_id', 'canonical_iri'])


def downgrade():
    op.drop_constraint('ori_id_canonical_fields', 'source')
