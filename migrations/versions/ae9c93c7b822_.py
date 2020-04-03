"""empty message

Revision ID: ae9c93c7b822
Revises: 721d07c44cfa
Create Date: 2020-04-03 18:07:16.491861

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae9c93c7b822'
down_revision = '721d07c44cfa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topic_tracker', sa.Column('is_archived', sa.String(length=1), nullable=True))
    op.add_column('topic_tracker', sa.Column('target_covered_date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('topic_tracker', 'target_covered_date')
    op.drop_column('topic_tracker', 'is_archived')
    # ### end Alembic commands ###
