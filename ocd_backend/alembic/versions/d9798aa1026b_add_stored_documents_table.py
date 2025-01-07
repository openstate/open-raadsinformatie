"""Add stored_documents table

Revision ID: d9798aa1026b
Revises: 3dc654fde400
Create Date: 2024-12-18 17:16:00.073993

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils.types.uuid import UUIDType


# revision identifiers, used by Alembic.
revision = 'd9798aa1026b'
down_revision = '3dc654fde400'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('stored_documents',
    sa.Column('id', sa.BigInteger(), primary_key=True, nullable=False, autoincrement=True),
    sa.Column('uuid', UUIDType(), nullable=False, index=True),
    sa.Column('resource_ori_id', sa.BigInteger(), nullable=False, index=True, unique=True),
    sa.Column('source', sa.String(), nullable=False),
    sa.Column('supplier', sa.String(), nullable=False),
    sa.Column('last_changed_at', sa.DateTime(), nullable=True),
    sa.Column('content_type', sa.String(), nullable=False),
    sa.Column('file_size', sa.BigInteger(), nullable=False),
    sa.Column('ocr_used', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['resource_ori_id'], ['resource.ori_id'], ),
    )


def downgrade():
    op.drop_table('stored_documents')
