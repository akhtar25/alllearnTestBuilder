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
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    username = db.Column(db.String(120), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    user_type= db.Column(db.ForeignKey('message_detail.msg_id'), nullable=True)
    user_avatar = db.Column(db.String(500), nullable=True)
    access_status = db.Column(db.ForeignKey('message_detail.msg_id'), nullable=True) #when an access request is raised the status is updated here: Requested, Not Requested, Granted
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=True)
    phone = db.Column(db.String(12), nullable=True)
    address = db.Column(db.String(200),nullable=True)
    city = db.Column(db.String(100),nullable=True)
    state = db.Column(db.String(100),nullable=True)
    #the 4 cols below have been added to record applicant information for jobs
    education = db.Column(db.String(500), nullable=True)
    experience = db.Column(db.String(1000), nullable=True)
    resume = db.Column(db.String(200),nullable=True)
    willing_to_travel = db.Column(db.Boolean,nullable=True)
    intro_link = db.Column(db.String(200),nullable=True)
    last_modified_date=db.Column(db.DateTime)

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
    class_sec_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_val=db.Column(db.String(20),nullable=True)
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
    #class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'), nullable=True)        
    subject_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    attendance_date = db.Column(db.DateTime)
    is_present=db.Column(db.String(1), nullable=True)
    last_modified_date=db.Column(db.DateTime)    


class Topic(db.Model):
    __tablename__ = "topic_detail"
    #content_id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(100),nullable=True)
    class_val=db.Column(db.String(20),nullable=True)
    unit_num=db.Column(db.Integer, nullable=True)
    chapter_num = db.Column(db.Integer,nullable=True)
    chapter_name= db.Column(db.String(120), nullable=True)
    start_date= db.Column(db.DateTime, nullable=True)
    end_date= db.Column(db.DateTime, nullable=True)    
    subject_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    board_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    book_id= db.Column(db.ForeignKey('book_details.book_id'), nullable=True)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=True)


class BoardDetail(db.Model):
    __tablename__ = "board_detail"
    board_det_id = db.Column(db.Integer,primary_key=True)
    board_id = db.Column(db.ForeignKey('message_detail.msg_id'), nullable=True)
    board_name = db.Column(db.String(100),nullable=True)
    description = db.Column(db.String(200),nullable=True)
    country = db.Column(db.String(200),nullable=True)
    board_type = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    last_modified_date=db.Column(db.DateTime, nullable=True)

# New tables added for Syllabus Page to relate board - class - subject - chapter - topic
class BoardClass(db.Model):
    __tablename__ = "board_class"
    board_class_id = db.Column(db.Integer,primary_key=True)
    board_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    board_det_id = db.Column(db.ForeignKey('board_detail.board_det_id'),nullable=True)
    class_val = db.Column(db.String(20), nullable=True)
    last_modified_date=db.Column(db.DateTime, nullable=True)


class BoardClassSubject(db.Model):
    __tablename__ = "board_class_subject"
    bcs_id = db.Column(db.Integer,primary_key=True)
    board_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    class_val = db.Column(db.String(20), nullable=True)
    subject_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=True)
    is_archived = db.Column(db.String(1),nullable=True)
    last_modified_date=db.Column(db.DateTime, nullable=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable= False)
    is_archived = db.Column(db.String(1), nullable=True)

class BoardClassSubjectBooks(db.Model):
    __tablename__ = "board_class_subject_books"
    bcsb_id = db.Column(db.Integer,primary_key=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable= False)
    class_val = db.Column(db.String(20), nullable=True)
    subject_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    book_id = db.Column(db.ForeignKey('book_details.book_id'), nullable=True)
    is_archived = db.Column(db.String(1), nullable=True)
    last_modified_date = db.Column(db.DateTime, nullable=True)


class ChapterDetail(db.Model):
    __tablename__="chapter_detail"
    chapter_id = db.Column(db.Integer,primary_key=True)
    chapter_num = db.Column(db.Integer,nullable=True)
    chapter_name= db.Column(db.String(120), nullable=True)
    subject_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    board_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    board_det_id = db.Column(db.ForeignKey('board_detail.board_det_id'),nullable=True)
    bcs_id = db.Column(db.ForeignKey('board_class_subject.bcs_id'),nullable=True)
    book_name = db.Column(db.String(200), nullable=True)
    last_modified_date=db.Column(db.DateTime, nullable=True)

class StudentClassSecDetail(db.Model):
    __tablename__= "student_class_sec_detail"
    student_class_sec_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.ForeignKey('student_profile.student_id'), nullable=True)
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'), nullable=True)
    class_val = db.Column(db.String(20), nullable=True)
    section=db.Column(db.String(1), nullable=True)
    is_current = db.Column(db.String(1), nullable=True)
    last_modified_date=db.Column(db.DateTime)
    promotion_date = db.Column(db.DateTime, nullable=True)

class TopicTracker(db.Model):
    __tablename__ = "topic_tracker"    
    topic_track_id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=True)
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'), nullable=True)      
    topic_id = db.Column(db.ForeignKey('topic_detail.topic_id'))
    subject_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    chapter_id = db.Column(db.ForeignKey('chapter_detail.chapter_id'),nullable=True) # this new column relates to the chapter detail table
    #last_topic = db.Column(db.ForeignKey('topic_detail.topic_id'),nullable=True)
    is_covered = db.Column(db.String(1), nullable=True) # this will only contain Y or N values
    #cover_Date = db.Column(db.DateTime, nullable=True)
    #next_topic = db.Column(db.ForeignKey('topic_detail.topic_id'),nullable=True)        
    reteach_count = db.Column(db.Integer, nullable=True)
    target_covered_date = db.Column(db.DateTime,nullable=True)
    is_archived = db.Column(db.String(1),nullable=True)
    last_modified_date=db.Column(db.DateTime)


class BookDetails(db.Model):
    __tablename__ = "book_details"
    book_id = db.Column(db.Integer, primary_key=True)
    class_val = db.Column(db.String(20),nullable=True)
    subject_id= db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    book_name= db.Column(db.String(120))
    book_link= db.Column(db.String(500)) 
    board_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    board_det_id = db.Column(db.ForeignKey('board_detail.board_det_id'),nullable=True)
    book_level = db.Column(db.String(1),nullable=True)  #F=Full book ; C=Chapter Level Book
    last_modified_date=db.Column(db.DateTime)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=True)

#End of changes for Syllabus Page

class QuestionDetails(db.Model):
    __tablename__ = "question_details"
    question_id = db.Column(db.Integer, primary_key=True)
    class_val=db.Column(db.String(20),nullable=True)
    subject_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    board_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    question_description=db.Column(db.String(1000),nullable=True)
    #slideshow_id=db.Column(db.ForeignKey('slide_tracker.slideshow_id'),nullable=True)
    question_type=db.Column(db.String(120),nullable=True)
    reference_link=db.Column(db.String(120),nullable=True)
    suggested_weightage = db.Column(db.Integer,nullable=True)
    topic_id = db.Column(db.ForeignKey('topic_detail.topic_id'), nullable=True)
    archive_status = db.Column(db.String(1),nullable=True)



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

class TestQuestions(db.Model):
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
    class_val=db.Column(db.String(20),nullable=True)
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
    upload_id=db.Column(db.String(120),nullable=True)
    version_number=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    uploaded_by = db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=True)
    question_paper_ref = db.Column(db.String(300), nullable=True)
    answer_sheet_ref = db.Column(db.String(300), nullable=True)
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
    #new cols added for online test upgrade    
    marks_scored = db.Column(db.Integer, nullable=True)
    answer_status = db.Column(db.Integer, nullable=True)
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


class JobDetail(db.Model):
    __tablename__ = "job_detail"
    job_id = db.Column(db.Integer,primary_key=True)
    category = db.Column(db.String(100),nullable=True)
    posted_by = db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=True)
    posted_on = db.Column(db.DateTime, nullable=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    description = db.Column(db.String(500), nullable=True)
    min_pay = db.Column(db.Integer,nullable=True)
    max_pay = db.Column(db.Integer,nullable=True)
    start_date = db.Column(db.DateTime,nullable=True)
    end_date = db.Column(db.DateTime,nullable=True)
    subject = db.Column(db.String(100),nullable=True)
    classes = db.Column(db.String(10),nullable=True)
    recomm_letter = db.Column(db.Integer, nullable=True) # 1 for true; 0 for false
    language = db.Column(db.String(100), nullable=True)
    timings = db.Column(db.String(100),nullable=True)
    stay = db.Column(db.String(100),nullable=True)
    fooding = db.Column(db.String(100),nullable=True)
    term  = db.Column(db.String(100),nullable=True)
    status  = db.Column(db.String(100),nullable=True)
    num_of_openings = db.Column(db.Integer,nullable=True)
    job_type = db.Column(db.String(50), nullable=True) # part time or full time 
    benefits = db.Column(db.String(200),nullable=True)
    city = db.Column(db.String(50),nullable=True)
    #school_admin_email = db.Column(db.String(100),nullable=True)
    last_modified_date=db.Column(db.DateTime,nullable=True)



class JobApplication(db.Model):
    __tablename__="job_application"
    app_id = db.Column(db.Integer,primary_key=True)
    job_id=db.Column(db.ForeignKey('job_detail.job_id'),nullable=True)
    applier_user_id = db.Column(db.ForeignKey('user.id'),nullable=True)
    applied_on =db.Column(db.DateTime,nullable=True)
    status = db.Column(db.String(100), nullable=True) #accepted - 1 or rejected - 2
    school_id = db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    available_from = db.Column(db.DateTime,nullable=True)
    available_till =db.Column(db.DateTime,nullable=True)
    #applicant_email = db.Column(db.String(100),nullable=True)
    last_modified_date=db.Column(db.DateTime,nullable=True)


#should create training table
# should create teacher - training table to related which teacher has completed what trainings
# should create pages to test teachers on trainings

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
    student_unique_id = db.Column(db.String(50),nullable=True) #added to identify each student since if a student is promoted new row will have to be inserted thereby changing the student_id
    user_id=db.Column(db.ForeignKey('user.id'), nullable=True)
    sponsor_id = db.Column(db.Integer, nullable=True)
    sponsor_name = db.Column(db.String(100), nullable=True)
    sponsored_status = db.Column(db.String(1), nullable=True)
    sponsored_amount = db.Column(db.Integer, nullable=True)
    sponsored_on = db.Column(db.DateTime, nullable=True)
    sponsored_till = db.Column(db.DateTime, nullable=True)
    points = db.Column(db.Integer,nullable=True)    #points section added for public test page
    is_archived= db.Column(db.String(1), nullable=True)
    last_modified_date=db.Column(db.DateTime,nullable=True)


class StudentRemarks(db.Model):
    __tablename__ = "student_remarks"
    remark_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.ForeignKey('student_profile.student_id'),nullable=False)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=False)
    remark_desc = db.Column(db.String(200), nullable=False)
    remark_type = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    is_archived = db.Column(db.String(1),nullable=False)
    last_modified_date = db.Column(db.DateTime,nullable=False)

class studentQROptions(db.Model):
    __tablename__="student_qr_options"
    student_qr_id = db.Column(db.Integer,primary_key=True)
    student_id = db.Column(db.ForeignKey('student_profile.student_id'), nullable=True)
    option = db.Column(db.String(1), nullable=True)
    qr_link = db.Column(db.String(200), nullable=True)

class CommunicationDetail(db.Model):
    __tablename__="communication_detail"
    comm_id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(1000), nullable=False)
    status = db.Column(db.ForeignKey('message_detail.msg_id'), nullable=False)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=False)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=False)
    last_modified_date = db.Column(db.DateTime,nullable=False)    


class CommunicationTransaction(db.Model):
    __tablename__="communication_transaction"
    comm_tran_id = db.Column(db.Integer, primary_key=True)
    comm_id = db.Column(db.ForeignKey('communication_detail.comm_id'), nullable=False)
    student_id = db.Column(db.ForeignKey('student_profile.student_id'), nullable=False)
    last_modified_date = db.Column(db.DateTime,nullable=False)    

# Tables for HomeWork Module
class HomeWorkDetail(db.Model):
    __tablename__ = "homework_detail"
    homework_id = db.Column(db.Integer, primary_key=True)
    homework_name = db.Column(db.String(200), nullable=False)
    class_sec_id=db.Column(db.ForeignKey('class_section.class_sec_id'),nullable=True)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=False)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'),nullable=False)
    question_count = db.Column(db.Integer, nullable=False)
    attachment = db.Column(db.String(200),nullable=True)
    is_archived = db.Column(db.String(1),nullable=False)
    last_modified_date = db.Column(db.DateTime,nullable=False)

class HomeWorkQuestions(db.Model):
    __tablename__="homework_questions"
    sq_id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.ForeignKey('homework_detail.homework_id'),nullable=False)
    question = db.Column(db.String(200), nullable=False)
    ref_url = db.Column(db.String(200),nullable=True)
    ref_type = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    is_archived = db.Column(db.String(1),nullable=False)
    last_modified_date = db.Column(db.DateTime,nullable=False)

class StudentHomeWorkResponse(db.Model):
    __tablename__ = "student_homework_response"
    homework_response_id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.ForeignKey('homework_detail.homework_id'),nullable=False)
    student_id = db.Column(db.ForeignKey('student_profile.student_id'),nullable=False)
    sq_id = db.Column(db.ForeignKey('homework_questions.sq_id'), nullable=False)
    answer = db.Column(db.String(200), nullable=True)
    teacher_remark  = db.Column(db.String(100), nullable=True)
    #is_archived = db.Column(db.String(1), nullable=True)
    last_modified_date = db.Column(db.DateTime,nullable=False)

# End


class SurveyDetail(db.Model):
    __tablename__ = "survey_detail"
    survey_id = db.Column(db.Integer, primary_key=True)
    survey_name = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=False)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'),nullable=False)
    question_count = db.Column(db.Integer, nullable=False)
    is_archived = db.Column(db.String(1),nullable=False)
    last_modified_date = db.Column(db.DateTime,nullable=False)

class SurveyQuestions(db.Model):
    __tablename__="survey_questions"
    sq_id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.ForeignKey('survey_detail.survey_id'),nullable=False)
    question = db.Column(db.String(200), nullable=False)
    is_archived = db.Column(db.String(1),nullable=False)
    last_modified_date = db.Column(db.DateTime,nullable=False)

class StudentSurveyResponse(db.Model):
    __tablename__ = "student_survey_response"
    survey_response_id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.ForeignKey('survey_detail.survey_id'),nullable=False)
    student_id = db.Column(db.ForeignKey('student_profile.student_id'),nullable=False)
    sq_id = db.Column(db.ForeignKey('survey_questions.sq_id'), nullable=False)
    answer = db.Column(db.String(200), nullable=True)
    last_modified_date = db.Column(db.DateTime,nullable=False)


class GuardianProfile(db.Model):
    __tablename__="guardian_profile"
    guardian_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    relation = db.Column(db.ForeignKey('message_detail.msg_id'), nullable=True)
    email = db.Column(db.String(150), nullable= True)
    phone = db.Column(db.String(12), nullable=True)
    user_id=db.Column(db.ForeignKey('user.id'), nullable=True)
    student_id = db.Column(db.ForeignKey('student_profile.student_id'), nullable=True)


class SchoolProfile(db.Model):
    __tablename__ = "school_profile"
    school_id = db.Column(db.Integer, primary_key=True)
    board_id=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    school_name=db.Column(db.String(500),nullable=True)
    registered_date=db.Column(db.DateTime,nullable=True)
    org_leaving_Date=db.Column(db.DateTime,nullable=True)
    org_leaving_reason=db.Column(db.String(500),nullable=True)    
    address_id = db.Column(db.ForeignKey('address_detail.address_id'), nullable=True)
    school_picture = db.Column(db.String(500), nullable=True)
    school_logo = db.Column(db.String(500), nullable=True)
    school_admin = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=True)
    sub_id =  db.Column(db.ForeignKey('subscription_detail.sub_id'), nullable=True)
    next_bill_due = db.Column(db.DateTime, nullable=True)
    how_to_reach = db.Column(db.String(500),nullable=True)
    school_type = db.Column(db.String(50),nullable=True) #ngo, budget, elite, government
    location_type = db.Column(db.String(50),nullable=True) # urban  , remote
    #camp_id =  db.Column(db.ForeignKey('campaign_detail.camp_id'), nullable=True)  We will have to uncheck it later
    impact_school_id = db.Column(db.Integer, nullable=True)
    school_session_start = db.Column(db.DateTime, nullable=True) #The date school starts every year
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
    #adding as a part of payroll setup
    curr_salary = db.Column(db.Integer, nullable=True)
    #end of payroll related row
    last_modified_date=db.Column(db.DateTime)
    device_preference = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)

#New tables to manage payroll
class TeacherSalary(db.Model):
    __tablename__="teacher_salary"
    teacher_salary_id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=False)
    total_salary = db.Column(db.Float, nullable=False)
    is_current = db.Column(db.String(1), nullable=False)
    salary_set_on = db.Column(db.DateTime, nullable=False)
    last_modified_date = db.Column(db.DateTime, nullable=False)

class TeacherPayrollDetail(db.Model):
    __tablename__="teacher_payroll_detail"
    tpd_id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=False)
    #teacher_name = db.Column(db.String(100), nullable=False)
    total_salary = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    days_in_month = db.Column(db.Integer, nullable = False)
    days_present = db.Column(db.Integer, nullable=False)
    calc_salary = db.Column(db.Float, nullable=False)
    paid_status = db.Column(db.String(1),nullable=False)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=True)
    last_modified_date = db.Column(db.DateTime, nullable=False)

#end of teacher payroll tables


class FeeDetail(db.Model):
    __tablename__ = "fee_detail"
    fee_trans_id=db.Column(db.Integer, primary_key=True)
    school_id=db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    student_id=db.Column(db.ForeignKey('student_profile.student_id'),nullable=True)
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'),nullable=True)
    payment_date = db.Column(db.DateTime,nullable=True)
    due_date = db.Column(db.DateTime,nullable=True)
    fee_amount = db.Column(db.Float,nullable=True)
    fee_paid_amount = db.Column(db.Float,nullable=True)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    paid_status = db.Column(db.String(1),nullable=False)
    delay_reason = db.Column(db.String(100),nullable=True)
    outstanding_amount = db.Column(db.Float,nullable=True)
    last_modified_date = db.Column(db.DateTime,nullable=True)    

class FeeClassSecDetail(db.Model):
    _tablename_ = "fee_class_sec_detail"
    fcs_id = db.Column(db.Integer, primary_key=True)
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'), nullable=True)
    class_val = db.Column(db.String(20), nullable=True)
    section=db.Column(db.String(1), nullable=True)
    is_current = db.Column(db.String(1), nullable=True)
    last_modified_date=db.Column(db.DateTime)
    change_date = db.Column(db.DateTime, nullable=True)
    amount = db.Column(db.Float,nullable=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=True)

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
    subject_id = db.Column(db.ForeignKey('message_detail.msg_id'), nullable=True)
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

class SubscriptionDetail(db.Model):
    __tablename__ = "subscription_detail"
    sub_id=db.Column(db.Integer,primary_key=True)
    sub_name = db.Column(db.String(100),nullable=True)  # plan for different durations (annual, quarter etc) should also be created separately
    sub_desc = db.Column(db.String(500), nullable=True)
    sub_duration_months = db.Column(db.Integer, nullable=True)
    group_name = db.Column(db.String(100), nullable=True)
    monthly_charge = db.Column(db.Integer,nullable=True)    
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    school_type = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)  #NGO, Budget, Lower Elite, Upper Elite, Government    
    student_limit = db.Column(db.Integer, nullable=True)
    teacher_limit = db.Column(db.Integer, nullable=True)
    test_limit = db.Column(db.Integer, nullable=True)
    archive_status = db.Column(db.String(1), nullable=True)
    last_modified_date = db.Column(db.DateTime,nullable=True)


class CampaignDetail(db.Model):
    __tablename__ = "campaign_detail"
    camp_id = db.Column(db.Integer,primary_key=True)
    camp_name = db.Column(db.String(100), primary_key=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    discount_percent = db.Column(db.Integer, nullable=True)
    archive_status = db.Column(db.String(1), nullable=True)
    last_modified_date = db.Column(db.DateTime,nullable=True)


class InvoiceDetail(db.Model):
    __tablename__="invoice_detail"
    invoice_id = db.Column(db.Integer,primary_key=True)
    school_id= db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    sent_to = db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=True)
    sent_email = db.Column(db.String(200), nullable=True)
    billing_date = db.Column(db.DateTime,nullable=True)
    payment_date = db.Column(db.DateTime,nullable=True)
    due_date =  db.Column(db.DateTime,nullable=True)
    subcription_charge = db.Column(db.Integer,nullable=True)
    tax = db.Column(db.Integer,nullable=True)
    invoice_total =db.Column(db.Integer,nullable=True)
    invoice_status = db.Column(db.String(1),nullable=True)     # Paid (P)    Unpaid (U)     Late (L)
    pay_id = db.Column(db.ForeignKey('payment_detail.pay_id'),nullable=True)
    last_modified_date = db.Column(db.DateTime,nullable=True)


class PaymentDetail(db.Model):
    __tablename__="payment_detail"
    pay_id = db.Column(db.Integer,primary_key=True)
    pay_type =  db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    account_card_num = db.Column(db.String(50), nullable=True)
    expiry_date = db.Column(db.Integer,nullable=True)
    ifsc_code = db.Column(db.String(20),nullable=True)
    ac_holder_name = db.Column(db.String(100), nullable=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    school_admin = db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=True)
    archive_status = db.Column(db.String(1),nullable=True)
    last_modified_date = db.Column(db.DateTime,nullable=True)


class SessionDetail(db.Model):
    __tablename__="session_detail"
    session_id = db.Column(db.Integer,primary_key=True)
    resp_session_id = db.Column(db.String(20), nullable=True) #combination of date and subject and class_sec in integer form 
    session_status = db.Column(db.Integer,nullable=True)   # open, in_progress, closed
    teacher_id=db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=True)
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'),nullable=True)
    test_id = db.Column(db.ForeignKey('test_details.test_id'),nullable=True) # this will only have a value when test has been configured before taking the feedback
    current_question = db.Column(db.ForeignKey('question_details.question_id'),nullable=True)
    load_new_question=db.Column(db.String(1),nullable=True) #tells if a new question has to be loaded on the pc screen when using pc+ mobile combination
    #new columns added for online test upgrade
    test_time = db.Column(db.Integer, nullable=True)
    total_marks = db.Column(db.Integer, nullable=True)
    correct_marks = db.Column(db.Integer, nullable = True)
    incorrect_marks = db.Column(db.Integer, nullable=True)
    last_modified_date = db.Column(db.DateTime,nullable=True)

class RespSessionQuestion(db.Model):
    __tablename__="resp_session_question"
    resp_quest_id = db.Column(db.Integer,primary_key=True)
    topic_id=db.Column(db.ForeignKey('topic_detail.topic_id'),nullable=True)
    question_id=db.Column(db.ForeignKey('question_details.question_id'),nullable=True)
    question_status = db.Column(db.Integer,nullable=True)  #answered_full, skipped, answered_part
    resp_session_id = db.Column(db.String(20), nullable=True) #combination of date and subject and class_sec in integer form 


class ContentDetail(db.Model):
    __tablename__="content_detail"
    content_id = db.Column(db.Integer,primary_key=True)
    content_name = db.Column(db.String(200), nullable=True)
    reference_link = db.Column(db.String(300),nullable=True)
    topic_id=db.Column(db.ForeignKey('topic_detail.topic_id'), nullable=True)    
    archive_status = db.Column(db.String(1),nullable=True)
    uploaded_by = db.Column(db.ForeignKey('teacher_profile.teacher_id'),nullable=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'),nullable=True)
    class_val=db.Column(db.String(20),nullable=True)
    subject_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    is_private = db.Column(db.String(1),nullable=True)
    content_type=db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    last_modified_date=db.Column(db.DateTime)
    
class ModuleDetail(db.Model):
    __tablename__="module_detail"
    module_id = db.Column(db.Integer,primary_key=True)
    module_name=db.Column(db.String(100),nullable=True)
    description = db.Column(db.String(300),nullable=True)
    module_type = db.Column(db.String(50),nullable=True)
    module_url = db.Column(db.String(200),nullable=True)
    title_val = db.Column(db.String(100), nullable=True)
    meta_val = db.Column(db.String(200), nullable=True)
    is_archived = db.Column(db.String(1),nullable=False)
    last_modified_date=db.Column(db.DateTime)


class ModuleAccess(db.Model):
    __tablename__="module_access"
    access_id =  db.Column(db.Integer,primary_key=True)
    user_type = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    module_id = db.Column(db.ForeignKey('module_detail.module_id'),nullable=True)
    module_name = db.Column(db.String(50), nullable=True)
    is_archived = db.Column(db.String(1),nullable=False)
    last_modified_date=db.Column(db.DateTime)

class TagDetail(db.Model):
    __tablename__="tag_detail"
    tag_id =  db.Column(db.Integer,primary_key=True)
    tag_name = db.Column(db.String(200),nullable=True)
    description=db.Column(db.String(200),nullable=True)
    tag_type = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    archive_status = db.Column(db.String(1),nullable=True)
    last_modified_date=db.Column(db.DateTime)

class ScheduleDetail(db.Model):
    __tablename__ = "schedule_detail"
    slot_id = db.Column(db.Integer, primary_key=True)
    slot_no = db.Column(db.Integer, nullable=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=True)
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'), nullable=True) 
    days_name= db.Column(db.String(20))
    subject_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=True)
    is_archived = db.Column(db.String(1), nullable=True)
    last_modified_date=db.Column(db.DateTime)

class TeacherSubjectClass(db.Model):
    __tablename__ = "teacher_subject_class"
    teacher_subj_id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable=True)
    subject_id = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=True)
    class_sec_id = db.Column(db.ForeignKey('class_section.class_sec_id'), nullable=True)
    is_archived = db.Column(db.String(1),nullable=True)
    last_modified_date=db.Column(db.DateTime)

class StudentTag(db.Model):
    __tablename__="student_tag"
    stud_tag_id =  db.Column(db.Integer,primary_key=True)
    student_id = db.Column(db.ForeignKey('student_profile.student_id'),nullable=True)
    tag_id =  db.Column(db.ForeignKey('tag_detail.tag_id'),nullable=True)
    archive_status = db.Column(db.String(1),nullable=True)
    last_modified_date=db.Column(db.DateTime)


#class InventoryDetail(db.Model):
#    __tablename__ = "inventory_detail"
#    inv_id = db.Column(db.Integer, primary_key=True)
#    inv_name = db.Column(db.String(200), nullable=False)
#    inv_description = db.Column(db.String(500), nullable=False) 
#    inv_category = db.Column(db.ForeignKey('message_detail.msg_id'), nullable=False)
#    total_stock = db.Column(db.Float, nullable=False)
#    stock_out = db.Column(db.Float, nullable=False)
#    item_rate = db.Column(db.Float, nullable=False)
#    total_cost = db.Column(db.Float, nullable=False)
#    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=True)
#    school_id = db.Column(db.ForeignKey('school_profile.school_id'),nullable=False)
#    is_archived = db.Column(db.String(1),nullable=True)    
#    last_modified_date=db.Column(db.DateTime, nullable=False)
#
#
#class InventoryAllocationStudent(db.Model):
#    __tablename__ = "inventory_allocation_stud"
#    alloc_id = db.Column(db.Integer, primary_key=True)
#    inv_id = db.Column(db.ForeignKey('inventory_detail.inv_id'), nullable=False)
#    student_id = db.Column(db.ForeignKey('student_profile.student_id'), nullable=False)
#    count = db.Column(db.Float, nullable=False)
#    allocation_type = db.Column(db.String(1), nullable=True) # P =Permanent; T=Temporary
#    allocation_status = db.Column(db.ForeignKey('message_detail.msg_id'), nullable=False)
#    is_archived = db.Column(db.String(1),nullable=True)    
#    last_modified_date=db.Column(db.DateTime, nullable=False)


class LiveClass(db.Model):
    __tablename__='live_class'
    live_class_id = db.Column(db.Integer, primary_key=True)
    class_sec_id= db.Column(db.ForeignKey('class_section.class_sec_id'), nullable=False)
    subject_id = db.Column(db.ForeignKey('message_detail.msg_id'), nullable=False)
    #chapter_num = db.Column(db.Integer, nullable=True)
    topic_id = db.Column(db.ForeignKey('topic_detail.topic_id'),nullable=True)    
    start_time = db.Column(db.DateTime, nullable = True)
    end_time = db.Column(db.DateTime, nullable = True)
    status = db.Column(db.String(10), nullable = False) # Upcoming; Over; Ongoing
    teacher_id = db.Column(db.ForeignKey('teacher_profile.teacher_id'), nullable=False)
    teacher_name = db.Column(db.String(100), nullable=True)
    conf_link = db.Column(db.String(200), nullable=True)
    #phone_number = db.Column(db.String(30), nullable=True)
    school_id = db.Column(db.ForeignKey('school_profile.school_id'), nullable= True)    
    #school_name = db.Column(db.String(100), nullable=True)
    is_archived = db.Column(db.String(1),nullable=False)
    last_modified_date = db.Column(db.DateTime, nullable=False)



#class ModuleDetail(db.Model):
#    __tablename__ = "module_mapping"
#    module_id = db.Column(db.Integer, primary_key=True)
#    module_name = db.Column(db.String(50), nullable=False)
#    module_type = db.Column(db.ForeignKey('message_detail.msg_id'),nullable=True)
#    module_url = db.Column(db.String(200),nullable=True)
#    is_archived = db.Column(db.String(1),nullable=False)
#    last_modified_date = db.Column(db.DateTime, nullable=False)
#
#
#class UserModuleMapping(db.Model):
#    __tablename__ ="user_module_mapping"
#    umm_id = db.Column(db.Integer, primary_key=True)
#    user_type = db.Column(db.ForeignKey('message_detail.msg_id'), nullable=False)
#    module_id = db.Column(db.ForeignKey('module_detail.module_id'), nullable=True)
#    module_name = db.Column(db.String(50), nullable=True)
#    is_archived = db.Column(db.String(1),nullable=False)
#    last_modified_date = db.Column(db.DateTime, nullable=False)