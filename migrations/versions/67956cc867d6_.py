"""empty message

Revision ID: 67956cc867d6
Revises: 072366d2539a
Create Date: 2020-04-16 16:00:27.176475

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67956cc867d6'
down_revision = '072366d2539a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('survey_questions',
    sa.Column('sq_id', sa.Integer(), nullable=False),
    sa.Column('survey_id', sa.Integer(), nullable=False),
    sa.Column('question', sa.String(length=200), nullable=False),
    sa.Column('is_archived', sa.String(length=1), nullable=False),
    sa.Column('last_modified_date', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['survey_id'], ['survey_detail.survey_id'], ),
    sa.PrimaryKeyConstraint('sq_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('survey_questions')
    # ### end Alembic commands ###
