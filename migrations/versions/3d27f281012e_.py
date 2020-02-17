"""empty message

Revision ID: 3d27f281012e
Revises: 7c7979833907
Create Date: 2020-02-17 17:54:18.401620

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d27f281012e'
down_revision = '7c7979833907'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('board_class', sa.Column('board_det_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'board_class', 'board_detail', ['board_det_id'], ['board_det_id'])
    op.add_column('board_class_subject', sa.Column('board_det_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'board_class_subject', 'board_detail', ['board_det_id'], ['board_det_id'])
    op.create_foreign_key(None, 'book_details', 'board_detail', ['board_det_id'], ['board_det_id'])
    op.add_column('chapter_detail', sa.Column('board_det_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'chapter_detail', 'board_detail', ['board_det_id'], ['board_det_id'])
    op.add_column('student_profile', sa.Column('sponsored_amount', sa.Integer(), nullable=True))
    op.add_column('student_profile', sa.Column('sponsored_on', sa.DateTime(), nullable=True))
    op.add_column('student_profile', sa.Column('sponsored_status', sa.String(length=1), nullable=True))
    op.add_column('student_profile', sa.Column('sponsored_till', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('student_profile', 'sponsored_till')
    op.drop_column('student_profile', 'sponsored_status')
    op.drop_column('student_profile', 'sponsored_on')
    op.drop_column('student_profile', 'sponsored_amount')
    op.drop_constraint(None, 'chapter_detail', type_='foreignkey')
    op.drop_column('chapter_detail', 'board_det_id')
    op.drop_constraint(None, 'book_details', type_='foreignkey')
    op.drop_constraint(None, 'board_class_subject', type_='foreignkey')
    op.drop_column('board_class_subject', 'board_det_id')
    op.drop_constraint(None, 'board_class', type_='foreignkey')
    op.drop_column('board_class', 'board_det_id')
    # ### end Alembic commands ###
