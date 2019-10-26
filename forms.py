from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField,SelectField,DateField,IntegerField,RadioField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length,NumberRange,InputRequired,NumberRange
from applicationDB import User,TestDetails,ClassSection
from flask import request
from wtforms.fields.html5 import DateField
from datetime import datetime
from wtforms.widgets import html5
from wtforms.widgets.html5 import NumberInput
from validate_email import validate_email
import re
#from flask_babel import _, lazy_gettext as _l


class SearchForm(FlaskForm):
    q = StringField(('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)


class LoginForm(FlaskForm):
    #username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    #submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    #username = StringField('Username', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=0, max=12)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                       EqualTo('password')])
    #submit = SubmitField('Register')

    #def validate_username(self, username):
    #    user = User.query.filter_by(username=username.data).first()
    #    if user is not None:
    #        raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    full_name =StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    #submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                       EqualTo('password')])
    #submit = SubmitField('Request Password Reset')

class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')

class ResultQueryForm(FlaskForm):
    class_val=SelectField('Select Class')
    section=SelectField('Select Section')
    test_type=SelectField('Test Type')
    subject_name=SelectField('Subject')
    #submit=SubmitField('Submit')

    #def validate_class_val(self,class_val):
     #   if class_val.data=='Select':
      #      raise ValidationError('* Please Select a Class')
    #def validate_section(self,section):
     #   if section.data=='Select':
      #      raise ValidationError('* Please Select a Section')
   # def validate_test_type(self,test_type):
    #    if test_type.data=='Select':
     #       raise ValidationError('* Please Select a Test type')
    #def validate_subject_name(self,subject_name):
     #   if subject_name.data=='Select':
      #      raise ValidationError('* Please Select a Subject')

class MarksForm(FlaskForm):
    marks=IntegerField('Marks',widget=NumberInput(min=-1,max=100,step=1))
    subjectId = StringField('Subject Id')
    date = DateField('Test Date', validators=[DataRequired()])
    totalMarks = IntegerField('Marks',widget=NumberInput(min=10,max=100,step=1))
    upload=SubmitField('Upload')
    def validate_marks(self,marks):
        if marks.data=='':
            raise ValidationError('* Please fill the field ')


class QuestionBuilderQueryForm(FlaskForm):
    class_val=SelectField('Class')
    subject_name=SelectField('Subject')
    topics=SelectField('Topics')
    chapter_num=SelectField('Select Chapter')
    question_type=SelectField('Question Type',choices=[(c, c) for c in ['Subjective','MCQ1']])
    question_desc=TextAreaField('Question',validators=[DataRequired(),Length(min=0, max=200)])
    option=StringField('Options',validators=[DataRequired()])
    weightage=IntegerField('Weightage',validators=[DataRequired()],widget=NumberInput(min=0,max=100,step=1))
    reference=StringField('Reference')
    submit=SubmitField('Confirm')
    def validate_option(self,option):
        if option.data=='':
            raise ValidationError('Select the correct option')

class QuestionUpdaterQueryForm(FlaskForm):
    class_val=SelectField('Class')
    subject_name=SelectField('Subject')
    topics=SelectField('Topics')
    question_type=SelectField('Question Type',choices=[(c, c) for c in ['Subjective','MCQ1']])
    question_desc=TextAreaField('Question',validators=[DataRequired(),Length(min=0, max=200)])
    option=StringField('Options',validators=[DataRequired()])
    weightage=IntegerField('Weightage',validators=[DataRequired()],widget=NumberInput(min=0,max=100,step=1))
    reference=StringField('Reference')
    submit=SubmitField('Confirm')
    def validate_option(self,option):
        if option.data=='':
            raise ValidationError('Select the correct option')

class LeaderBoardQueryForm(FlaskForm):
    subject_name=SelectField('Subject')
    test_type=SelectField('Test Type')
    section=SelectField('Section') 

class TestBuilderQueryForm(FlaskForm):
    class_val=SelectField('Class')
    subject_name=SelectField('Subject')
    test_type=SelectField('Test Type')
    test_date=DateField('Test Date',format='%d/%m/%Y')
    submit=SubmitField('Load Topics')

class ContentManager(FlaskForm):
    class_val=SelectField('Class')
    subject_name=SelectField('Select Subject')
    chapter_num=SelectField('Select Chapter')
    topics=SelectField('Topics')
    content_type=SelectField('Content Type')

class QuestionBankQueryForm(FlaskForm):
    class_val=SelectField('Select Class')
    subject_name=SelectField('Select Subject')
    chapter_num=SelectField('Select Chapter')
    submit=SubmitField('Load Topics')
    test_type=SubmitField('Test type')




class SchoolRegistrationForm(FlaskForm):
    schoolName =StringField('School Name', validators=[DataRequired()])
    board = SelectField('Board')
    address1 = TextAreaField('Address Line 1', validators=[DataRequired(),Length(min=0, max=200)])
    address2 = TextAreaField('Address Line 2', validators=[Length(min=0, max=200)])
    locality = StringField('Locality', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    pincode = StringField('Pincode',validators=[DataRequired()],widget=NumberInput())
    class_val=StringField('Class',validators=[DataRequired()],widget=NumberInput(min=1,max=10))
    section=StringField('Section',validators=[DataRequired()])
    student_count=StringField('Student Count',validators=[DataRequired()],widget=NumberInput(min=1,max=100))
    #teacher_name = StringField('Teacher\'s Name', validators=[DataRequired()])  
    #teacher_subject = StringField('Subject (optional)')
    #class_teacher = StringField('Teacher\'s Class(optional) ', validators=[NumberRange(min=0,max=10)],widget=NumberInput())
    #class_teacher_section=StringField('Teacher\'s Section')
    #teacher_email = StringField('Email', validators=[DataRequired(),NumberRange(min=0,max=100)])
    #paymentPlan = SelectField('Payment Plan',choices=[(c, c) for c in ['Free', 'Fixed', 'Dynamic']])

   # def validate_class_val(self,schoolName):
    #    if schoolName.data=='Select':
     #       raise ValidationError('* Please enter the school name')
    #def validate_section(self,board):
     #   if board.data=='Select':
      #      raise ValidationError('Please select a curriculum board')
    #def validate_test_type(self,address1):
     #   if address1.data=='Select':
      #      raise ValidationError('Please enter the address')
    #def validate_city(self,city):
     #   if city.data=='Select':
      #      raise ValidationError('Please enter the city')
    #def validate_pincode(self,pincode):
     #   if pincode.data=='Select':
      #      raise ValidationError('Please enter the pinCode')
    #def validate_state(self,state):
     #   if state.data=='Select':
      #      raise ValidationError('Please enter the state')

class SchoolTeacherForm(FlaskForm):
    teacher_name = StringField('Teacher\'s Name', validators=[DataRequired()])  
    teacher_subject = SelectField('Subject')
    class_teacher = SelectField('Class')
    class_teacher_section=SelectField('Section')
    teacher_email = StringField('Email', validators=[DataRequired()])
    
    def validate_teacher_email(self,teacher_email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", teacher_email):
            raise ValidationError('Error in email')

class PaymentDetailsForm(FlaskForm):
    cardNumber = StringField('Card Number', validators=[Length(min=0,max=16)])
    cardHolder = StringField('Card Holder\'s Name', validators=[Length(min=0,max=100)])
    expiry_month = StringField('MM', validators=[NumberRange(min=0,max=12)])
    expiry_year = StringField('YY', validators=[NumberRange(min=2018,max=2099)])
    payButton=SubmitField('Pay')

class addEventForm(FlaskForm):
    eventName  = StringField('Event Name', validators=[DataRequired(),Length(max=100)])
    eventDate  = DateField('Event Date', validators=[DataRequired()])
    duration = StringField('Duration', validators=[DataRequired(),Length(min=0,max=50)])
    startDate = DateField('Start Date', validators=[DataRequired()])
    endDate = DateField('End Date', validators=[DataRequired()])
    category = StringField('Category',validators=[DataRequired(),Length(max=100)])

class SingleStudentRegistration(FlaskForm):
    roll_number = StringField('Roll Number', validators=[Length(max=100)])
    first_name = StringField('First Name', validators=[Length(max=100)])
    last_name = StringField('Last Name', validators=[Length(max=100)])
    class_val = SelectField('Class')
    school_admn_no=StringField('School Admission No.', validators=[Length(max=10)])
    gender=SelectField('Gender',choices=[(c, c) for c in ['Male', 'Female', 'Other']])
    birthdate = DateField('Birth Date')
    phone=StringField('Phone No.',validators=[Length(max=10)])
    address1 = StringField('Address 1', validators=[Length(max=100)])
    address2 = StringField('Addess 2', validators=[Length(max=100)])
    locality = StringField('Locality', validators=[Length(max=100)])
    city = StringField('City', validators=[Length(max=100)])
    state = StringField('State', validators=[Length(max=100)])
    pincode = StringField('Pin code', validators=[Length(max=100)])
    country = StringField('Country', validators=[Length(max=100)])
    section = SelectField('Section')
    guardian_first_name = StringField('Guardian First Name', validators=[Length(max=100)])
    guardian_last_name = StringField('Guardian Last Name', validators=[Length(max=100)])
    guardian_email = StringField('Guardian Email ', validators=[Length(max=100)])
    guardian_phone = StringField('Guardian Phone', validators=[Length(max=100)])
    relation = SelectField('Relation',choices=[(c, c) for c in ['Father', 'Mother', 'Other']])   
    submit=SubmitField('Confirm') 


class feedbackReportForm(FlaskForm):
    class_val=SelectField('Select Class')
    section=SelectField('Select Section')    
    subject_name=SelectField('Select Subject')


class testPerformanceForm(FlaskForm):
    class_val=SelectField('Select Class')
    section=SelectField('Select Section')    
    test_type=SelectField('Select Test Type')


class studentPerformanceForm(FlaskForm):
    class_val1=SelectField('Select Class')
    section1=SelectField('Select Section')    
    test_type1=SelectField('Select Test Type')
    student_name1=SelectField('Select Student')


class createSubscriptionForm(FlaskForm):    
    sub_name =StringField('Subcription Name',validators=[DataRequired(),Length(max=100)])
    monthly_charge= StringField('Charge',validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    student_limit =StringField('Student Limit',validators=[DataRequired()])     
    teacher_limit = StringField('Teacher Limit',validators=[DataRequired()])
    test_limit = StringField('Tests Limit',validators=[DataRequired()])
    sub_desc = TextAreaField('Subscription Description', validators=[Length(min=0, max=500)])
    sub_duration = StringField('Duration',validators=[DataRequired()])


    