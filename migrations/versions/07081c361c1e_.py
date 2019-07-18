"""empty message

Revision ID: 07081c361c1e
Revises: 
Create Date: 2019-07-18 13:22:53.381776

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07081c361c1e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('guardian_profile', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'guardian_profile', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'guardian_profile', type_='foreignkey')
    op.drop_column('guardian_profile', 'user_id')
    # ### end Alembic commands ###
