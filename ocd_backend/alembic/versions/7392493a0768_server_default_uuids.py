"""server default uuids

Revision ID: 7392493a0768
Revises: 58d71214c327
Create Date: 2019-11-01 14:47:27.259869

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7392493a0768'
down_revision = '58d71214c327'
branch_labels = None
depends_on = None


def upgrade():
    # Requires "CREATE EXTENSION pgcrypto;" but needs elevated permissions
    op.alter_column('property', 'id', nullable=False, server_default=sa.text("gen_random_uuid()"))
    # ### end Alembic commands ###


def downgrade():
    op.alter_column('property', 'id', nullable=False, server_default=None)
    # ### end Alembic commands ###
