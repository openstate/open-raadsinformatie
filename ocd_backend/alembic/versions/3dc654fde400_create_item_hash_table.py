"""Create item hash table.

Revision ID: 3dc654fde400
Revises: 5b2ac6d04808
Create Date: 2024-01-18 14:52:33.587403

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3dc654fde400'
down_revision = '5b2ac6d04808'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('item_hash',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('item_id', sa.String(), nullable=False, index=True, unique=True),
    sa.Column('item_hash', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('item_hash')
