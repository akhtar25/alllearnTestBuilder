"""empty message

Revision ID: 83ada2e931ca
Revises: 6f64f4e4b3bb
Create Date: 2019-06-11 18:02:48.381719

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '83ada2e931ca'
down_revision = '6f64f4e4b3bb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('slide_tracker')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('slide_tracker',
    sa.Column('slideshow_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('last_modified_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('subject_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('topic_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['subject_id'], ['message_detail.msg_id'], name='slide_tracker_subject_id_fkey'),
    sa.ForeignKeyConstraint(['topic_id'], ['topic_detail.topic_id'], name='slide_tracker_topic_id_fkey'),
    sa.PrimaryKeyConstraint('slideshow_id', name='slide_tracker_pkey')
    )
    # ### end Alembic commands ###