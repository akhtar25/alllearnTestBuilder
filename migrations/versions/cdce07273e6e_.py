"""empty message

Revision ID: cdce07273e6e
Revises: 9d89b8c8bbf2
Create Date: 2020-08-23 17:18:35.580043

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cdce07273e6e'
down_revision = '9d89b8c8bbf2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('batch_test',
    sa.Column('batch_test_id', sa.Integer(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('test_id', sa.Integer(), nullable=True),
    sa.Column('resp_session_id', sa.String(length=50), nullable=False),
    sa.Column('is_current', sa.String(length=1), nullable=False),
    sa.Column('is_archived', sa.String(length=1), nullable=False),
    sa.Column('last_modified_date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['batch_id'], ['course_batch.batch_id'], ),
    sa.ForeignKeyConstraint(['test_id'], ['test_details.test_id'], ),
    sa.ForeignKeyConstraint(['topic_id'], ['topic_detail.topic_id'], ),
    sa.PrimaryKeyConstraint('batch_test_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('batch_test')
    # ### end Alembic commands ###
