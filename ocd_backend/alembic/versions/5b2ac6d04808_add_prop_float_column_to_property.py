"""add prop_float column to property

Revision ID: 5b2ac6d04808
Revises: 4415298e147b
Create Date: 2020-02-13 16:15:38.150696

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5b2ac6d04808'
down_revision = '4415298e147b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('property', sa.Column('prop_float', sa.Float(), nullable=True))
    op.drop_constraint('property_check', 'property')
    op.create_check_constraint('property_check', 'property', 'NOT(prop_resource IS NULL AND prop_string IS NULL AND prop_datetime IS NULL AND prop_integer IS NULL AND prop_float IS NULL AND prop_url IS NULL AND prop_json IS NULL)'),


def downgrade():
    op.drop_constraint('property_check', 'property')
    op.create_check_constraint('property_check', 'property', 'NOT(prop_resource IS NULL AND prop_string IS NULL AND prop_datetime IS NULL AND prop_integer IS NULL AND prop_url IS NULL AND prop_json IS NULL)'),
    op.drop_column('property', 'prop_float')
