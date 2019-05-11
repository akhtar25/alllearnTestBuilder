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
    sur_name = db.Column(db.String(120), nullable=False)
    sur_email = db.Column(db.String(120),nullable=False)
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

class Member(db.Model):
    __tablename__ = "member_details"
    mem_id = db.Column(db.Integer, primary_key=True)
    mem_name = db.Column(db.String(120), nullable=False)
    mem_location = db.Column(db.String(120))
    mem_dept = db.Column(db.String(120))
    mem_age = db.Column(db.Integer)
    mem_type = db.Column(db.String(2))
    mem_join_dt = db.Column(db.DateTime)
    mem_end_dt= db.Column(db.DateTime)
    mem_gender = db.Column(db.String(2))
    mem_hour_day = db.Column(db.Integer)
    mem_city = db.Column(db.String(120))
    mem_branch_id = db.Column(db.Integer)


class Hospital(db.Model):
    __tablename__ = "hospital_details"
    hosp_id = db.Column(db.Integer, primary_key=True)
    hosp_name = db.Column(db.String(120), nullable=False)
    hosp_location = db.Column(db.String(120))
    hosp_phone = db.Column(db.Integer)
    hosp_city = db.Column(db.String(120))


class Medicines(db.Model):
    __tablename__ = "medicine_details"
    med_id = db.Column(db.Integer, primary_key=True)
    med_name = db.Column(db.String(120), nullable=False)
    med_dosage = db.Column(db.String(120), nullable=False)
    med_cost_id = db.Column(db.Integer)
    med_in_stock = db.Column(db.Integer)
    med_maker = db.Column(db.String(120))
    med_cancer_type = db.Column(db.String(120))


class Articles(db.Model):
    __tablename__ = "articles_details"
    art_id = db.Column(db.Integer, primary_key=True)
    art_name = db.Column(db.String(120), nullable=False)
    art_content = db.Column(db.String(500))
    art_read_count= db.Column(db.Integer)
    art_author = db.Column(db.String(120))
    art_date = db.Column(db.DateTime)


class Doctor(db.Model):
    __tablename__ = "doctor_details"
    doc_id = db.Column(db.Integer, primary_key=True)
    doc_name = db.Column(db.String(120), nullable=False)
    doc_hosp_id = db.Column(db.ForeignKey('hospital_details.hosp_id'), nullable=True)
    doc_experience = db.Column(db.Integer)
    doc_city = db.Column(db.String(120))
    doc_phone = db.Column(db.Integer)
    doc_cnsl_prvdr = db.Column(db.String(2))


class Author(db.Model):
    __tablename__ = "author_details"
    auth_id = db.Column(db.Integer, primary_key=True)
    auth_type = db.Column(db.String(120), nullable=False)
    auth_art_count = db.Column(db.Integer, nullable=True)
    art_indiv_id = db.Column(db.Integer)


class Cost(db.Model):
    __tablename__ = "cost_details"
    cost_id = db.Column(db.Integer, primary_key=True)
    cost_item = db.Column(db.String(120), nullable=False)
    cost_unit_price = db.Column(db.Integer, nullable=False)
    cost_center= db.Column(db.String(100), nullable=False)

class Stay(db.Model):
    __tablename__ = "stay_details"
    stay_id = db.Column(db.Integer, primary_key=True)
    stay_name = db.Column(db.String(120), nullable=False)
    stay_location = db.Column(db.String(500), nullable=False)
    stay_city = db.Column(db.String(100), nullable=False)
    stay_total_room_count = db.Column(db.Integer, nullable=False)
    stay_avlbl_room_count = db.Column(db.Integer, nullable=False)
    stay_bed_count = db.Column(db.Integer, nullable=False)
    stay_cost_id = db.Column(db.ForeignKey('cost_details.cost_id'), nullable=True)


class Booking(db.Model):
    __tablename__ = "booking_details"
    book_id = db.Column(db.Integer, primary_key=True)
    book_stay_id = db.Column(db.ForeignKey('stay_details.stay_id'), nullable=True)
    book_day_count = db.Column(db.Integer, nullable=False)
    book_start_date = db.Column(db.DateTime, nullable=False)
    book_end_date = db.Column(db.DateTime, nullable=False)
    book_total_cost = db.Column(db.Integer, nullable=False)
    book_refund_cost = db.Column(db.Integer, nullable=False)
    book_sur_id = db.Column(db.ForeignKey('survivor_details.sur_id'), nullable=True)


class Support_Meeting(db.Model):
    __tablename__ = "support_meeting_details"
    meet_id = db.Column(db.Integer, primary_key=True)
    meet_name = db.Column(db.String(120), nullable=True)
    meet_city = db.Column(db.Integer, nullable=False)
    meet_address = db.Column(db.String(500), nullable=False)
    meet_start_date = db.Column(db.DateTime, nullable=False)
    meet_end_date = db.Column(db.DateTime, nullable=False)
    meet_cost_id = db.Column(db.ForeignKey('cost_details.cost_id'), nullable=True)
    meet_start_time = db.Column(db.DateTime, nullable=False)
    meet_end_time = db.Column(db.DateTime, nullable=False)
    meet_food = db.Column(db.String, nullable=False)
    meet_doc_id = db.Column(db.ForeignKey('doctor_details.doc_id'), nullable=False)
    meet_coord_id = db.Column(db.ForeignKey('member_details.mem_id'), nullable=False)


class Message_Table(db.Model):
    __tablename__ = "message_details"
    msg_id = db.Column(db.Integer, primary_key=True)
    msg_type = db.Column(db.String(120), nullable=True)
    msg_description = db.Column(db.String(500), nullable=False)


class Counselling(db.Model):
    __tablename__ = "counselling_details"
    cnsl_id = db.Column(db.Integer, primary_key=True)
    cnsl_cnslr_id = db.Column(db.Integer, nullable=True)
    cnsl_sur_id =db.Column(db.ForeignKey('survivor_details.sur_id'), nullable=False)
    cnsl_type = db.Column(db.Integer, nullable=False)
    cnsl_time = db.Column(db.DateTime, nullable=False)
    cnsl_date = db.Column(db.DateTime, nullable=False)
    cnsl_about = db.Column(db.String(500), nullable=False)
    cnsl_review_cnslrr = db.Column(db.String(500), nullable=False)
    cnsl_review_cnslee = db.Column(db.String(500), nullable=False)


class Donation(db.Model):
    __tablename__ = "donation_details"
    don_id = db.Column(db.Integer, primary_key=True)
    don_amount = db.Column(db.Integer, nullable=True)
    don_date =db.Column(db.DateTime,nullable=False)
    don_by = db.Column(db.String(120), nullable=False)
    don_city = db.Column(db.Integer, nullable=False)
    don_sur_id =db.Column(db.ForeignKey('survivor_details.sur_id'), nullable=True)
    don_doc_id =db.Column(db.ForeignKey('doctor_details.doc_id'), nullable=True)


class Transaction(db.Model):
    __tablename__ = "transaction_details"
    trn_id = db.Column(db.Integer, primary_key=True)
    trn_amount = db.Column(db.Integer, nullable=True)
    trn_type =db.Column(db.String(2),nullable=False)
    trn_timestamp = db.Column(db.DateTime, nullable=False)
    trn_amount = db.Column(db.Integer, nullable=False)
    trn_balance =db.Column(db.Integer, nullable=True)
    trn_desc =db.Column(db.String(500), nullable=True)
    trn_by =db.Column(db.String(500), nullable=True)


