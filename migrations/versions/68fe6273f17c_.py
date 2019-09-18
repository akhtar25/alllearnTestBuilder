"""empty message

Revision ID: 68fe6273f17c
Revises: 9377eacb2560
Create Date: 2019-09-17 14:59:31.816329

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '68fe6273f17c'
down_revision = '9377eacb2560'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('question_details', sa.Column('archive_status', sa.String(length=1), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('question_details', 'archive_status')
    # ### end Alembic commands ###