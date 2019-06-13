from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField,SelectField,DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from applicationDB import User,TestDetails
from flask import request
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
    class_name=SelectField('Select Class',choices=[('default','Select class'),('1','Class 1'),('2','Class 2'),('3','Class 3'),
    ('4','Class 4'),('5','Class 5'),('6','Class 6'),('7','Class 7'),('8','Class 8'),('9','Class 9'),
    ('10','Class 10')
    ])
    class_section=SelectField('Select Section',choices=[(c, c) for c in ['Select','A', 'B', 'C', 'D']])
    test_type=SelectField('Test Type',choices=[(c, c) for c in ['Select','Class test', 'Unit test', 'SA', 'Practice test']])
    subject_name=SelectField('Subject',choices=[(c, c) for c in ['Select','English', 'Hindi', 'Maths', 'EVS','Social Science','Computer']])
    #submit=SubmitField('Submit')

    def validate_class_name(self,class_name):
        if class_name.data=='default':
            raise ValidationError('* Please Select a Class')
    def validate_class_section(self,class_section):
        if class_section.data=='Select':
            raise ValidationError('* Please Select a Section')
    def validate_test_type(self,test_type):
        if test_type.data=='Select':
            raise ValidationError('* Please Select a Test type')
    def validate_subject_name(self,subject_name):
        if subject_name.data=='Select':
            raise ValidationError('* Please Select a Subject')
