"""empty message

Revision ID: 4873c6a0a311
Revises: 97ea0741acc1
Create Date: 2019-06-21 13:00:23.372045

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4873c6a0a311'
down_revision = '97ea0741acc1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('question_options', 'is_correct')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('question_options', sa.Column('is_correct', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
