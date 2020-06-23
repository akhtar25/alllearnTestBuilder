"""empty message

Revision ID: 971143e523d1
Revises: 
Create Date: 2020-06-21 12:01:00.274357

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '971143e523d1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('teacher_subject_class',
    sa.Column('teacher_subj_id', sa.Integer(), nullable=False),
    sa.Column('school_id', sa.Integer(), nullable=True),
    sa.Column('subject_id', sa.Integer(), nullable=True),
    sa.Column('teacher_id', sa.Integer(), nullable=True),
    sa.Column('class_sec_id', sa.Integer(), nullable=True),
    sa.Column('is_archived', sa.String(length=1), nullable=True),
    sa.Column('last_modified_date', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['class_sec_id'], ['class_section.class_sec_id'], ),
    sa.ForeignKeyConstraint(['school_id'], ['school_profile.school_id'], ),
    sa.ForeignKeyConstraint(['subject_id'], ['message_detail.msg_id'], ),
    sa.ForeignKeyConstraint(['teacher_id'], ['teacher_profile.teacher_id'], ),
    sa.PrimaryKeyConstraint('teacher_subj_id')
    )
    op.drop_column('live_class', 'end_time')
    op.drop_column('live_class', 'start_time')
    op.alter_column('module_access', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('module_access', 'module_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('module_access', 'user_type',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('module_detail', 'description',
               existing_type=sa.VARCHAR(length=300),
               nullable=True)
    op.alter_column('module_detail', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('module_detail', 'module_name',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('module_detail', 'module_name',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    op.alter_column('module_detail', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('module_detail', 'description',
               existing_type=sa.VARCHAR(length=300),
               nullable=False)
    op.alter_column('module_access', 'user_type',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('module_access', 'module_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('module_access', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.add_column('live_class', sa.Column('start_time', sa.VARCHAR(length=30), autoincrement=False, nullable=False))
    op.add_column('live_class', sa.Column('end_time', sa.VARCHAR(length=30), autoincrement=False, nullable=False))
    op.drop_table('teacher_subject_class')
    # ### end Alembic commands ###
