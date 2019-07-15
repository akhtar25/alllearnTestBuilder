from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField,SelectField,DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length,NumberRange,InputRequired
from applicationDB import User,TestDetails
from flask import request
from wtforms.fields.html5 import DateField
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
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    #submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                       EqualTo('password')])
    #submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
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
    marks=StringField('Marks', validators=[DataRequired(),NumberRange(min=0,max=100)])
    upload=SubmitField('Upload')

class QuestionBuilderQueryForm(FlaskForm):
    class_val=SelectField('Class')
    subject_name=SelectField('Subject')
    topics=SelectField('Topics')
    question_desc=TextAreaField('Question')
    option=StringField('Options')
    reference=StringField('Reference')
    submit=SubmitField('Confirm')

class TestBuilderQueryForm(FlaskForm):
    class_val=SelectField('Class')
    subject_name=SelectField('Subject')
    test_type=SelectField('Test Type')
    submit=SubmitField('Load Topics')

    def validate_subject_name(self,subject_name):
        if subject_name.data=='Select':
            raise ValidationError('* Please Select a Subject')




class SchoolRegistrationForm(FlaskForm):
    schoolName =StringField('School Name', validators=[DataRequired(),NumberRange(min=0,max=100)])
    board = SelectField('Board',choices=[(c, c) for c in ['CBSE','ICSE']])
    address1 = TextAreaField('Address Line 1', validators=[DataRequired(),Length(min=0, max=200)])
    address2 = TextAreaField('Address Line 2', validators=[Length(min=0, max=200)])
    locality = StringField('Locality', validators=[DataRequired(),NumberRange(min=0,max=100)])
    city = StringField('City', validators=[DataRequired(),NumberRange(min=0,max=50)])
    state = StringField('State', validators=[DataRequired(),NumberRange(min=0,max=50)])
    country = StringField('Country', validators=[DataRequired(),NumberRange(min=0,max=50)])
    pinCode = StringField('Pin Code', validators=[DataRequired(),NumberRange(min=0,max=10)])
    teacher_name = StringField('Teacher\'s Name', validators=[DataRequired(),NumberRange(min=0,max=100)])
    teacher_subject = StringField('Subject (optional)', validators=[NumberRange(min=0,max=100)])
    classTeacherFor = StringField('Class Teacher For(optional) ', validators=[NumberRange(min=0,max=10)])
    teacher_email = StringField('Email', validators=[DataRequired(),NumberRange(min=0,max=100)])
    paymentPlan = SelectField('Payment Plan',choices=[(c, c) for c in ['Free', 'Fixed', 'Dynamic']])

    def validate_class_val(self,schoolName):
        if schoolName.data=='Select':
            raise ValidationError('* Please enter the school name')
    def validate_section(self,board):
        if board.data=='Select':
            raise ValidationError('Please select a curriculum board')
    def validate_test_type(self,address1):
        if address1.data=='Select':
            raise ValidationError('Please enter the address')
    def validate_city(self,city):
        if city.data=='Select':
            raise ValidationError('Please enter the city')
    def validate_pinCode(self,pinCode):
        if pinCode.data=='Select':
            raise ValidationError('Please enter the pinCode')
    def validate_state(self,state):
        if state.data=='Select':
            raise ValidationError('Please enter the state')

class PaymentDetailsForm(FlaskForm):
    cardNumber = StringField('Card Number', validators=[Length(min=0,max=16)])
    cardHolder = StringField('Card Holder\'s Name', validators=[Length(min=0,max=100)])
    expiry_month = StringField('MM', validators=[NumberRange(min=0,max=12)])
    expiry_year = StringField('YY', validators=[NumberRange(min=2018,max=2099)])
    payButton=SubmitField('Pay')

class addEventForm(FlaskForm):
    eventName  = StringField('Event Name', validators=[Length(max=100)])
    eventDate  = DateField('Event Date')
    duration = StringField('Duration', validators=[Length(max=50)])
    startDate = DateField('Start Date')
    endDate = DateField('End Date')
    category = StringField('Category', validators=[Length(max=100)])

class SingleStudentRegistration(FlaskForm):
    roll_number = StringField('Roll Number', validators=[Length(max=100)])
    fist_name = StringField('First Name', validators=[Length(max=100)])
    last_name = StringField('Last Name', validators=[Length(max=100)])
    class_val = StringField('Class', validators=[Length(max=100)])
    birthdate = DateField('Birth Date', format='%d/%m/%Y')
    address = StringField('Addess', validators=[Length(max=100)])
    section = StringField('Section', validators=[Length(max=100)])
    profilePicture = StringField('Profile Picture', validators=[Length(max=100)])
    guardian_name = StringField('Guardian Name', validators=[Length(max=100)])
    guardian_email = StringField('Guardian Email ', validators=[Length(max=100)])
    guardian_phone = StringField('Guardian Phone', validators=[Length(max=100)])
    relation = StringField('Relation',choices=[(c, c) for c in ['Father', 'Mother', 'Other']])    