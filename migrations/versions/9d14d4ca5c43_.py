"""empty message

Revision ID: 9d14d4ca5c43
Revises: 
Create Date: 2020-04-14 00:53:18.760158

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9d14d4ca5c43'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('teacher_payroll_detail',
    sa.Column('tpd_id', sa.Integer(), nullable=False),
    sa.Column('teacher_id', sa.Integer(), nullable=False),
    sa.Column('teacher_name', sa.String(length=100), nullable=False),
    sa.Column('total_salary', sa.Float(), nullable=False),
    sa.Column('month', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('days_in_month', sa.Integer(), nullable=False),
    sa.Column('days_present', sa.Integer(), nullable=False),
    sa.Column('calc_salary', sa.Float(), nullable=False),
    sa.Column('paid_status', sa.String(length=1), nullable=False),
    sa.Column('last_modified_date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['teacher_id'], ['teacher_profile.teacher_id'], ),
    sa.PrimaryKeyConstraint('tpd_id')
    )
    op.create_table('teacher_salary',
    sa.Column('teacher_salary_id', sa.Integer(), nullable=False),
    sa.Column('teacher_id', sa.Integer(), nullable=False),
    sa.Column('total_salary', sa.Float(), nullable=False),
    sa.Column('is_current', sa.String(length=1), nullable=False),
    sa.Column('salary_set_on', sa.DateTime(), nullable=False),
    sa.Column('last_modified_date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['teacher_id'], ['teacher_profile.teacher_id'], ),
    sa.PrimaryKeyConstraint('teacher_salary_id')
    )
    op.drop_table('board_class_subject_books')
    op.add_column('board_class_subject', sa.Column('board_det_id', sa.Integer(), nullable=True))
    op.drop_constraint('board_class_subject_school_id_fkey', 'board_class_subject', type_='foreignkey')
    op.create_foreign_key(None, 'board_class_subject', 'board_detail', ['board_det_id'], ['board_det_id'])
    op.drop_column('board_class_subject', 'school_id')
    op.drop_column('board_class_subject', 'is_archieve')
    op.add_column('teacher_profile', sa.Column('curr_salary', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('teacher_profile', 'curr_salary')
    op.add_column('board_class_subject', sa.Column('is_archieve', sa.VARCHAR(length=1), autoincrement=False, nullable=True))
    op.add_column('board_class_subject', sa.Column('school_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'board_class_subject', type_='foreignkey')
    op.create_foreign_key('board_class_subject_school_id_fkey', 'board_class_subject', 'school_profile', ['school_id'], ['school_id'])
    op.drop_column('board_class_subject', 'board_det_id')
    op.create_table('board_class_subject_books',
    sa.Column('bcsb_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('school_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('class_val', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('subject_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('book_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('is_archieve', sa.VARCHAR(length=1), autoincrement=False, nullable=True),
    sa.Column('last_modified_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['book_id'], ['book_details.book_id'], name='board_class_subject_books_book_id_fkey'),
    sa.ForeignKeyConstraint(['school_id'], ['school_profile.school_id'], name='board_class_subject_books_school_id_fkey'),
    sa.ForeignKeyConstraint(['subject_id'], ['message_detail.msg_id'], name='board_class_subject_books_subject_id_fkey'),
    sa.PrimaryKeyConstraint('bcsb_id', name='board_class_subject_books_pkey')
    )
    op.drop_table('teacher_salary')
    op.drop_table('teacher_payroll_detail')
    # ### end Alembic commands ###
