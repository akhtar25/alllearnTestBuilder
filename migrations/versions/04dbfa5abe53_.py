"""empty message

Revision ID: 04dbfa5abe53
Revises: 18db4b6ba609
Create Date: 2020-02-25 23:24:44.462090

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04dbfa5abe53'
down_revision = '18db4b6ba609'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('school_profile', sa.Column('impact_school_id', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('school_profile', 'impact_school_id')
    # ### end Alembic commands ###
