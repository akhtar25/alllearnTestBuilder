"""empty message

Revision ID: ddab542c86da
Revises: 
Create Date: 2020-07-07 14:10:04.778448

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ddab542c86da'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('student_homework_response', sa.Column('is_archived', sa.String(length=1), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('student_homework_response', 'is_archived')
    # ### end Alembic commands ###
