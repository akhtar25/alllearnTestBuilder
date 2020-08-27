"""empty message

Revision ID: d493a26379c1
Revises: 87b0239ffb16
Create Date: 2020-08-27 15:49:11.086777

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd493a26379c1'
down_revision = '87b0239ffb16'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('course_topics', sa.Column('video_class_url', sa.String(length=300), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('course_topics', 'video_class_url')
    # ### end Alembic commands ###
