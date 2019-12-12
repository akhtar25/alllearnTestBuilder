"""empty message

Revision ID: 480e66c91402
Revises: 61d1b0e8821f
Create Date: 2019-11-02 23:36:39.065907

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '480e66c91402'
down_revision = '61d1b0e8821f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('job_application', sa.Column('job_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'job_application', 'job_detail', ['job_id'], ['job_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'job_application', type_='foreignkey')
    op.drop_column('job_application', 'job_id')
    # ### end Alembic commands ###