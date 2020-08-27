"""empty message

Revision ID: 27aee03b412b
Revises: d493a26379c1
Create Date: 2020-08-27 15:53:21.000076

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27aee03b412b'
down_revision = 'd493a26379c1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('course_batch', sa.Column('is_ongoing', sa.String(length=1), nullable=True))
    op.add_column('course_batch', sa.Column('ongoing_topic_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'course_batch', 'topic_detail', ['ongoing_topic_id'], ['topic_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'course_batch', type_='foreignkey')
    op.drop_column('course_batch', 'ongoing_topic_id')
    op.drop_column('course_batch', 'is_ongoing')
    # ### end Alembic commands ###
