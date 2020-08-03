"""empty message

Revision ID: d5059b5b26be
Revises: 4438f85e30ec
Create Date: 2020-08-03 18:16:14.896152

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5059b5b26be'
down_revision = '4438f85e30ec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('login_type', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'message_detail', ['login_type'], ['msg_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'login_type')
    # ### end Alembic commands ###
