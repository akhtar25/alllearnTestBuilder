"""empty message

Revision ID: 0c06967ef177
Revises: 04253ec81309
Create Date: 2020-02-25 22:53:10.921915

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c06967ef177'
down_revision = '04253ec81309'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('school_profile', 'impact_school_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('school_profile', sa.Column('impact_school_id', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###