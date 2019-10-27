"""empty message

Revision ID: 2b5a1caadeb7
Revises: 5e91aaf4e388
Create Date: 2019-10-18 22:01:31.765763

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b5a1caadeb7'
down_revision = '5e91aaf4e388'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('invoice_detail', sa.Column('pay_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'invoice_detail', 'payment_detail', ['pay_id'], ['pay_id'])
    op.add_column('school_profile', sa.Column('sub_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'school_profile', 'subscription_detail', ['sub_id'], ['sub_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'school_profile', type_='foreignkey')
    op.drop_column('school_profile', 'sub_id')
    op.drop_constraint(None, 'invoice_detail', type_='foreignkey')
    op.drop_column('invoice_detail', 'pay_id')
    # ### end Alembic commands ###