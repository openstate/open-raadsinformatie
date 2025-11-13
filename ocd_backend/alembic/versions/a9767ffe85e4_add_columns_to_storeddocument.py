"""Add columns to StoredDocument

Revision ID: a9767ffe85e4
Revises: d9798aa1026b
Create Date: 2025-11-13 16:47:03.858376

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9767ffe85e4'
down_revision = 'd9798aa1026b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stored_documents', sa.Column('markdown_used', sa.String(), nullable=True))


def downgrade():
    op.drop_column('stored_documents', 'markdown_used')
