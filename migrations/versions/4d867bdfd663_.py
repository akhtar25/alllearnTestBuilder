"""empty message

Revision ID: 4d867bdfd663
Revises: b34f95795c8d
Create Date: 2019-10-10 19:15:52.153958

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d867bdfd663'
down_revision = 'b34f95795c8d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('access_status', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('school_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'school_profile', ['school_id'], ['school_id'])
    op.create_foreign_key(None, 'user', 'message_detail', ['access_status'], ['msg_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'school_id')
    op.drop_column('user', 'access_status')
    # ### end Alembic commands ###