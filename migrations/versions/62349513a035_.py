"""empty message

Revision ID: 62349513a035
Revises: ea4d08ca3c5f
Create Date: 2020-08-14 13:55:47.334017

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '62349513a035'
down_revision = 'ea4d08ca3c5f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('course_detail', sa.Column('ideal_for', sa.String(length=100), nullable=True))
    op.add_column('course_topics', sa.Column('test_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'course_topics', 'test_details', ['test_id'], ['test_id'])
    op.add_column('test_questions', sa.Column('is_archived', sa.String(length=1), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('test_questions', 'is_archived')
    op.drop_constraint(None, 'course_topics', type_='foreignkey')
    op.drop_column('course_topics', 'test_id')
    op.drop_column('course_detail', 'ideal_for')
    # ### end Alembic commands ###
