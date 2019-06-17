"""empty message

Revision ID: 3ebb2ba02d0e
Revises: 823f9d724e9a
Create Date: 2019-06-13 14:28:23.434770

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ebb2ba02d0e'
down_revision = '823f9d724e9a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('teacher_profile', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'teacher_profile', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'teacher_profile', type_='foreignkey')
    op.drop_column('teacher_profile', 'user_id')
    # ### end Alembic commands ###