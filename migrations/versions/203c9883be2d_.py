"""empty message

Revision ID: 203c9883be2d
Revises: 
Create Date: 2020-11-30 13:18:52.709253

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '203c9883be2d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('response_capture', sa.Column('answer_type', sa.Integer(), nullable=True))
    op.add_column('response_capture', sa.Column('question_type', sa.String(length=120), nullable=True))
    op.create_foreign_key(None, 'response_capture', 'message_detail', ['answer_type'], ['msg_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'response_capture', type_='foreignkey')
    op.drop_column('response_capture', 'question_type')
    op.drop_column('response_capture', 'answer_type')
    # ### end Alembic commands ###