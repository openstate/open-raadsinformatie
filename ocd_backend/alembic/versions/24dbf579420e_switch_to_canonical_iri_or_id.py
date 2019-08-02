"""switch to canonical iri or id

Revision ID: 24dbf579420e
Revises: 1afd444fda6b
Create Date: 2019-07-31 17:10:49.264005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '24dbf579420e'
down_revision = '1afd444fda6b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('source', sa.Column('canonical_id', sa.String(), nullable=True))
    op.add_column('source', sa.Column('canonical_iri', sa.String(), nullable=True))
    op.drop_column('source', 'entity')
    op.drop_column('source', 'entity_type')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('source', sa.Column('entity_type', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('source', sa.Column('entity', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('source', 'canonical_iri')
    op.drop_column('source', 'canonical_id')
    # ### end Alembic commands ###