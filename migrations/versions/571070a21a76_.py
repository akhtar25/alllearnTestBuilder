"""empty message

Revision ID: 571070a21a76
Revises: be8837e7b86a
Create Date: 2019-06-11 16:02:29.431442

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '571070a21a76'
down_revision = 'be8837e7b86a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('alllearn_school_perf', 'avg_perf_alllearn',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('alllearn_school_perf', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('alllearn_school_perf', 'quarter',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('alllearn_school_perf', 'year',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('attendance', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('attendance', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('attendance', 'teacher_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('book_details', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('book_details', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('calendar', 'date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('calendar', 'date_aging',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('calendar', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('calendar', 'month',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('calendar', 'month_aging',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('calendar', 'month_name',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('calendar', 'semi_annual',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('calendar', 'semi_annual_aging',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('calendar', 'week',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('calendar', 'week_aging',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('calendar', 'year',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('calendar', 'year_aging',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('class_section', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('class_section', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('class_section', 'section_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('class_section', 'student_count',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('content', 'board_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('content', 'chapter_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('content', 'chapter_name',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    op.alter_column('content', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('content', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('content', 'topic_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('content', 'topic_name',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    op.alter_column('content_tracker', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('content_tracker', 'is_completed',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('content_tracker', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('content_tracker', 'teacher_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('content_tracker', 'topic_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('event_detail', 'date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('event_detail', 'event_color',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('event_detail', 'event_duration_hours',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('event_detail', 'event_name',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    op.alter_column('event_detail', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('financial_details', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('financial_details', 'maint_cost',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('financial_details', 'month',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('financial_details', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('financial_details', 'subscription_amt',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('financial_details', 'year',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('message_detail', 'description',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('performance_detail', 'class_avg_score',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'class_year_rank',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('performance_detail', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('performance_detail', 'month',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'school_avg_score',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'school_month_rank',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'school_semi_annual_rank',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'school_year_rank',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'section_avg_score',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'section_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'section_semi_annual_rank',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'section_year_rank',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'semi_annual',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'student_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'student_month_rank',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'student_score',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'student_semi_annual_rank',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'student_year_rank',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('performance_detail', 'year',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('question_details', 'board_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('question_details', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('question_details', 'question_description',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('question_details', 'question_type',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    op.alter_column('question_details', 'slideshow_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('question_details', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('question_options', 'is_correct',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('question_options', 'option_desc',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('question_options', 'option_type',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('question_options', 'question_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('recomm_detail', 'if_this',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('recomm_detail', 'subject',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('recomm_detail', 'then_this',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('response_capture', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('response_capture', 'question_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('response_capture', 'response_option',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('response_capture', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('response_capture', 'slideshow_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('response_capture', 'student_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('response_capture', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('response_capture', 'teacher_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('result_upload', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('result_upload', 'is_present',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('result_upload', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('result_upload', 'student_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('result_upload', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('result_upload', 'test_type',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('result_upload', 'version_number',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('school_fee_mgt', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('school_fee_mgt', 'delay_reason',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('school_fee_mgt', 'due_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('school_fee_mgt', 'fee_amount',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('school_fee_mgt', 'fee_paid_amount',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('school_fee_mgt', 'is_paid',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('school_fee_mgt', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('school_fee_mgt', 'outstanding_amount',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('school_fee_mgt', 'payment_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('school_fee_mgt', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('school_fee_mgt', 'student_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('school_profile', 'city',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('school_profile', 'registered_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('school_profile', 'school_name',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('school_profile', 'state',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('search', 'is_error_page',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('search', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('search', 'redirect_url',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('search', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('search', 'search_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('search', 'search_keywords',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    op.alter_column('slide_tracker', 'chapter_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('slide_tracker', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('slide_tracker', 'topic_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('student_profile', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('student_profile', 'dob',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('student_profile', 'gender',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('student_profile', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('student_profile', 'student_name',
               existing_type=sa.VARCHAR(length=200),
               nullable=True)
    op.alter_column('survivor_details', 'sur_email',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    op.alter_column('survivor_details', 'sur_name',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    op.alter_column('teacher_profile', 'designation',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('teacher_profile', 'email',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('teacher_profile', 'phone',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('teacher_profile', 'profile_picture',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('teacher_profile', 'registration_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('teacher_profile', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('teacher_profile', 'school_leaving_reason',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('teacher_profile', 'teacher_name',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    op.alter_column('test_details', 'board_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('test_details', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('test_details', 'test_type',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    op.alter_column('test_questions', 'question_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('test_questions', 'test_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('test_questions', 'test_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('test_questions', 'question_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('test_details', 'test_type',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    op.alter_column('test_details', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('test_details', 'board_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('teacher_profile', 'teacher_name',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('teacher_profile', 'school_leaving_reason',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('teacher_profile', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('teacher_profile', 'registration_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('teacher_profile', 'profile_picture',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('teacher_profile', 'phone',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('teacher_profile', 'email',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('teacher_profile', 'designation',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('survivor_details', 'sur_name',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    op.alter_column('survivor_details', 'sur_email',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    op.alter_column('student_profile', 'student_name',
               existing_type=sa.VARCHAR(length=200),
               nullable=False)
    op.alter_column('student_profile', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('student_profile', 'gender',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('student_profile', 'dob',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('student_profile', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('slide_tracker', 'topic_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('slide_tracker', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('slide_tracker', 'chapter_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('search', 'search_keywords',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    op.alter_column('search', 'search_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('search', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('search', 'redirect_url',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('search', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('search', 'is_error_page',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('school_profile', 'state',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('school_profile', 'school_name',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('school_profile', 'registered_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('school_profile', 'city',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('school_fee_mgt', 'student_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('school_fee_mgt', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('school_fee_mgt', 'payment_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('school_fee_mgt', 'outstanding_amount',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('school_fee_mgt', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('school_fee_mgt', 'is_paid',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('school_fee_mgt', 'fee_paid_amount',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('school_fee_mgt', 'fee_amount',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('school_fee_mgt', 'due_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('school_fee_mgt', 'delay_reason',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('school_fee_mgt', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('result_upload', 'version_number',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('result_upload', 'test_type',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('result_upload', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('result_upload', 'student_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('result_upload', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('result_upload', 'is_present',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('result_upload', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('response_capture', 'teacher_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('response_capture', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('response_capture', 'student_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('response_capture', 'slideshow_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('response_capture', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('response_capture', 'response_option',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('response_capture', 'question_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('response_capture', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('recomm_detail', 'then_this',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('recomm_detail', 'subject',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('recomm_detail', 'if_this',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('question_options', 'question_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('question_options', 'option_type',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('question_options', 'option_desc',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('question_options', 'is_correct',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('question_details', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('question_details', 'slideshow_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('question_details', 'question_type',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    op.alter_column('question_details', 'question_description',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('question_details', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('question_details', 'board_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'year',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'student_year_rank',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'student_semi_annual_rank',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'student_score',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'student_month_rank',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'student_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'semi_annual',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'section_year_rank',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'section_semi_annual_rank',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'section_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'section_avg_score',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'school_year_rank',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'school_semi_annual_rank',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'school_month_rank',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'school_avg_score',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'month',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('performance_detail', 'date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('performance_detail', 'class_year_rank',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('performance_detail', 'class_avg_score',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('message_detail', 'description',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    op.alter_column('financial_details', 'year',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('financial_details', 'subscription_amt',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('financial_details', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('financial_details', 'month',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('financial_details', 'maint_cost',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('financial_details', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('event_detail', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('event_detail', 'event_name',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    op.alter_column('event_detail', 'event_duration_hours',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('event_detail', 'event_color',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('event_detail', 'date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('content_tracker', 'topic_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('content_tracker', 'teacher_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('content_tracker', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('content_tracker', 'is_completed',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('content_tracker', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('content', 'topic_name',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    op.alter_column('content', 'topic_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('content', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('content', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('content', 'chapter_name',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    op.alter_column('content', 'chapter_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('content', 'board_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('class_section', 'student_count',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('class_section', 'section_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('class_section', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('class_section', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('calendar', 'year_aging',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('calendar', 'year',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('calendar', 'week_aging',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('calendar', 'week',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('calendar', 'semi_annual_aging',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('calendar', 'semi_annual',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('calendar', 'month_name',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('calendar', 'month_aging',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('calendar', 'month',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('calendar', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('calendar', 'date_aging',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('calendar', 'date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('book_details', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('book_details', 'class_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('attendance', 'teacher_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('attendance', 'subject_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('attendance', 'class_sec_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('alllearn_school_perf', 'year',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('alllearn_school_perf', 'quarter',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('alllearn_school_perf', 'last_modified_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('alllearn_school_perf', 'avg_perf_alllearn',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
