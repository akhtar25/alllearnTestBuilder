"""empty message

Revision ID: 9715b1128b2b
Revises: cdce07273e6e
Create Date: 2020-08-24 09:59:00.132530

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9715b1128b2b'
down_revision = 'cdce07273e6e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comments', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'comments', 'user', ['user_id'], ['id'])
    op.add_column('course_detail', sa.Column('average_rating', sa.Float(), nullable=True))
    op.add_column('course_review', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'course_review', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'course_review', type_='foreignkey')
    op.drop_column('course_review', 'user_id')
    op.drop_column('course_detail', 'average_rating')
    op.drop_constraint(None, 'comments', type_='foreignkey')
    op.drop_column('comments', 'user_id')
    # ### end Alembic commands ###
