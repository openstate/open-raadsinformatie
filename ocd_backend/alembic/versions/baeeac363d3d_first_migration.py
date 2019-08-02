"""first migration

Revision ID: baeeac363d3d
Revises: 
Create Date: 2019-07-23 11:43:16.531116

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils.types.uuid import UUIDType


# revision identifiers, used by Alembic.
revision = 'baeeac363d3d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.schema.CreateSequence(sa.schema.Sequence('ori_id_seq')))
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('resource',
    sa.Column('ori_id', sa.BigInteger(), nullable=False),
    sa.Column('iri', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('ori_id')
    )
    op.create_table('property',
    sa.Column('id', UUIDType(), nullable=False),
    sa.Column('resource_id', sa.BigInteger(), nullable=False),
    sa.Column('predicate', sa.String(), nullable=False),
    sa.Column('order', sa.BigInteger(), nullable=True),
    sa.Column('prop_resource', sa.BigInteger(), nullable=True),
    sa.Column('prop_string', sa.String(), nullable=True),
    sa.Column('prop_datetime', sa.DateTime(), nullable=True),
    sa.Column('prop_integer', sa.BigInteger(), nullable=True),
    sa.Column('prop_url', sa.String(), nullable=True),
    sa.CheckConstraint(u'NOT(prop_resource IS NULL AND prop_string IS NULL AND prop_datetime IS NULL AND prop_integer IS NULL AND prop_url IS NULL)'),
    sa.ForeignKeyConstraint(['prop_resource'], ['resource.ori_id'], ),
    sa.ForeignKeyConstraint(['resource_id'], ['resource.ori_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('source',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('iri', sa.String(), nullable=True),
    sa.Column('resource_ori_id', sa.BigInteger(), nullable=False),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('entity', sa.String(), nullable=True),
    sa.Column('used_file', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['resource_ori_id'], ['resource.ori_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('source')
    op.drop_table('property')
    op.drop_table('resource')
    # ### end Alembic commands ###