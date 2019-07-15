from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from time import time
import jwt
from flask import current_app as app
from search import add_to_index, remove_from_index, query_index


db=SQLAlchemy()

#from app import app

login_manager = LoginManager()
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    user_type= db.Column(db.ForeignKey('message_detail.msg_id'), nullable=True)
    user_avatar = db.Column(db.String(500), nullable=True)
   

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def get_reset_password_token(self,expires_in=600):
        return jwt.encode(
            {'reset_password':self.id,'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id=jwt.decode(token,app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class Post(SearchableMixin, db.Model):
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return '<Post {}>'.format(self.body)




class Survivor(db.Model):
    __tablename__ = "survivor_details"
    sur_id = db.Column(db.Integer, primary_key=True)
    sur_name = db.Column(db.String(120), nullable=True)
    sur_email = db.Column(db.String(120),nullable=True)
    sur_treatment_status = db.Column(db.String(120))
    sur_address = db.Column(db.String(500))
    sur_city = db.Column(db.Integer)
    sur_cnsl_prvdr = db.Column(db.String(2))
    sur_cnsl_require = db.Column(db.String(2))
    sur_phone = db.Column(db.Integer)
    sur_gender = db.Column(db.String(2))
    sur_age = db.Column(db.Integer)
    sur_newsletter = db.Column(db.String(2))

    def __init__(self, name, email, treat_stat="NA", address="NA", city=0000, cnsl_prvdr="NA", cnsl_require="NA", phone=0000, gender="NA", age=0, newsletter="NA"):
        self.sur_name=name
        self.sur_email=email
        self.sur_treatment_status = treat_stat
        self.sur_address = address
        self.sur_city=city
        self.sur_cnsl_prvdr=cnsl_prvdr
        self.sur_cnsl_require=cnsl_require
        self.sur_phone=phone
        self.sur_gender=gender
        self.sur_age=age
        self.sur_newsletter=newsletter


class ClassSection(db.Model):
    __tablename__ = "class_section"
    class_sec_id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    class_val=db.Column(db.Integer,nullable=True)
    section=db.Column(db.String(1),nullable=True)
    school_id=db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)    
    student_count= db.Column(db.Integer,nullable=True)
    class_teacher=db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=True)
    last_modified_date=db.Column(db.DateTime)


class Attendance(db.Model):
    __tablename__ = "attendance"
    attendance_id=db.Column(db.Integer,primary_key=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable= False)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=True)        
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'), nullable=True)        
    subject_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    attendance_date = db.Column(db.DateTime)
    is_present=db.Column(db.String(1), nullable=True)
    last_modified_date=db.Column(db.DateTime)    


class Topic(db.Model):
    __tablename__ = "topic_detail"
    #content_id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(100),nullable=True)
    class_val=db.Column(db.Integer,nullable=True)
    unit_num=db.Column(db.Integer, nullable=True)
    chapter_num = db.Column(db.Integer,nullable=True)
    chapter_name= db.Column(db.String(120), nullable=True)
    start_date= db.Column(db.DateTime, nullable=True)
    end_date= db.Column(db.DateTime, nullable=True)
    subject_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    board_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    book_id= db.Column(db.ForeignKey('book_details.book_id'), nullable=True)


class TopicTracker(db.Model):
    __tablename__ = "topic_tracker"    
    topic_track_id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=True)
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'), nullable=True)      
    topic_id = db.Column(db.ForeignKey('topic_detail.topic_id'))
    subject_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    #last_topic = db.Column(db.ForeignKey('topic_detail.topic_id'),nullable=True)
    is_covered = db.Column(db.String(1), nullable=True) # this will only contain Y or N values
    #cover_Date = db.Column(db.DateTime, nullable=True)
    next_topic = db.Column(db.ForeignKey('topic_detail.topic_id'),nullable=True)        
    last_modified_date=db.Column(db.DateTime)


class BookDetails(db.Model):
    __tablename__ = "book_details"
    book_id = db.Column(db.Integer, primary_key=True)
    class_val = db.Column(db.Integer,nullable=True)
    subject_id= db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    book_name= db.Column(db.String(120))
    book_link= db.Column(db.String(500))
    last_modified_date=db.Column(db.DateTime)

class QuestionDetails(db.Model):
    __tablename__ = "question_details"
    question_id = db.Column(db.Integer, primary_key=True)
    class_val=db.Column(db.Integer,nullable=True)
    subject_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    board_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    question_description=db.Column(db.String(500),nullable=True)
    #slideshow_id=db.Column(db.ForeignKey('slide_tracker.slideshow_id'),nullable=True)
    question_type=db.Column(db.String(120),nullable=True)
    reference_link=db.Column(db.String(120),nullable=True)
    topic_id = db.Column(db.ForeignKey('topic_detail.topic_id'), nullable=True)



class QuestionOptions(db.Model):
    __tablename__ = "question_options"
    option_id=db.Column(db.Integer, primary_key=True)
    option = db.Column(db.String(1), nullable = True)
    option_desc=db.Column(db.LargeBinary(length=None),nullable=True)
    option_desc=db.Column(db.String(500),nullable=True)
    option_type=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    question_id = db.Column(db.ForeignKey('question_details.question_id'), nullable=True)    
    is_correct=db.Column(db.String(1),nullable=True)
    weightage=db.Column(db.Integer)
    last_modified_date=db.Column(db.DateTime)

class testQuestions(db.Model):
    __tablename__ = "test_questions"
    tq_id = db.Column(db.Integer,primary_key=True)
    test_id = db.Column(db.ForeignKey('test_details.test_id'), nullable=True)
    question_id=db.Column(db.ForeignKey('question_details.question_id'),nullable=True)    
    last_modified_date=db.Column(db.DateTime)

class TestDetails(db.Model):
    __tablename__ = "test_details"
    test_id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    class_val = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)    
    test_type=db.Column(db.String(120),nullable=True)
    region_id=db.Column(db.ForeignKey('message_detail.msg_id'))    
    subject_id=db.Column(db.ForeignKey('message_detail.msg_id'))
    total_marks=db.Column(db.Integer)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=True)
    test_paper_link = db.Column(db.String(200), nullable=True)
    date_of_creation = db.Column(db.DateTime)
    date_of_test = db.Column(db.DateTime)
    year=db.Column(db.Integer)
    month=db.Column(db.String(3))
    last_modified_date=db.Column(db.DateTime)

class ResultUpload(db.Model):
    __tablename__ = "result_upload"
    res_upload_id=db.Column(db.Integer,primary_key=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=True)
    class_sec_id=db.Column(db.ForeignKey('class_section.class_sec_id'),nullable=True)
    subject_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    student_id=db.Column(db.ForeignKey('student_profile.student_id'),nullable=True)
    exam_date=db.Column(db.DateTime)
    is_present=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    reason=db.Column(db.String(120),nullable=True)
    test_type=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    marks_scored=db.Column(db.Integer)
    total_marks=db.Column(db.Integer)
    test_id=db.Column(db.ForeignKey('test_details.test_id'),nullable=True)
    version_number=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    uploaded_by = db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=True)
    last_modified_date=db.Column(db.DateTime)    

class MessageDetails(db.Model):
    __tablename__ = "message_detail"
    msg_id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(120), nullable=True)
    description = db.Column(db.String(500), nullable=True)


class ResponseCapture(db.Model):
    __tablename__ = "response_capture"
    response_id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=True)
    class_sec_id=db.Column(db.ForeignKey('class_section.class_sec_id'),nullable=True)
    student_id=db.Column(db.ForeignKey('student_profile.student_id'),nullable=True)
    subject_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    #slideshow_id=db.Column(db.ForeignKey('slide_tracker.slideshow_id'),nullable=True)
    question_id=db.Column(db.ForeignKey('question_details.question_id'),nullable=True)
    response_option=db.Column(db.String(1),nullable=True)
    is_correct=db.Column(db.String(1), nullable=True)
    resp_session_id = db.Column(db.String(20), nullable=True) #combination of date and subject and class_sec in integer form 
    teacher_id=db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=True)
    last_modified_date=db.Column(db.DateTime)

class Address(db.Model):
    __tablename__ = "address_detail"
    address_id = db.Column(db.Integer,primary_key=True)
    address_1 = db.Column(db.String(100), nullable=True)
    address_2 = db.Column(db.String(100), nullable=True)
    locality = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(30), nullable=True)
    state = db.Column(db.String(30), nullable=True)
    country = db.Column(db.String(20),nullable=True)
    pin = db.Column(db.String(10), nullable=True)


class StudentProfile(db.Model):
    __tablename__ = "student_profile"
    student_id=db.Column(db.Integer,primary_key=True)
    first_name = db.Column(db.String(50), nullable = True)
    last_name = db.Column(db.String(50), nullable=True)
    full_name=db.Column(db.String(200),nullable=True)
    school_id=db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    class_sec_id=db.Column(db.ForeignKey('class_section.class_sec_id'),nullable=True)
    gender=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    dob=db.Column(db.DateTime,nullable=True)
    email = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(12), nullable=True)
    address_id = db.Column(db.ForeignKey('address_detail.address_id'), nullable=True)
    registration_date=db.Column(db.DateTime,nullable=True)
    leaving_date=db.Column(db.DateTime,nullable=True)
    leaving_reason=db.Column(db.String(500), nullable=True)
    roll_number=db.Column(db.Integer,nullable=True)
    school_adm_number=db.Column(db.String(120),nullable=True)
    profile_picture= db.Column(db.String(500),nullable=True)
    last_modified_date=db.Column(db.DateTime,nullable=True)


class studentQROptions(db.Model):
    __tablename__="student_qr_options"
    student_qr_id = db.Column(db.Integer,primary_key=True)
    student_id = db.Column(db.ForeignKey('student_profile.student_id'), nullable=True)
    option = db.Column(db.String(1), nullable=True)
    qr_link = db.Column(db.String(200), nullable=True)

    

class GuardianProfile(db.Model):
    __tablename__="guardian_profile"
    guardian_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    relation = db.Column(db.ForeignKey('message_detail.msg_id'), nullable=True)
    email = db.Column(db.String(150), nullable= True)
    phone = db.Column(db.String(12), nullable=True)
    student_id = db.Column(db.ForeignKey('student_profile.student_id'), nullable=True)


class SchoolProfile(db.Model):
    __tablename__ = "school_profile"
    school_id = db.Column(db.Integer, primary_key=True)
    school_name=db.Column(db.String(500),nullable=True)
    registered_date=db.Column(db.DateTime,nullable=True)
    org_leaving_Date=db.Column(db.DateTime,nullable=True)
    org_leaving_reason=db.Column(db.String(500),nullable=True)    
    address_id = db.Column(db.ForeignKey('address_detail.address_id'), nullable=True)
    last_modified_date=db.Column(db.DateTime)

class TeacherProfile(db.Model):
    __tablename__ = "teacher_profile"
    teacher_id = db.Column(db.Integer, primary_key=True)
    teacher_name=db.Column(db.String(500),nullable=True)
    school_id=db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    designation=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    subject_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)    
    subject_name=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    class_sec_id=db.Column(db.ForeignKey('class_section.class_sec_id'),nullable=True)
    registration_date=db.Column(db.DateTime,nullable=True)
    school_leaving_date= db.Column(db.DateTime,nullable=True)
    school_leaving_reason = db.Column(db.String(500),nullable=True)
    profile_picture= db.Column(db.String(500),nullable=True)
    email=db.Column(db.String,nullable=True)
    phone = db.Column(db.String(12), nullable=True)
    address_id = db.Column(db.ForeignKey('address_detail.address_id'), nullable=True)
    user_id=db.Column(db.ForeignKey('user.id'), nullable=True)
    last_modified_date=db.Column(db.DateTime)


class FeeManagement(db.Model):
    __tablename__ = "school_fee_mgt"
    fee_trans_id=db.Column(db.Integer, primary_key=True)
    school_id=db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    student_id=db.Column(db.ForeignKey('student_profile.student_id'),nullable=True)
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'),nullable=True)
    payment_date = db.Column(db.DateTime,nullable=True)
    due_date = db.Column(db.DateTime,nullable=True)
    fee_amount = db.Column(db.Integer,nullable=True)
    fee_paid_amount = db.Column(db.Integer,nullable=True)
    is_paid = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    delay_reason = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    outstanding_amount = db.Column(db.Integer,nullable=True)
    last_modified_date = db.Column(db.DateTime,nullable=True)    



class PerformanceDetail(db.Model):
    __tablename__ = "performance_detail"
    perf_id= db.Column(db.Integer,primary_key=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'), nullable=True)
    test_type = db.Column(db.ForeignKey('message_detail.msg_id'), nullable=True)
    student_id = db.Column(db.ForeignKey('student_profile.student_id'),nullable=True)
    year = db.Column(db.Integer,nullable=True)
    semi_annual = db.Column(db.Integer,nullable=True)
    month = db.Column(db.Integer,nullable=True)
    date = db.Column(db.DateTime,nullable=True)
    school_avg_score = db.Column(db.Integer,nullable=True)
    class_avg_score = db.Column(db.Integer,nullable=True)
    section_avg_score = db.Column(db.Integer,nullable=True)
    student_score = db.Column(db.Integer,nullable=True)
    #school_year_rank = db.Column(db.Integer,nullable=True)
    #school_semi_annual_rank = db.Column(db.Integer,nullable=True)
    #school_month_rank = db.Column(db.Integer,nullable=True)
    #class_year_rank = db.Column(db.Integer,nullable=True)
    #section_year_rank = db.Column(db.Integer,nullable=True)
    #section_semi_annual_rank = db.Column(db.Integer,nullable=True)
    #student_year_rank = db.Column(db.Integer,nullable=True)
    #student_semi_annual_rank = db.Column(db.Integer,nullable=True)
    #student_month_rank = db.Column(db.Integer,nullable=True)
    last_modified_date = db.Column(db.DateTime,nullable=True)



class AlllearnSchoolPerf(db.Model):
    __tablename__ = "alllearn_school_perf"
    all_perf_id= db.Column(db.Integer,primary_key=True)
    avg_perf_alllearn = db.Column(db.Integer,nullable=True)
    quarter = db.Column(db.Integer,nullable=True)
    year =  db.Column(db.Integer,nullable=True)
    last_modified_date=db.Column(db.DateTime,nullable=True)


class EventDetail(db.Model):
    __tablename__ = "event_detail"
    event_id = db.Column(db.Integer,primary_key=True)
    event_name =  db.Column(db.String(120),nullable=True)
    event_duration =  db.Column(db.String(10),nullable=True)
    event_date =  db.Column(db.DateTime,nullable=True)
    event_start =  db.Column(db.DateTime,nullable=True)
    event_end = db.Column(db.DateTime,nullable=True)
    event_category = db.Column(db.String(20), nullable=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=True)
    last_modified_date=db.Column(db.DateTime,nullable=True)


class Calendar(db.Model):
    __tablename__ = "calendar"
    calendar_id=db.Column(db.Integer,primary_key=True)
    date = db.Column(db.DateTime,nullable=True)
    date_aging = db.Column(db.Integer,nullable=True)
    week = db.Column(db.Integer,nullable=True)
    week_aging = db.Column(db.Integer,nullable=True)
    month = db.Column(db.Integer,nullable=True)
    month_name = db.Column(db.Integer,nullable=True)
    month_aging = db.Column(db.Integer,nullable=True)
    semi_annual = db.Column(db.Integer,nullable=True)
    semi_annual_aging = db.Column(db.Integer,nullable=True)
    year = db.Column(db.Integer,nullable=True)
    year_aging = db.Column(db.Integer,nullable=True)
    last_modified_date=db.Column(db.DateTime,nullable=True)


class Recommendation(db.Model):
    __tablename__ = "recomm_detail"    
    recomm_id=db.Column(db.Integer,primary_key=True)
    subject = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    if_this = db.Column(db.String(500),nullable=True)
    then_this = db.Column(db.String(500), nullable=True)


class Search(db.Model):
    __tablename__ = "search"
    search_id=db.Column(db.Integer,primary_key=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    search_keywords = db.Column(db.String(100),nullable=True)
    search_date = db.Column(db.DateTime,nullable=True)
    is_error_page = db.Column(db.Integer,nullable=True)
    redirect_url = db.Column(db.String(500),nullable=True)
    last_modified_date = db.Column(db.DateTime,nullable=True)

class FinancialDetails(db.Model):
    __tablename__ = "financial_details"
    fin_det_id=db.Column(db.Integer,primary_key=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'),nullable=True)
    subscription_amt = db.Column(db.Integer,nullable=True)
    maint_cost = db.Column(db.Integer,nullable=True)
    year= db.Column(db.Integer,nullable=True)
    month= db.Column(db.Integer,nullable=True)