"""first migration

Revision ID: 3b9423e49df5
Revises: 
Create Date: 2019-06-28 17:02:34.359825

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils.types.uuid import UUIDType


# revision identifiers, used by Alembic.
revision = '3b9423e49df5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.schema.CreateSequence(sa.schema.Sequence('ori_id_seq')))
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('source',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('iri', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('iri')
    )
    op.create_table('resource',
    sa.Column('ori_id', sa.Integer(), nullable=False),
    sa.Column('iri', sa.String(), nullable=True),
    sa.Column('source_iri_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['source_iri_id'], ['source.id'], ),
    sa.PrimaryKeyConstraint('ori_id')
    )
    op.create_table('property',
    sa.Column('id', UUIDType(), nullable=False),
    sa.Column('resource_id', sa.Integer(), nullable=False),
    sa.Column('predicate', sa.String(), nullable=False),
    sa.Column('prop_resource', sa.Integer(), nullable=True),
    sa.Column('prop_bool', sa.Boolean(), nullable=True),
    sa.Column('prop_string', sa.String(), nullable=True),
    sa.Column('prop_float', sa.Float(), nullable=True),
    sa.Column('prop_datetime', sa.DateTime(), nullable=True),
    sa.Column('prop_integer', sa.BigInteger(), nullable=True),
    sa.Column('prop_url', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['prop_resource'], ['resource.ori_id'], ),
    sa.ForeignKeyConstraint(['resource_id'], ['resource.ori_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('property')
    op.drop_table('resource')
    op.drop_table('source')
    # ### end Alembic commands ###