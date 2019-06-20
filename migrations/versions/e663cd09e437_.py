"""empty message

Revision ID: e663cd09e437
Revises: 
Create Date: 2019-06-20 13:06:09.692465

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e663cd09e437'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('question_details', sa.Column('topic_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'question_details', 'topic_detail', ['topic_id'], ['topic_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'question_details', type_='foreignkey')
    op.drop_column('question_details', 'topic_id')
    # ### end Alembic commands ###
