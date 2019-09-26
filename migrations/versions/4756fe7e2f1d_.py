"""empty message

Revision ID: 4756fe7e2f1d
Revises: 99dcf9f30aa1
Create Date: 2019-09-26 16:21:03.759271

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4756fe7e2f1d'
down_revision = '99dcf9f30aa1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('content_detail', sa.Column('content_type', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'content_detail', 'message_detail', ['content_type'], ['msg_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'content_detail', type_='foreignkey')
    op.drop_column('content_detail', 'content_type')
    # ### end Alembic commands ###