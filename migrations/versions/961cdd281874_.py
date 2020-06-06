"""empty message

Revision ID: 961cdd281874
Revises: 37bb52d71d71
Create Date: 2020-06-07 03:54:30.548503

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '961cdd281874'
down_revision = '37bb52d71d71'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_module_mapping',
    sa.Column('umm_id', sa.Integer(), nullable=False),
    sa.Column('user_type', sa.Integer(), nullable=False),
    sa.Column('module_id', sa.Integer(), nullable=True),
    sa.Column('module_name', sa.String(length=50), nullable=True),
    sa.Column('is_archived', sa.String(length=1), nullable=False),
    sa.Column('last_modified_date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['module_id'], ['module_detail.module_id'], ),
    sa.ForeignKeyConstraint(['user_type'], ['message_detail.msg_id'], ),
    sa.PrimaryKeyConstraint('umm_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_module_mapping')
    # ### end Alembic commands ###
