"""empty message

Revision ID: 8051700f5986
Revises: 62349513a035
Create Date: 2020-08-14 23:05:22.601536

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8051700f5986'
down_revision = '62349513a035'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('course_detail_teacher_id_fkey', 'course_detail', type_='foreignkey')
    op.create_foreign_key(None, 'course_detail', 'teacher_profile', ['teacher_id'], ['teacher_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'course_detail', type_='foreignkey')
    op.create_foreign_key('course_detail_teacher_id_fkey', 'course_detail', 'message_detail', ['teacher_id'], ['msg_id'])
    # ### end Alembic commands ###
