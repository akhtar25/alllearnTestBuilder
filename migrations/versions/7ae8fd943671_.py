"""empty message

Revision ID: 7ae8fd943671
Revises: d27500f15dfc
Create Date: 2020-05-03 00:40:47.497310

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ae8fd943671'
down_revision = 'd27500f15dfc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('inventory_allocation_stud',
    sa.Column('alloc_id', sa.Integer(), nullable=False),
    sa.Column('inv_id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('count', sa.Float(), nullable=False),
    sa.Column('allocation_type', sa.String(length=1), nullable=True),
    sa.Column('allocation_status', sa.Integer(), nullable=False),
    sa.Column('is_archived', sa.String(length=1), nullable=True),
    sa.Column('last_modified_date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['allocation_status'], ['message_detail.msg_id'], ),
    sa.ForeignKeyConstraint(['inv_id'], ['inventory_detail.inv_id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['student_profile.student_id'], ),
    sa.PrimaryKeyConstraint('alloc_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('inventory_allocation_stud')
    # ### end Alembic commands ###
