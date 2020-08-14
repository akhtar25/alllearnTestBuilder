from flask import Flask, Markup, render_template, request, flash, redirect, url_for, Response,session,jsonify
from send_email import welcome_email, send_password_reset_email, user_access_request_email, access_granted_email, new_school_reg_email, performance_report_email
from send_email import new_teacher_invitation,new_applicant_for_job, application_processed, job_posted_email
from applicationDB import *
from qrReader import *
import csv
import itertools
from config import Config
from forms import LoginForm, RegistrationForm,ContentManager,LeaderBoardQueryForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm,ResultQueryForm,MarksForm, TestBuilderQueryForm,SchoolRegistrationForm, PaymentDetailsForm, addEventForm,QuestionBuilderQueryForm, SingleStudentRegistration, SchoolTeacherForm, feedbackReportForm, testPerformanceForm, studentPerformanceForm, QuestionUpdaterQueryForm,  QuestionBankQueryForm,studentDirectoryForm, promoteStudentForm 
from forms import createSubscriptionForm,ClassRegisterForm,postJobForm, AddLiveClassForm
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from logging.handlers import RotatingFileHandler
import os
import logging
import datetime as dt
from datetime import date
from datetime import timedelta
from datetime import datetime
from pytz import timezone
from tzlocal import get_localzone
from flask_moment import Moment
from elasticsearch import Elasticsearch
from flask import g, jsonify
from forms import SearchForm
from forms import PostForm
from applicationDB import Post  
import barCode
import json, boto3
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func, distinct, text, update
from sqlalchemy.sql import label
import re
import pandas as pd
#from pandas import DataFrame
import numpy as np
import plotly
import pprint
from miscFunctions import subjects,topics,subjectPerformance,signs3Folder,chapters
from docx import Document
from docx.shared import Inches
from urllib.request import urlopen,Request
from io import StringIO, BytesIO
from collections import defaultdict
from sqlalchemy.inspection import inspect
import hashlib
from random import randint
import string
import random
import requests
#import matplotlib.pyplot as plt
from flask_talisman import Talisman, ALLOW_FROM
from flask_api import FlaskAPI, status, exceptions
from calendar import monthrange
import calendar
from urllib.parse import quote,urlparse, parse_qs
from google.oauth2 import id_token
from google.auth.transport import requests
#from flask_material import Material

#app=Flask(__name__)
app=FlaskAPI(__name__)
#csp = {
# 'default-src': [
#        '\'self\'',
#        '*.*.com'
#    ]
#}
talisman = Talisman(app, content_security_policy=None)
#Material(app)
#csrf = CSRFProtect()
#csrf.init_app(app)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)
login_manager.init_app(app)
moment = Moment(app)


app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None

import errors

if not app.debug and not app.testing:
    if app.config['LOG_TO_STDOUT']:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)        
    else:
        dateVal= datetime.today()
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/allLearn'+str(dateVal).replace(' ','').replace(':','').replace('.','')+'.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('allLearn startup')


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now()
        db.session.commit()
    g.search_form = SearchForm()
    #scheme = request.headers.get('X-Forwarded-Proto')        
    #if scheme and scheme == 'http' and request.url.startswith('http://'):        
    #    url = request.url.replace('http://', 'https://', 1)
    #    code = 301
    #    return redirect(url, code=code)
    
    

#helper methods
def schoolNameVal():
    if current_user.is_authenticated:
        teacher_id = ''
        if current_user.user_type==134 or current_user.user_type==234:
            teacher_id = StudentProfile.query.filter_by(user_id=current_user.id).first()
        else:
            teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()        
        if teacher_id != None:
            print(teacher_id.school_id)
            school_name_row=SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
            if school_name_row!=None:
                name=school_name_row.school_name            
                return name
            else:
                return None            
        else:
            return None
    else:
        return None


notes = {
    0: 'do the shopping',
    1: 'build the codez',
    2: 'paint the door',
}

def note_repr(key):
    return {
        'url': request.host_url.rstrip('/') + url_for('notes_detail', key=key),
        'text': notes[key]
    }


@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])



#Route to verify google sign in token
@app.route('/gTokenSignin',methods=["GET","POST"])
def gTokenSignin():
    try:
        idtoken = request.form.get('idtoken')
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(idtoken, requests.Request(), app.config['GOOGLE_CLIENT_ID'])
        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
        print('This is the email: ')
        print(idinfo["email"])
        print('#############')
                
        #section to create new user
        chkUserData = User.query.filter_by(email=str(idinfo["email"])).first()
        if chkUserData==None:
            user = User(username=idinfo["email"], email=idinfo["email"], user_type='140', access_status='144', 
                first_name = idinfo["given_name"],last_name= idinfo["family_name"], last_modified_date = datetime.today(),
                user_avatar = idinfo["picture"], login_type=244)
            #user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            #if a teacher has already been added during school registration then simply add the new user's id to it's teacher profile value        
            checkTeacherProf = TeacherProfile.query.filter_by(email=idinfo["email"]).first()
            #if a student has already been added during school registration then simply add the new user's id to it's student profile value
            checkStudentProf = StudentProfile.query.filter_by(email=idinfo["email"]).first()
    
            if checkTeacherProf!=None:
                checkTeacherProf.user_id=user.id
                db.session.commit()        
            elif checkStudentProf!=None:
                checkStudentProf.user_id=user.id
                db.session.commit()
            else:
                pass
        #end of section
          
        #section to create session and auto login

        #endof section

        return '0'
        # // These six fields are included in all Google ID Tokens.
        # "iss": "https://accounts.google.com",
        # "sub": "110169484474386276334",
        # "azp": "1008719970978-hb24n2dstb40o45d4feuo2ukqmcc6381.apps.googleusercontent.com",
        # "aud": "1008719970978-hb24n2dstb40o45d4feuo2ukqmcc6381.apps.googleusercontent.com",
        # "iat": "1433978353",
        # "exp": "1433981953",
        #
        # // These seven fields are only included when the user has granted the "profile" and
        # // "email" OAuth scopes to the application.
        # "email": "testuser@gmail.com",
        # "email_verified": "true",
        # "name" : "Test User",
        # "picture": "https://lh4.googleusercontent.com/-kYgzyAWpZzJ/ABCDEFGHI/AAAJKLMNOP/tIXL9Ir44LE/s99-c/photo.jpg",
        # "given_name": "Test",
        # "family_name": "User",
        # "locale": "en"
        #}
    except ValueError:
        # Invalid token
        return '1'
        



#@register.filter
#def month_name(month_number):
#    return calendar.month_name[month_number]

@app.route("/api", methods=['GET', 'POST'])
def notes_list():
    """
    List or create notes.
    """
    if request.method == 'POST':
        note = str(request.data.get('text', ''))
        idx = max(notes.keys()) + 1
        notes[idx] = note
        return note_repr(idx), status.HTTP_201_CREATED

    # request.method == 'GET'
    return [note_repr(idx) for idx in sorted(notes.keys())]


#@app.route("/api/leaderBoard/<int:schoolID>",methods=['GET','PUT','DELETE'])
#def leaderboardAPI(schoolID):
#    return leaderboardContent(schoolID)

@property
def serialize(self):
 return {
    'student_id': self.student_id,
    'full_name': self.full_name,
    #'class_val': self.class_val,
    #'section': self.section,
    #'sponsored_status': self.sponsored_status,
    #'sponsored_on': self.sponsored_on,
    #'sponsored_amount': self.sponsored_amount,
    #'sponsored_till': self.sponsored_till,
    #'profile_picture': self.profile_picture,
    #'perf_avg': self.perf_avg,
}



@app.route("/api/studentList/<int:schoolID>/", methods=['GET', 'PUT', 'DELETE'])
def studentListAPI(schoolID):
    #studentList = StudentProfile.query.filter_by(school_id=schoolID).all()
    studentListQuery = "select sp.student_id as student_id, sp.full_name as full_name , cs.class_val as class_val , cs.section as section , sponsored_status as spnsored_status, sponsored_on as sponsoted_on, sponsored_amount as sponsored_amount, sponsored_till as sponsored_till, "
    studentListQuery = studentListQuery + "sp.profile_picture as profile_picture,  CAST ( round( avg(pd.student_score),2) as Varchar) as perf_avg "
    studentListQuery = studentListQuery + "from student_profile sp "
    studentListQuery = studentListQuery + "inner join class_section cs on "
    studentListQuery = studentListQuery + "cs.class_sec_id  = sp.class_sec_id and "
    studentListQuery = studentListQuery + "sp.school_id  = "+str(schoolID)
    studentListQuery = studentListQuery + " inner join performance_detail pd on "
    studentListQuery = studentListQuery + "pd.student_id  = sp.student_id "
    studentListQuery = studentListQuery + "group by sp.student_id , sp.full_name , cs.class_val , cs.section , sp.profile_picture , sponsored_status , sponsored_on , sponsored_amount , sponsored_till "
    studentListQuery = studentListQuery + "order by perf_avg desc"

    studentListData = db.session.execute(text(studentListQuery)).fetchall()
    
    # the two lines below can also be used to send data but without the flask api library
    #resp = jsonify({'result': [dict(row) for row in studentListData]})
    #resp.status_code = 200

    return {'result': [dict(row) for row in studentListData]}
    #return [(str(idx.student_id)+','+str(idx.first_name)+','+str(idx.last_name)+',' +str(idx.sponsored_status)) for idx in studentList]





@app.route("/api/<int:key>/", methods=['GET', 'PUT', 'DELETE'])
def notes_detail(key):
    """
    Retrieve, update or delete note instances.
    """
    if request.method == 'PUT':
        note = str(request.data.get('text', ''))
        notes[key] = note
        return note_repr(key)

    elif request.method == 'DELETE':
        notes.pop(key, None)
        return '', status.HTTP_204_NO_CONTENT

    # request.method == 'GET'
    if key not in notes:
        raise exceptions.NotFound()
    return note_repr(key)
##########################End of test section



def leaderboardContent(qclass_val):
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    query = "select  school,class as class_val,section,studentid,student_name,profile_pic,subjectid,test_count,marks from fn_performance_leaderboard_detail_v1("+str(teacher_id.school_id)+")"
    if qclass_val=='dashboard':
        
        where = " where marks is not null order by marks"
        query = query + where
        print('Query inside leaderboardContent:'+str(query))
    else:
        if qclass_val!='' and qclass_val is not None and str(qclass_val)!='None':
            where = " where class='"+str(qclass_val)+"' order by marks desc"
        else:
            where = " where marks is not null order by marks desc"
        query = query + where
        print('Query inside leaderboardContent:'+str(query))    
    leaderbrd_row = db.session.execute(text(query)).fetchall()
    try:
        df = pd.DataFrame(leaderbrd_row,columns=['school','class_val','section','studentid','student_name','profile_pic','subjectid','test_count','marks'])
        
        leaderbrd_pivot = pd.pivot_table(df,index=['studentid','profile_pic','student_name','class_val','section']
                        , columns='subjectid', values='marks'
                        ,aggfunc='sum').reset_index()
        leaderbrd_pivot = leaderbrd_pivot.rename_axis(None).rename_axis(None, axis=1)
        col_list= list(leaderbrd_pivot)
        col_list.remove('studentid')
        col_list.remove('student_name')
        col_list.remove('class_val')
        col_list.remove('section')
        col_list.remove('profile_pic')
        leaderbrd_pivot['total_marks%'] = leaderbrd_pivot[col_list].mean(axis=1)

        # leaderbrd_pivot = leaderbrd_pivot.groupby(['studentid','student_name','class_val','section']).agg()
        df2 = pd.DataFrame(leaderbrd_row,columns=['school','class_val','section','studentid','student_name','profile_pic','subjectid','test_count','marks'])
        leaderbrd_pivot2 = pd.pivot_table(df2,index=['studentid','profile_pic','student_name','class_val','section']
                        , columns='subjectid', values='test_count'
                        ,aggfunc='sum').reset_index()
        leaderbrd_pivot2 = leaderbrd_pivot2.rename_axis(None).rename_axis(None, axis=1)
        col_list2= list(leaderbrd_pivot2)
        col_list2.remove('studentid')
        col_list2.remove('student_name')
        col_list2.remove('class_val')
        col_list2.remove('section')
        col_list2.remove('profile_pic')
        leaderbrd_pivot2['total_tests'] = leaderbrd_pivot2[col_list2].sum(axis=1)
        result = pd.merge(leaderbrd_pivot,leaderbrd_pivot2,on=('studentid','student_name','class_val','section','profile_pic'))
    except:
        result = 1222
    return result  


def stateList():
    with open('stateList.txt', 'r') as f:
        stateListVal = f.readlines()
        stateListVal = str(stateListVal).split(',')
        return stateListVal


def cityList():
    with open('cityList.txt', 'r') as f:
        cityListVal = f.readlines()
        cityListVal = str(cityListVal)
        cityListVal = cityListVal.replace('[','').replace(']','').replace('\'','').replace(',',':null,')
        cityListVal = cityListVal.split(',')
        cityListVal[-1]=cityListVal[-1]+ ':null'
        cityListDict = dict(item.split(':') for item in cityListVal)
        #cityListVal = cityListVal.split(',')
        return cityListDict


def classSecCheck():
    teacherProfile = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    if teacherProfile==None:
        return 'N'
    else:
        classSecRow = ClassSection.query.filter_by(school_id=teacherProfile.school_id).all()
        #print(classSecRow)
        if len(classSecRow)==0:
            print('returning N')
            return 'N'            
        else:
            return 'Y'

@app.route('/',methods=["GET","POST"])
@app.route('/practiceTest',methods=["GET","POST"])
def practiceTest():    
    if request.method=="POST":
        board = request.form.get('board')
        class_val = request.form.get('class_val')
        email = current_user.email     
        #print("board:"+ str(board))
        #print("class_val:" +str(class_val))
        schoolRow = SchoolProfile.query.filter_by(school_name="AllLearn "+str(board)).first()
        #print("school id:" +str(schoolRow.school_id))
        classSectionRow = ClassSection.query.filter_by(school_id=schoolRow.school_id, class_val=str(class_val)).first()
        #print("class sec id:"+ str(classSectionRow.class_sec_id))
        checkStudTable= StudentProfile.query.filter_by(email=current_user.email).first()
        if checkStudTable==None or checkStudTable=="":
            studentDataAdd = StudentProfile(first_name=current_user.first_name,last_name=current_user.last_name,full_name=current_user.first_name +" " + current_user.last_name,
                school_id=schoolRow.school_id,class_sec_id=classSectionRow.class_sec_id,
                phone=current_user.phone,school_adm_number="prac_"+ str(current_user.id), user_id=current_user.id,
                roll_number=000,last_modified_date=datetime.today(), email=current_user.email,points=10)
            db.session.add(studentDataAdd)
            
            #updating the public.user table
            current_user.user_type=234
            current_user.access_status=145
            current_user.school_id=schoolRow.school_id
            current_user.last_modified_date=datetime.today()
            db.session.commit() 
        else:
            studentDataAdd = StudentProfile.query.filter_by(id=current_user.id).first()

        #This section is to update an anonymously taken test with new student id    
        #try:
        #if session.get('anonUser'):
        #    splitVals = str(session['anonUser']).split('_')
        #    respSessionID = splitVals[1]
        #    session['anonUser'] = False
        #    print("Resp Session ID of older test: "+str(respSessionID))
        #    ###Section to update the test results of anon user with the new student id in resp capture
        #    respUPDQuery = "Update response_capture set student_id=" + str(studentDataAdd.student_id)
        #    respUPDQuery = respUPDQuery + " , class_sec_id=" + str(studentDataAdd.class_sec_id) 
        #    respUPDQuery = respUPDQuery + " where resp_session_id=\'"+ str(respSessionID) + "\'"
        #    print(str(respUPDQuery))
        #    db.session.execute(text(respUPDQuery))
                
        #except:
        #    print('error occurred. response cap not updated.')
        #    pass
        db.session.commit()        
        print('New entry made into the student table')

    if ("school.alllearn" in str(request.url)):
            print('#######this is the request url: '+ str(request.url))
            return redirect(url_for('index'))
    if current_user.is_anonymous:            
        studentProfile = StudentProfile.query.filter_by(user_id=app.config['ANONYMOUS_USERID']).first()  #staging anonymous username f        
    else:
        studentProfile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if studentProfile==None:
        studentData=""      
        testHistory=""  
        perfRows=""
        testCount = 0
        leaderboardData = ""
        class_val=""
        questionsAnswered=0
        print('#####Student data is null')
    else:        
        studentDataQuery = "with temptable as "
        studentDataQuery = studentDataQuery + " (with total_marks_cte as ( "
        studentDataQuery = studentDataQuery + " select sum(suggested_weightage) as total_weightage, count(*) as num_of_questions  from question_details where question_id in "
        studentDataQuery = studentDataQuery + " (select question_id from response_capture rc2 where student_id ="+ str(studentProfile.student_id)+") ) "
        studentDataQuery = studentDataQuery + " select distinct sp.roll_number, sp.full_name, sp.student_id, "
        studentDataQuery = studentDataQuery + " SUM(CASE WHEN rc.is_correct='Y' THEN qd.suggested_weightage ELSE 0 end) AS  points_scored , "
        studentDataQuery = studentDataQuery + " total_marks_cte.total_weightage "
        studentDataQuery = studentDataQuery + " from response_capture rc inner join student_profile sp on "
        studentDataQuery = studentDataQuery + " rc.student_id=sp.student_id "
        studentDataQuery = studentDataQuery + " inner join question_details qd on "
        studentDataQuery = studentDataQuery + " qd.question_id=rc.question_id, total_marks_cte         "
        studentDataQuery = studentDataQuery + " group by sp.roll_number, sp.full_name, sp.student_id, total_marks_cte.total_weightage ) "
        studentDataQuery = studentDataQuery + " ,temp2 as (select count(distinct resp_session_id) as tests_taken "
        studentDataQuery = studentDataQuery + " , student_id from response_capture group by student_id) "
        studentDataQuery = studentDataQuery + " select *from temptable inner join temp2 on temptable.student_id =temp2.student_id and temp2.student_id =" + str(studentProfile.student_id)
        studentData = db.session.execute(text(studentDataQuery)).first()

        
        #getting class_val for the student
        classDataQuery = "select *from class_section cs where class_sec_id="+ str(studentProfile.class_sec_id)
        classData = db.session.execute(classDataQuery).first()
        class_val = classData.class_val

        #performanceQuery = "select *from fn_leaderboard_responsecapture () where student_id='"+str(studentProfile.student_id)+ "'"
        performanceQuery = "select *from fn_leaderboard_responsecapture() where student_id ='"+str(studentProfile.student_id)+"' order by class_val desc" # and class_val='"+str(class_val)+"'"
        perfRows = db.session.execute(text(performanceQuery)).fetchall()

        testCountQuery = "select sum(test_taken) as tests_taken from fn_leaderboard_ResponseCapture() where student_id='"+str(studentProfile.student_id)+ "'"
        testCount = db.session.execute(text(testCountQuery)).first()

        #section for test history query
        testHistoryQuery = "SELECT *FROM fn_student_performance_response_capture("+str(studentProfile.student_id)+")"
        testHistory = db.session.execute(testHistoryQuery).fetchall()
        ##end of test history query

        #other recent test takers
        #recentTestTakersQuery = "select *from fn_student_test_taken_details() order by test_taken_on desc limit 10"
        #recentTestTakers = db.session.execute(recentTestTakersQuery).fetchall()        
        #Questions answered
        questionsAnsweredQuery = "select count(*) as qanswered from response_capture where student_id="+str(studentProfile.student_id)
        questionsAnswered = db.session.execute(questionsAnsweredQuery).first()
        #leaderboard data
        leaderboardQuery = "SELECT student_id,first_name,SUBJECT,student_score,class_val"
        leaderboardQuery = leaderboardQuery + " FROM fn_leaderboard_ResponseCapture() M "
        leaderboardQuery = leaderboardQuery + " WHERE M.student_score = "
        leaderboardQuery = leaderboardQuery + " (SELECT MAX(MM.student_score) FROM fn_leaderboard_ResponseCapture() MM where class_val='"+str(class_val)+"' GROUP BY "
        leaderboardQuery = leaderboardQuery + " MM.SUBJECT having  MM.SUBJECT =M.subject)"
        leaderboardQuery = leaderboardQuery + " order by student_score desc"
        leaderboardData = db.session.execute(leaderboardQuery).fetchall()
    if studentData!=None or studentData!="":
        try:
            avg_performance = round(((studentData.points_scored/studentData.total_weightage) *100),2)
        except:
            avg_performance=0
    else:
        avg_performance = 0
    
    meta_val = "Preparing for exams need not be difficult. Take free mock tests anytime you want with allLearn. CBSE | IIT JEE | NEET | Competitive Exams"
    return render_template('/practiceTest.html',studentData=studentData, disconn=1,
        studentProfile=studentProfile, avg_performance=avg_performance,testHistory=testHistory,perfRows=perfRows,testCount=testCount,
        leaderboardData=leaderboardData,class_val=class_val,questionsAnswered=questionsAnswered,title='Take unlimited free practice tests anytime',
        meta_val=meta_val)


@app.route('/normal')
def normal():
    return 'Normal'

@app.route('/embeddable')
@talisman(frame_options=ALLOW_FROM, frame_options_allow_from='*')
def embeddable():
    return 'Embeddable'

@app.route("/loaderio-ad2552628971ece0389988c13933a170/")
def performanceTestLoaderFunction():
    return render_template("loaderio-ad2552628971ece0389988c13933a170.html")

@app.route("/account/")
@login_required
def account():
    return render_template('account.html')

@app.route('/sign-s3')
def sign_s3():
    S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
    #S3_BUCKET = "alllearndatabucketv2"
    file_name = request.args.get('file-name')
    print(file_name)    
    file_type = request.args.get('file-type')
    print(file_type)
    #if file_type=='image/png' or file_type=='image/jpeg':
    #   file_type_folder='images'
    #s3 = boto3.client('s3')
    s3 = boto3.client('s3', region_name='ap-south-1')
    folder_name=request.args.get('folder')
    print('FolderName:'+folder_name)
    # folder_url=signs3Folder(folder_name,file_type)
    folder_url = folder_name
    print('folder_url:'+str(folder_url))
    print(s3)

    presigned_post = s3.generate_presigned_post(
      Bucket = S3_BUCKET,
      Key = str(folder_url)+"/"+str(file_name),
      Fields = {"acl": "public-read", "Content-Type": file_type},
      Conditions = [
        {"acl": "public-read"},
        {"Content-Type": file_type}
      ],
      ExpiresIn = 3600
    )
   
    
    return json.dumps({
      'data': presigned_post,
      'url': 'https://%s.s3.amazonaws.com/%s/%s' % (S3_BUCKET,folder_url,file_name)
    })


@app.route("/submit_form/", methods = ["POST"])
@login_required
def submit_form():
    #teacherProfile = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #teacherProfile.teacher_name = request.form["full-name"]
    #teacherProfile.profile_picture = request.form["avatar-url"]
    #db.session.commit()
    #flash('DB values updated')
    return redirect(url_for('account'))


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password_page.html', form=form)


@app.route('/schoolProfile')
@login_required
def schoolProfile():
    print('User Type Id:'+str(current_user.user_type))
    studentDetails = StudentProfile.query.filter_by(user_id = current_user.id).first()
    if current_user.user_type==134:
        teacherRow=StudentProfile.query.filter_by(user_id=current_user.id).first()
    else:
        teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    registeredStudentCount = db.session.execute(text("select count(*) from student_profile where school_id ='"+str(teacherRow.school_id)+"'")).first()
    registeredTeacherCount = db.session.execute(text("select count(*) from teacher_profile where school_id ='"+str(teacherRow.school_id)+"'")).first()
    allTeachers = TeacherProfile.query.filter_by(school_id=teacherRow.school_id).all()
    classSectionRows = ClassSection.query.filter_by(school_id=teacherRow.school_id).all()
    schoolProfileRow = SchoolProfile.query.filter_by(school_id = teacherRow.school_id).first()
    addressRow = Address.query.filter_by(address_id = schoolProfileRow.address_id).first()
    subscriptionRow = SubscriptionDetail.query.filter_by(sub_id = schoolProfileRow.sub_id).first()
    value=0
    #if current_user.user_type==134:
    #    value=1
    return render_template('schoolProfile.html', teacherRow=teacherRow, registeredStudentCount=registeredStudentCount, registeredTeacherCount=registeredTeacherCount,allTeachers=allTeachers,classSectionRows=classSectionRows, schoolProfileRow=schoolProfileRow,addressRow=addressRow,subscriptionRow=subscriptionRow,disconn=value,user_type_val=str(current_user.user_type),studentDetails=studentDetails)




@app.route('/schoolRegistration', methods=['GET','POST'])
@login_required
def schoolRegistration():
    #queries for subcription 
    fromImpact = request.args.get('fromImpact')
    subscriptionRow = SubscriptionDetail.query.filter_by(archive_status='N').order_by(SubscriptionDetail.sub_duration_months).all()    
    distinctSubsQuery = db.session.execute(text("select distinct group_name, sub_desc, student_limit, teacher_limit, test_limit from subscription_detail where archive_status='N' order by student_limit ")).fetchall()

    S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
    form = SchoolRegistrationForm()
    form.board.choices=[(str(i.description), str(i.description)) for i in MessageDetails.query.with_entities(MessageDetails.description).distinct().filter_by(category='Board').all()]
    if form.validate_on_submit():
        user = User.query.filter_by(id=current_user.id).first()
        user.user_type = 71
        user.access_status = 145
        db.session.commit()
        selected_sub_id = request.form.get('selected_sub_id')        
        address_id=Address.query.filter_by(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data).first()
        if address_id is None:
            address_data=Address(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data,country=form.country.data)
            db.session.add(address_data)
            address_id=db.session.query(Address).filter_by(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data).first()
        board_id=MessageDetails.query.filter_by(description=form.board.data).first()
        school_picture=request.files['school_image']
        school_picture_name=request.form['file-input'] 

        school=SchoolProfile(school_name=form.schoolName.data,board_id=board_id.msg_id,address_id=address_id.address_id,registered_date=dt.datetime.now(), last_modified_date = dt.datetime.now(), sub_id=selected_sub_id,how_to_reach=form.how_to_reach.data)
        db.session.add(school)
        school_id=db.session.query(SchoolProfile).filter_by(school_name=form.schoolName.data,address_id=address_id.address_id).first()
        if school_picture_name!='':
            school = SchoolProfile.query.get(school_id.school_id)
            school.school_picture = 'https://'+ S3_BUCKET + '.s3.amazonaws.com/school_data/school_id_' + str(school_id.school_id) + '/school_profile/' + school_picture_name
            client = boto3.client('s3', region_name='ap-south-1')
            client.upload_fileobj(school_picture , os.environ.get('S3_BUCKET_NAME'), 'school_data/school_id_'+ str(school_id.school_id) + '/school_profile/' + school_picture_name,ExtraArgs={'ACL':'public-read'})
       
        teacher=TeacherProfile(school_id=school.school_id,email=current_user.email,user_id=current_user.id, designation=147, registration_date=dt.datetime.now(), last_modified_date=dt.datetime.now(), phone=current_user.phone, device_preference=78 )
        db.session.add(teacher)
        db.session.commit()
        newTeacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        newSchool = SchoolProfile.query.filter_by(school_id=school_id.school_id).first() 
        session['school_logo'] = newSchool.school_logo 
        session['schoolPicture'] = newSchool.school_picture   
        # Session variable code start
        session['schoolName'] = schoolNameVal()
        session['userType'] = current_user.user_type
        session['username'] = current_user.username
        
        #print('user name')
        #print(session['username'])
        school_id = ''
        #print('user type')
        #print(session['userType'])
        session['studentId'] = ''
        # if session['userType']==71:
        #     school_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
        # elif session['userType']==134:
        #     school_id = StudentProfile.query.filter_by(user_id=current_user.id).first()
        #     session['studentId'] = school_id.student_id
        # else:
        #     school_id = User.query.filter_by(id=current_user.id).first()
        # school_pro = SchoolProfile.query.filter_by(school_id=school_id.school_id).first()
        # session['school_logo'] = ''
        # if school_pro:
        #     session['school_logo'] = school_pro.school_logo
        #     session['schoolPicture'] = school_pro.school_picture
        query = "select user_type,md.module_name,description, module_url, module_type from module_detail md inner join module_access ma on md.module_id = ma.module_id where user_type = '"+str(current_user.user_type)+"' and ma.is_archived = 'N' and md.is_archived = 'N' order by module_type"
        moduleDetRow = db.session.execute(query).fetchall()
        #print('School profile')
        # print(session['schoolPicture'])
        # det_list = [1,2,3,4,5]
        session['moduleDet'] = []
        detList = session['moduleDet']
        
        for det in moduleDetRow:
            eachList = []
            print(det.module_name)
            print(det.module_url)
            eachList.append(det.module_name)
            eachList.append(det.module_url)
            eachList.append(det.module_type)
            # detList.append(str(det.module_name)+":"+str(det.module_url)+":"+str(det.module_type))
            detList.append(eachList)
        session['moduleDet'] = detList
        # End code   
        newSchool.school_admin = newTeacherRow.teacher_id

        db.session.commit()
        flash('School Registered Successfully!')
        new_school_reg_email(form.schoolName.data)
        fromSchoolRegistration = True
       
        subjectValues = MessageDetails.query.filter_by(category='Subject').all()
        teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
        board = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
        boardRows = MessageDetails.query.filter_by(msg_id=board.board_id).first()
        school_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
        classValues = "SELECT class_val,sum(class_sec_id) as s FROM class_section cs where school_id = '"+str(teacher_id.school_id)+"' group by class_val order by s"
        classValues = db.session.execute(text(classValues)).fetchall()
        classValuesGeneral = "SELECT class_val,sum(class_sec_id) as s FROM class_section cs group by class_val order by s"
        classValuesGeneral = db.session.execute(text(classValuesGeneral)).fetchall()
        subjectValues = MessageDetails.query.filter_by(category='Subject').all()
        bookName = BookDetails.query.all()
        chapterNum = Topic.query.distinct().all()
        topicId = Topic.query.all()
        generalBoardId = SchoolProfile.query.with_entities(SchoolProfile.board_id).filter_by(school_id=teacher_id.school_id).first()
        generalBoard = MessageDetails.query.filter_by(msg_id=generalBoardId.board_id).first()
        fromSchoolRegistration = True
        return render_template('syllabus.html',generalBoard=generalBoard,boardRowsId = boardRows.msg_id , boardRows=boardRows.description,subjectValues=subjectValues,school_name=school_id.school_name,classValues=classValues,classValuesGeneral=classValuesGeneral,bookName=bookName,chapterNum=chapterNum,topicId=topicId,fromSchoolRegistration=fromSchoolRegistration,user_type_val=str(current_user.user_type))
    return render_template('schoolRegistration.html',fromImpact=fromImpact,disconn = 1,form=form, subscriptionRow=subscriptionRow, distinctSubsQuery=distinctSubsQuery)

@app.route('/admin')
@login_required
def admin():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    query = "select count(*) from public.user where user_type='161'"
    query2 = "SELECT count(*) FROM public.user WHERE last_seen >=current_date - 30;"
    count = db.session.execute(text(query)).fetchall()
    user_type_val = current_user.user_type
    min_user_count = db.session.execute(text(query2)).first()
    schoolDetails = SchoolProfile.query.all()
    teacherDetails = TeacherProfile.query.all()
    schoolCount = "select count(*) from school_profile"
    school_count = db.session.execute(text(schoolCount)).first()
    print(school_count[0])
    teacherCount = "select count(*) from teacher_profile"
    teacher_count = db.session.execute(text(teacherCount)).first()
    studentCount = "select count(*) from student_profile"
    student_count = db.session.execute(text(studentCount)).first()
    userCount = "select count(*) from public.user"
    user_count = db.session.execute(text(userCount)).first()

    userTypeCount = "select user_type,count(*) as user_count,description from public.user inner join message_detail on msg_id=user_type group by user_type,description"
    user_type_count = db.session.execute(text(userTypeCount)).fetchall()
    schoolreg1 = "SELECT count(*) FROM school_profile WHERE registered_date <=current_date - 30;"
    regSchool1 = db.session.execute(text(schoolreg1)).first()
    schoolreg2 = "SELECT count(*) FROM school_profile WHERE registered_date >=current_date - 30;"
    regSchool2 = db.session.execute(text(schoolreg2)).first()

    teacherreg1 = "SELECT count(*) FROM teacher_profile WHERE registration_date <=current_date - 30;"
    regTeacher1 = db.session.execute(text(teacherreg1)).first()
    teacherreg2 = "SELECT count(*) FROM teacher_profile WHERE registration_date >=current_date - 30;"
    regTeacher2 = db.session.execute(text(teacherreg2)).first()

    studentreg1 = "SELECT count(*) FROM student_profile WHERE registration_date <=current_date - 30;"
    regStudent1 = db.session.execute(text(studentreg1)).first()
    studentreg2 = "SELECT count(*) FROM student_profile WHERE registration_date >=current_date - 30;"
    regStudent2 = db.session.execute(text(studentreg2)).first()
    print(regTeacher2[0])
    print(regTeacher1[0])
    try:
        perSchool = float((int(regSchool2[0])*100)/int(regSchool1[0]))
        perSchool = round(perSchool,2)
    except:
        perSchool = 0
    try: 
        perTeacher = float((int(regTeacher2[0])*100)/int(regTeacher1[0]))
        perTeacher = round(perTeacher,2)
    except:
        perTeacher = 0
    try:
        perStudent = float((int(regStudent2[0])*100)/int(regStudent1[0]))
        perStudent = round(perStudent,2)
    except:
        perStudent = 0
    # perSchool=''
    num = ''
    num2 = ''
    for c in count:
        num = c.count
    # for c2 in count2:
    #     num2 = c2.count
    print('Count'+str(num))
    print('Count2:'+str(num2))
    return render_template('admin.html',count=num,user_type_val=str(current_user.user_type),schoolDetails=schoolDetails,school_count=school_count,teacher_count=teacher_count,student_count=student_count,teacherDetails=teacherDetails,user_count=user_count,min_user_count=min_user_count,user_type_count=user_type_count,perSchool=perSchool,perTeacher=perTeacher,perStudent=perStudent)


@app.route('/promoteStudent',methods=['POST','GET'])
@login_required
def promoteStudent():
    form = promoteStudentForm()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    available_class=ClassSection.query.with_entities(ClassSection.class_val,ClassSection.section).distinct().order_by(ClassSection.class_val).filter_by(school_id=teacher_id.school_id).all()
    class_list=[(str(i.class_val)+"-"+str(i.section),str(i.class_val)+"-"+str(i.section)) for i in available_class]
    form.class_section1.choices = class_list
    form.class_section2.choices = class_list
    studentListQuery = "select sp.student_id,sp.school_id ,full_name , section ,class_val ,section from student_profile sp inner join class_section cs on sp.class_sec_id =cs.class_sec_id where sp.school_id='"+str(teacher_id.school_id)+"'"
    studentList = db.session.execute(studentListQuery).fetchall()
    if request.method == 'POST':
        #print('Inside post request')    
        flash('Student promoted successfully')
        classSecBefore = form.class_section1.data
        classSecAfter = form.class_section2.data
        #print('Class Section after')
        #print(classSecAfter)
        resClassSection = classSecAfter.split("-")
        classAfter = resClassSection[0]
        #print(classAfter)
        sectionAfter = resClassSection[1]
        #print(sectionAfter)
        value = request.form.getlist('checkbox')
        for i in range(len(value)):
            #print(value[i])
            studentPromote = StudentProfile.query.filter_by(student_id=str(value[i])).first()
            #print(studentPromote.full_name)
            classSection = ClassSection.query.with_entities(ClassSection.class_sec_id).filter_by(class_val=str(classAfter),section=str(sectionAfter),school_id=str(teacher_id.school_id)).first()
            studentPromote.class_sec_id = classSection.class_sec_id
            db.session.commit()
            studentClassSec = StudentClassSecDetail.query.filter_by(student_id=str(value[i])).first()
            if studentClassSec:
                studentClassSec.is_current = 'N'
                db.session.commit()
            classSecAdd = StudentClassSecDetail(student_id=str(value[i]),
            class_sec_id=classSection.class_sec_id,class_val=str(classAfter),
            section=str(sectionAfter),is_current='Y',last_modified_date=datetime.now(),promotion_date=datetime.now())
            db.session.add(classSecAdd)
            db.session.commit()
        return render_template('promoteStudent.html',form=form,studentList=studentList,user_type_val=str(current_user.user_type))
    else:
        return render_template('promoteStudent.html',form=form,studentList=studentList,user_type_val=str(current_user.user_type))

@app.route('/classRegistration', methods=['GET','POST'])
@login_required
def classRegistration():
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    classSectionRows = ClassSection.query.filter_by(school_id=teacherRow.school_id).all()

    form = ClassRegisterForm()
    #if form.validate_on_submit():
    if request.method == 'POST':
        #print('passed validation')
        class_val=request.form.getlist('class_val')
        class_section=request.form.getlist('section')
        student_count=request.form.getlist('student_count')

        for i in range(len(class_val)):
            #print('there is a range')
            class_data=ClassSection(class_val=int(class_val[i]),section=str(class_section[i]).upper(),student_count=int(student_count[i]),school_id=teacherRow.school_id)
            db.session.add(class_data)
        
        db.session.commit()
        #adding records to topic tracker while registering school
        
        classSecRows = ClassSection.query.filter_by(school_id=teacherRow.school_id).all()

        topicTrackerRows = "select distinct class_sec_id from topic_tracker where school_id='"+str(teacherRow.school_id)+"'"

        classSecNotInTopicTracker = db.session.execute(text(topicTrackerRows)).fetchall()

        for i in range(len(class_val)):
            class_id = ClassSection.query.with_entities(ClassSection.class_sec_id).filter_by(school_id=teacherRow.school_id,class_val=class_val[i]).first()
            if class_id.class_sec_id not in classSecNotInTopicTracker: 
                insertRow = "insert into topic_tracker (subject_id, class_sec_id, is_covered, topic_id, school_id, reteach_count, last_modified_date) (select subject_id, '"+str(class_id.class_sec_id)+"', 'N', topic_id, '"+str(teacherRow.school_id)+"', 0,current_date from Topic_detail where class_val="+str(class_val[i])+")"
                db.session.execute(text(insertRow))
        db.session.commit()

        flash('Classes added successfully!')
    return render_template('classRegistration.html', classSectionRows=classSectionRows,form=form)    
    



@app.route('/teacherDirectory',methods=['GET','POST'])
@login_required
def teacherDirectory():
    school_name_val = schoolNameVal()
    
    if school_name_val ==None:
        print('did we reach here')
        return redirect(url_for('disconnectedAccount'))
    else:
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        #section for payroll report
        payrollReportQuery = "select to_date(concat('01-',month,'-',year),'DD-MM-YYYY') as period, sum(calc_salary) as salary_spend, count(*) teacher_count, (avg(days_present) / avg(days_in_month))*100 as avg_productivity from teacher_payroll_detail where school_id= "+ str(teacher_id.school_id)
        payrollReportQuery= payrollReportQuery+" group  by month, year "
        payrollReportData = db.session.execute(payrollReportQuery).fetchall()
        #end of payroll report section
        allTeachers = TeacherProfile.query.filter_by(school_id = teacher_id.school_id).all()
        available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher_id.school_id).all()
        class_list=[('select','Select')]
        section_list=[]
        for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all():
            class_list.append((str(i.class_val), "Class "+str(i.class_val)))
        for i in available_section:
            section_list.append((i.section,i.section))
        form=SchoolTeacherForm()
        form.teacher_subject.choices = [(str(i.msg_id), str(i.description)) for i in MessageDetails.query.with_entities(MessageDetails.msg_id,MessageDetails.description).distinct().filter_by(category='Subject').all()]
        form.class_teacher.choices = class_list
        form.class_teacher_section.choices = section_list
        if request.method=='POST':
            teacher_name=request.form.getlist('teacher_name')
            teacher_subject=request.form.getlist('teacher_subject')
            teacher_class=request.form.getlist('class_teacher')
            teacher_class_section=request.form.getlist('class_teacher_section')
            teacher_email=request.form.getlist('teacher_email')
            print(teacher_name)
            for i in range(len(teacher_name)):
                if teacher_class[i]!='select':
                    class_sec_id=ClassSection.query.filter_by(class_val=str(teacher_class[i]),section=teacher_class_section[i]).first()
                    teacher_data=TeacherProfile(teacher_name=teacher_name[i],school_id=teacher_id.school_id,class_sec_id=class_sec_id.class_sec_id,email=teacher_email[i],subject_id=int(teacher_subject[i]),last_modified_date= datetime.now(), registration_date = datetime.now())
                    db.session.add(teacher_data)
                else:
                    teacher_data=TeacherProfile(teacher_name=teacher_name[i],school_id=teacher_id.school_id,email=teacher_email[i],subject_id=int(teacher_subject[i]),last_modified_date= datetime.now(), registration_date = datetime.now(), device_preference=195)
                    db.session.add(teacher_data)
                    #send email to the teachers here
                new_teacher_invitation(teacher_email[i],teacher_name[i],school_name_val, str(teacher_id.teacher_name))
            db.session.commit()
            flash('Successful registration !')            
        return render_template('teacherDirectory.html',form=form, payrollReportData=payrollReportData,allTeachers=allTeachers,user_type_val=str(current_user.user_type))

# New Section added to manage feeDetail
@app.route('/feeMonthData')
def feeMonthData():
    qmonth = request.args.get('month')
    qyear = request.args.get('year')
    class_val = request.args.get('class_val')
    section = request.args.get('section')
    print('inside Summary Box route')
    print(class_val)
    print(section)
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ''
    if class_val!=None:
        class_sec_id = ClassSection.query.filter_by(class_val=class_val,section=section,school_id=teacherDataRow.school_id).first()
    print(qmonth+ ' '+qyear)
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #days in month
    daysInMonth = monthrange(int(qyear),int(qmonth))
    daysInMonth = int(daysInMonth[1])
    feeDetail = ''
    if class_val=='None' or class_val=='':
        print('if class is None')
        paid_fees = "select sum(fee_paid_amount) as collected_fee from fee_detail where school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        paid_fees = db.session.execute(text(paid_fees)).first()
        paid_student_count = "select count(*) as no_of_paid_students from fee_detail where fee_amount=fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        paid_student_count = db.session.execute(text(paid_student_count)).first()
        classSec_ids = FeeClassSecDetail.query.filter_by(school_id=teacherDataRow.school_id).all()
        unpaid_students_count = 0
        for class_sec_id in classSec_ids:
            unpaid_students = "select count(*) as no_of_unpaid_students from student_profile sp where sp.student_id not in (select student_id from fee_detail where school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"') and sp.school_id='"+str(teacherDataRow.school_id)+"' and sp.class_sec_id='"+str(class_sec_id.class_sec_id)+"'"
            unpaid_students = db.session.execute(text(unpaid_students)).first()
            unpaid_students_count = unpaid_students_count + unpaid_students.no_of_unpaid_students
        partially_paid_students = "select count(*) as partially_paid_students from fee_Detail where fee_amount>fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        partially_paid_students = db.session.execute(text(partially_paid_students)).first()
        class_sec_ids = ClassSection.query.filter_by(school_id=teacherDataRow.school_id).all()
        total_unpaid_students = 0
        if partially_paid_students:
            total_unpaid_students = int(unpaid_students_count) + int(partially_paid_students.partially_paid_students)
        
        total_unpaid_fee = 0
        for class_sec_id in class_sec_ids:
            unpaid_students = "select count(*) as no_of_unpaid_students from student_profile sp where sp.student_id not in (select student_id from fee_detail where school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"') and sp.school_id='"+str(teacherDataRow.school_id)+"' and sp.class_sec_id='"+str(class_sec_id.class_sec_id)+"'"
            unpaid_students = db.session.execute(text(unpaid_students)).first()
            fee_amount = FeeClassSecDetail.query.filter_by(class_sec_id=class_sec_id.class_sec_id,school_id=teacherDataRow.school_id).first()
            unpaid_students_fee = 0
            if unpaid_students and fee_amount:
                unpaid_students_fee = int(unpaid_students.no_of_unpaid_students) * int(fee_amount.amount)
            partially_paid_fee = "select sum(outstanding_amount) as pending_amount from fee_detail where fee_amount>fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
            partially_paid_fee = db.session.execute(text(partially_paid_fee)).first()
            if partially_paid_fee:
                print('partially paid fee:'+str(partially_paid_fee.pending_amount))
            if partially_paid_fee.pending_amount:
                total_unpaid_fee = total_unpaid_fee + unpaid_students_fee + partially_paid_fee.pending_amount
            else:
                total_unpaid_fee = total_unpaid_fee + unpaid_students_fee
    else:
        print('if class is not None')
        paid_fees = "select sum(fee_paid_amount) as collected_fee from fee_detail where school_id='"+str(teacherDataRow.school_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        paid_fees = db.session.execute(text(paid_fees)).first()
        paid_student_count = "select count(*) as no_of_paid_students from fee_detail where fee_amount=fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        paid_student_count = db.session.execute(text(paid_student_count)).first()
        unpaid_students = "select count(*) as no_of_unpaid_students from student_profile sp where sp.student_id not in (select student_id from fee_detail where school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"') and sp.school_id='"+str(teacherDataRow.school_id)+"' and sp.class_sec_id='"+str(class_sec_id.class_sec_id)+"'"
        unpaid_students = db.session.execute(text(unpaid_students)).first()
        partially_paid_students = "select count(*) as partially_paid_students from fee_Detail where fee_amount>fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        partially_paid_students = db.session.execute(text(partially_paid_students)).first()
        total_unpaid_students = 0
        if unpaid_students and partially_paid_students:
            total_unpaid_students = int(unpaid_students.no_of_unpaid_students) + int(partially_paid_students.partially_paid_students)
        fee_amount = FeeClassSecDetail.query.filter_by(class_sec_id=class_sec_id.class_sec_id,school_id=teacherDataRow.school_id).first()
        
        unpaid_students_fee = 0
        if unpaid_students and fee_amount:
            unpaid_students_fee = int(unpaid_students.no_of_unpaid_students) * int(fee_amount.amount)
        partially_paid_fee = "select sum(outstanding_amount) as pending_amount from fee_detail where fee_amount>fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        partially_paid_fee = db.session.execute(text(partially_paid_fee)).first()
        total_unpaid_fee = 0
        if partially_paid_fee:
            print('partially paid fee:'+str(partially_paid_fee.pending_amount))
            if partially_paid_fee.pending_amount:
                total_unpaid_fee = unpaid_students_fee + partially_paid_fee.pending_amount
            else:
                total_unpaid_fee = unpaid_students_fee
    return render_template('_summaryBox.html',paid_fees=paid_fees.collected_fee,paid_student_count=paid_student_count.no_of_paid_students,total_unpaid_students=total_unpaid_students,total_unpaid_fee=total_unpaid_fee)

# New Section added to manage fee status
@app.route('/feeStatusDetail')
def feeStatusDetail():
    qmonth = request.args.get('month')
    qyear = request.args.get('year')
    class_val = request.args.get('class_val')
    section = request.args.get('section')
    
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,section=section,school_id=teacherDataRow.school_id).first()
    print(qmonth+ ' '+qyear)
    #days in month
    daysInMonth = monthrange(int(qyear),int(qmonth))
    daysInMonth = int(daysInMonth[1])
    feeStatusDataQuery = "select sp.student_id as student_id, sp.profile_picture as profile_picture, sp.full_name as student_name, fd.fee_amount as fee_amount,fd.fee_paid_amount as paid_amount, fd.outstanding_amount as rem_amount, fd.paid_status as paid_status,fd.delay_reason"
    feeStatusDataQuery = feeStatusDataQuery + " from student_profile  sp left join "
    feeStatusDataQuery = feeStatusDataQuery + "fee_detail fd on fd.student_id=sp.student_id "
    feeStatusDataQuery = feeStatusDataQuery + " and fd.month = "+str(qmonth) + " and fd.year = "+ str(qyear) + " where sp.school_id=" + str(teacherDataRow.school_id) + " and sp.class_sec_id='"+str(class_sec_id.class_sec_id)+"' order by paid_status asc"
    feeStatusDataRows = db.session.execute(text(feeStatusDataQuery)).fetchall()
    print(str(len(feeStatusDataRows)))
    sections = ClassSection.query.filter_by(school_id=teacherDataRow.school_id,class_val=class_val).all()
    total_amt = ''
    amount = FeeClassSecDetail.query.filter_by(class_sec_id=class_sec_id.class_sec_id,school_id=teacherDataRow.school_id).first()
    if amount:
        total_amt = amount.amount
    print('Total amount:'+str(total_amt))
    return render_template('_feeStatusTable.html',total_amt=total_amt,feeStatusDataRows=feeStatusDataRows,qmonth=qmonth,qyear=qyear,class_val=class_val,section=section)
#New Section added to manage payroll
@app.route('/payrollMonthData')
def payrollMonthData():
    qmonth = request.args.get('month')
    qyear = request.args.get('year')
    print(qmonth+ ' '+qyear)
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #days in month
    daysInMonth = monthrange(int(qyear),int(qmonth))
    daysInMonth = int(daysInMonth[1])
    #temporary query
    payrollDataQuery = "select tp.teacher_id as teacher_id, tp.profile_picture as profile_picture, tp.teacher_name as teacher_name, tp.curr_salary as curr_salary,tpd.days_present as days_present, tpd.calc_salary, tpd.paid_status as paid_status"
    payrollDataQuery = payrollDataQuery + " from teacher_profile  tp left join "
    payrollDataQuery = payrollDataQuery + "teacher_payroll_detail tpd on tpd.teacher_id=tp.teacher_id "
    payrollDataQuery = payrollDataQuery + " and tpd.month = "+str(qmonth) + " and tpd.year = "+ str(qyear) + " where tp.school_id=" + str(teacherDataRow.school_id) + " order by paid_status asc"
    payrollDataRows = db.session.execute(text(payrollDataQuery)).fetchall()
    print(str(len(payrollDataRows)))
    return render_template('_payrollMonthData.html',daysInMonth=daysInMonth, payrollDataRows=payrollDataRows, qmonth=qmonth, qyear = qyear)

@app.route('/updateFeeData', methods=['GET','POST'])
def updateFeeData():
    teacherDetailRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()    
    qmonth = request.form.get('qmonth')
    qyear = request.form.get('qyear')
    total_amt = request.args.get('total_amt')
    total_amt = total_amt.strip()
    qclass_val = request.form.get('qclass_val')
    qsection = request.form.get('qsection')
    print('inside updateFeeData')
    print('Total Fee Amount:'+str(total_amt))
    class_sec_id = ClassSection.query.filter_by(class_val=qclass_val,section=qsection,school_id=teacherDetailRow.school_id).first()
    student_id_list = request.form.getlist('student_id')
    paid_amount_list = request.form.getlist('paid_amount')
    rem_amount_list = request.form.getlist('rem_amount')
    # validation when rem_amount is negative
    for i in range(len(rem_amount_list)-1):
        print('inside re_amount_list')
        print(i)
        print(rem_amount_list[i])
        if rem_amount_list[i]:
            if int(rem_amount_list[i])<0:
                return jsonify(['1'])
    # End
    delay_reason_list = request.form.getlist('delay_reason')
    count_list = []
    for i in range(len(paid_amount_list)):
        if paid_amount_list[i]:
            print('counter:'+str(i))
            print('paid amount:'+str(paid_amount_list[i]))
            count_list.append(i)
    # print(paid_amount_list)
    print('count_list length:'+str(len(count_list)))
    for i in range(len(count_list)):
        print('inside for loop')
        print(count_list[i])
        print(student_id_list[count_list[i]])
        if paid_amount_list[count_list[i]]:
            indivFeeRecord = FeeDetail.query.filter_by(student_id=student_id_list[count_list[i]], month=qmonth, year=qyear).first()
            if indivFeeRecord and indivFeeRecord.outstanding_amount!=0:
                print('if record already exist:'+str(paid_amount_list[count_list[i]]))
                indivFeeRecord.fee_amount = total_amt
                indivFeeRecord.fee_paid_amount = paid_amount_list[count_list[i]]
                indivFeeRecord.outstanding_amount = rem_amount_list[count_list[i]]
                indivFeeRecord.delay_reason = delay_reason_list[count_list[i]]
                print('pending amount:'+str(rem_amount_list[count_list[i]]))
                if rem_amount_list[count_list[i]]==0 or rem_amount_list[count_list[i]]=='0':
                    indivFeeRecord.paid_status = 'Y'
                else:
                    indivFeeRecord.paid_status = 'N'
            elif indivFeeRecord==None or indivFeeRecord=='':
                print('Adding new values:'+str(paid_amount_list[count_list[i]]))
                print('Paid Amount:'+paid_amount_list[count_list[i]])
                print('Total Amount:'+total_amt)
                if float(paid_amount_list[count_list[i]])==float(total_amt):
                    print('if paid amount equal to total amount')
                    feeInsert=FeeDetail(school_id=teacherDetailRow.school_id,student_id=student_id_list[count_list[i]],fee_amount = total_amt,
                    class_sec_id=class_sec_id.class_sec_id,payment_date=datetime.today(),fee_paid_amount = paid_amount_list[count_list[i]],outstanding_amount=rem_amount_list[count_list[i]],month=qmonth,year=qyear
                    ,paid_status='Y',delay_reason=delay_reason_list[count_list[i]],last_modified_date=datetime.today())
                else:
                    print('if paid amount is less than total amount')
                    feeInsert=FeeDetail(school_id=teacherDetailRow.school_id,student_id=student_id_list[count_list[i]],fee_amount = total_amt,
                    class_sec_id=class_sec_id.class_sec_id,payment_date=datetime.today(),fee_paid_amount = paid_amount_list[count_list[i]],outstanding_amount=rem_amount_list[count_list[i]],month=qmonth,year=qyear
                    ,paid_status='N',delay_reason=delay_reason_list[count_list[i]],last_modified_date=datetime.today())
                db.session.add(feeInsert)
    db.session.commit()
    return jsonify(['0'])

@app.route('/updatePayrollData', methods=['GET','POST'])
def updatePayrollData():
    teacherDetailRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()    
    teacher_id_list = request.form.getlist('teacher_id')    
    current_salary_list = request.form.getlist('currentSalaryInput')
    days_count_list = request.form.getlist('dayCountInput')
    days_present_list = request.form.getlist('days_present')
    calc_salary_list = request.form.getlist('calcSalaryInput')
    #paid_status_list = request.form.getlist('paid_status')
    has_changed_list = request.form.getlist('hasChanged')
    qmonth = request.form.get('qmonth')
    qyear = request.form.get('qyear')
    #print(teacher_id_list)
    #print(current_salary_list)
    #print(days_count_list)
    #print(days_present_list)
    #print(calc_salary_list)
    #print(has_changed_list)
    #print(qmonth)
    #print(qyear)
    ##print(paid_status_list)
    #print("#########")
    for i in range(len(has_changed_list)):
        print("This is the value of i "+ str(i))
        if has_changed_list[i]=='Y':   
            print ('Something has changed')
            #if (paid_status_list[i]):
            #    paidValue = 'Y'
            #else:
            #    paidValue='N'
            indivPayrollRecord = TeacherPayrollDetail.query.filter_by(teacher_id=teacher_id_list[i], month=qmonth, year=qyear).first()
            if indivPayrollRecord==None:
                print('Adding new values')
                payrollInsert=TeacherPayrollDetail(teacher_id=teacher_id_list[i],total_salary=current_salary_list[i],month=qmonth,
                    year=qyear,days_in_month=days_count_list[i],days_present = days_present_list[i], calc_salary = calc_salary_list[i], paid_status='Y',
                    last_modified_date=datetime.today(), school_id = teacherDetailRow.school_id)
                db.session.add(payrollInsert)
            else:
                if indivPayrollRecord.calc_salary!=calc_salary_list[i]:
                    print('Updating exiting values')
                    indivPayrollRecord.days_present = days_present_list[i]
                    indivPayrollRecord.calc_salary= calc_salary_list[i]
                    indivPayrollRecord.paid_status = 'Y'
                    indivPayrollRecord.last_modified_date = datetime.today()

    db.session.commit()
    return jsonify(['0'])

#End of section for payroll



@app.route('/bulkStudReg')
def bulkStudReg():
    return render_template('_bulkStudReg.html')


@app.route('/singleStudReg')
def singleStudReg():
    student_id = request.args.get('student_id')
    print('Inside single student Registration:'+str(student_id))
    if student_id=='':
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher_id.school_id).all()
        section_list=[(i.section,i.section) for i in available_section]
        form=SingleStudentRegistration()
        form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).order_by(ClassSection.class_val).all()]
        form.section.choices= section_list
        studentDetailRow = []
        guardianDetail1 = []
        guardianDetail2 =[]
        return render_template('_singleStudReg.html',form=form,student_id=student_id,studentDetailRow=studentDetailRow,guardianDetail1=guardianDetail1,guardianDetail2=guardianDetail2)
    else:
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher_id.school_id).all()
        section_list=[(i.section,i.section) for i in available_section]
        form=SingleStudentRegistration()
        form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).order_by(ClassSection.class_val).all()]
        form.section.choices= section_list
        guardianDetail2 = ''
        query = "select sp.first_name,sp.last_name,sp.profile_picture,md.description as gender,date(sp.dob) as dob,sp.phone,ad.address_1,ad.address_2,ad.locality,ad.city,ad.state,ad.country,ad.pin,cs.class_val,cs.section, sp.roll_number, sp.school_adm_number from student_profile sp "                 
        query = query + "inner join message_detail md on md.msg_id=sp.gender "
        query = query + "left join class_section cs on cs.class_sec_id=sp.class_sec_id " 
        query = query + "left join address_detail ad on ad.address_id=sp.address_id "
        query = query + "where sp.student_id='"+str(student_id)+"'"
        # query = query + "left join guardian_profile gp on gp.student_id=sp.student_id "
        # query = query + "inner join message_detail md2 on md2.msg_id=gp.relation where sp.student_id='"+str(student_id)+"'"
        studentDetailRow = db.session.execute(text(query)).first()
        queryGuardian1 = "select gp.guardian_id,gp.first_name,gp.last_name,gp.email,gp.phone,m1.description as relation from guardian_profile gp inner join message_detail m1 on m1.msg_id=gp.relation where student_id='"+str(student_id)+"'"
        guardianDetail1 = db.session.execute(text(queryGuardian1)).first()
        #print('Guardain Detail1 :')
        #print(guardianDetail1)
        guardianDetail2 = ''
        if guardianDetail1!=None:
            #print('If guardian Detail1 is not empty')
            queryGuardian2 = "select gp.guardian_id,gp.first_name,gp.last_name,gp.email,gp.phone,m1.description as relation from guardian_profile gp inner join message_detail m1 on m1.msg_id=gp.relation where student_id='"+str(student_id)+"' and guardian_id!='"+str(guardianDetail1.guardian_id)+"'"
            guardianDetail2 = db.session.execute(text(queryGuardian2)).first()
        # print(guardianDetail1)
        # print(guardianDetail2)
        #print('Name:'+str(studentDetailRow.first_name))
        #print('Gender:'+str(studentDetailRow.class_val))
        return render_template('_singleStudReg.html',form=form,student_id=student_id,studentDetailRow=studentDetailRow,guardianDetail1=guardianDetail1,guardianDetail2=guardianDetail2)


@app.route('/studentRegistration', methods=['GET','POST'])
@login_required
def studentRegistration(): 
    studId = request.args.get('student_id') 
    form=SingleStudentRegistration()
    if request.method=='POST':
        print('Inside Student Registration')
        if form.submit.data:            
            studentId = request.form['tag']
            print('Student Id:'+str(studentId))
            if studentId:                
                print('Inside Student update when student id is not empty')
                student_id = request.form['tag']
                teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
                class_sec=ClassSection.query.filter_by(class_val=str(form.class_val.data),section=form.section.data,school_id=teacher_id.school_id).first()
                gender=MessageDetails.query.filter_by(description=form.gender.data).first()
                address_id=Address.query.filter_by(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data).first()
                if address_id is None:
                    address_data=Address(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data,country=form.country.data)
                    db.session.add(address_data)
                    address_id=db.session.query(Address).filter_by(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data).first()
                studentDetails = StudentProfile.query.filter_by(student_id=student_id).first()
                studentClassSec = StudentClassSecDetail.query.filter_by(student_id=student_id).first()
                studProfile = "update student_profile set profile_picture='"+str(request.form['profile_image'])+"' where student_id='"+student_id+"'"
                #print('Query:'+str(studProfile))

                profileImg = db.session.execute(text(studProfile))
                #print(studentDetails)
                #if request.form['birthdate']:
                    #print('DOB:'+str(request.form['birthdate']))
                #print('Student id:'+str(student_id))
                #print('First Name:'+str(studentDetails.first_name))
                #print('Image url:'+str(request.form['profile_image']))
                studentDetails.first_name=form.first_name.data
                studentDetails.last_name=form.last_name.data
                studentDetails.gender=gender.msg_id
                if request.form['birthdate']=='':
                    studentDetails.dob=None
                else:
                    studentDetails.dob=request.form['birthdate']
                studentDetails.phone=form.phone.data
                studentDetails.address_id=address_id.address_id
                studentDetails.profile_image=request.form['profile_image']
                studentDetails.class_sec_id=class_sec.class_sec_id
                studentDetails.roll_number=int(form.roll_number.data)
                studentDetails.school_adm_number=form.school_admn_no.data
                studentDetails.full_name=form.first_name.data +" " + form.last_name.data
                if studentClassSec!=None and studentClassSec!="":
                    studentClassSec.class_sec_id = class_sec.class_sec_id
                    studentClassSec.class_val = str(form.class_val.data)
                    studentClassSec.section = form.section.data
                else:
                    studentClassSecAdd = StudentClassSecDetail(student_id=student_id, class_sec_id=class_sec.class_sec_id, 
                        class_val=str(form.class_val.data), section=form.section.data, is_current='Y', last_modified_date=datetime.today())
                    db.session.add(studentClassSecAdd)
                db.session.commit()
                first_name=request.form.getlist('guardian_first_name')
                last_name=request.form.getlist('guardian_last_name')
                phone=request.form.getlist('guardian_phone')
                email=request.form.getlist('guardian_email')
                relation=request.form.getlist('relation')
                gId = ''
                for i in range(len(first_name)):
                    if i==0:
                        relation_id=MessageDetails.query.filter_by(description=relation[i]).first()
                        # query = "select first_name,last_name,full_name,relation,email,phone from guardian_profile where student_id='"+str(student_id)+"' limit 1"
                        # guardianData = db.session.execute(text(query))
                        guardianData = GuardianProfile.query.filter_by(student_id=student_id).first()
                        # print('Query:'+query)
                        # print(guardianData.first_name)
                        if guardianData:
                            guardianData.first_name = first_name[i]
                            guardianData.last_name = last_name[i]
                            guardianData.full_name = first_name[i] + ' ' + last_name[i]
                            guardianData.relation = relation_id.msg_id
                            guardianData.phone = phone[i]
                            guardianData.email = email[i]
                            gId = guardianData.guardian_id
                            # gId = int(gId)+1 
                            print('Gid:'+str(guardianData.guardian_id))
                            print('Gid:'+str(gId))
                            print('Guardian First Name:'+str(first_name[i]))
                            db.session.commit()
                        else:
                            relation_id=MessageDetails.query.filter_by(description=relation[i]).first()
                            guardian_data=GuardianProfile(first_name=first_name[i],last_name=last_name[i],full_name=first_name[i] + ' ' + last_name[i],relation=relation_id.msg_id,
                            email=email[i],phone=phone[i],student_id=student_id)
                            db.session.add(guardian_data)    
                    if i==1:
                        query = "select *from guardian_profile where student_id='"+str(student_id)+"' and guardian_id!='"+str(gId)+"'"
                        print('Query:'+str(query))
                        guardian_id = db.session.execute(text(query)).first()
                        
                        if guardian_id:
                            guarId = guardian_id.guardian_id
                            relation_id=MessageDetails.query.filter_by(description=relation[i]).first()
                            guardianData = GuardianProfile.query.filter_by(student_id=student_id,guardian_id=guarId).first()
                            print('Second guardian first name:'+str(guardianData.first_name))
                            guardianData.first_name = first_name[i]
                            guardianData.last_name = last_name[i]
                            guardianData.full_name = first_name[i] + ' ' + last_name[i]
                            guardianData.relation = relation_id.msg_id
                            guardianData.phone = phone[i]
                            guardianData.email = email[i]
                            print(guardianData)
                            print('Second Guardian First Name:'+str(first_name[i]))
                        else:
                            relation_id=MessageDetails.query.filter_by(description=relation[i]).first()
                            guardian_data=GuardianProfile(first_name=first_name[i],last_name=last_name[i],full_name=first_name[i] + ' ' + last_name[i],relation=relation_id.msg_id,
                            email=email[i],phone=phone[i],student_id=student_id)
                            db.session.add(guardian_data)
                # guardian_data=GuardianProfile(first_name=first_name[i],last_name=last_name[i],full_name=first_name[i] + ' ' + last_name[i],relation=relation_id.msg_id,
                # email=email[i],phone=phone[i],student_id=student_data.student_id)
                db.session.commit()
                flash(Markup('Data Updated Successfully! Go to <a href="/studentProfile"> Student Directory</a>?'))
                return render_template('studentRegistration.html',studentId=student_id,user_type_val=str(current_user.user_type))


            else:
                print('Inside Student Registration when student id is empty')
                address_id=Address.query.filter_by(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data).first()
                if address_id is None:
                    address_data=Address(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data,country=form.country.data)
                    db.session.add(address_data)
                    address_id=db.session.query(Address).filter_by(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data).first()
                teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
                print('Print Form Data:'+form.section.data)
                
                class_sec=ClassSection.query.filter_by(class_val=str(form.class_val.data),section=form.section.data,school_id=teacher_id.school_id).first()
                gender=MessageDetails.query.filter_by(description=form.gender.data).first()
                print('Section Id:'+str(class_sec.class_sec_id))
                if request.form['birthdate']:
                    student=StudentProfile(first_name=form.first_name.data,last_name=form.last_name.data,full_name=form.first_name.data +" " + form.last_name.data,
                    school_id=teacher_id.school_id,class_sec_id=class_sec.class_sec_id,gender=gender.msg_id,
                    dob=request.form['birthdate'],phone=form.phone.data,profile_picture=request.form['profile_image'],address_id=address_id.address_id,school_adm_number=form.school_admn_no.data,
                    roll_number=int(form.roll_number.data))
                else:
                    student=StudentProfile(first_name=form.first_name.data,last_name=form.last_name.data,full_name=form.first_name.data +" " + form.last_name.data,
                    school_id=teacher_id.school_id,class_sec_id=class_sec.class_sec_id,gender=gender.msg_id,
                    phone=form.phone.data,profile_picture=request.form['profile_image'],address_id=address_id.address_id,school_adm_number=form.school_admn_no.data,
                    roll_number=int(form.roll_number.data))
                #print('Query:'+student)
                db.session.add(student)
                student_data=db.session.query(StudentProfile).filter_by(school_adm_number=form.school_admn_no.data).first()
                for i in range(4):
                    if i==0:
                        option='A'
                        qr_link='https:er5ft/api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + str(student_data.student_id) + '-' + form.roll_number.data + '-' + student_data.first_name + '@' + option
                    elif i==1:
                        option='B'
                        qr_link='https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + str(student_data.student_id) + '-' + form.roll_number.data + '-' + student_data.first_name + '@' + option
                    elif i==2:
                        option='C'
                        qr_link='https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + str(student_data.student_id) + '-' + form.roll_number.data + '-' + student_data.first_name + '@' + option
                    else:
                        option='D'
                        qr_link='https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + str(student_data.student_id) + '-' + form.roll_number.data + '-' + student_data.first_name + '@' + option
                    student_qr_data=studentQROptions(student_id=student_data.student_id,option=option,qr_link=qr_link)
                    db.session.add(student_qr_data)
                first_name=request.form.getlist('guardian_first_name')
                last_name=request.form.getlist('guardian_last_name')
                phone=request.form.getlist('guardian_phone')
                email=request.form.getlist('guardian_email')
                relation=request.form.getlist('relation')
                print('Insert into ClassSec table')
                student_class_sec = StudentClassSecDetail(student_id=student_data.student_id, class_sec_id=class_sec.class_sec_id,
                class_val=int(form.class_val.data), section=form.section.data, is_current='Y',last_modified_date=datetime.today()) 
                db.session.add(student_class_sec)
                for i in range(len(first_name)):
                    relation_id=MessageDetails.query.filter_by(description=relation[i]).first()
                    guardian_id = GuardianProfile.query.filter_by(email=email[i]).first()
                    if guardian_id:
                        print('If guardian already exist')
                        if guardian_id.student_id=='':
                            guardian_id.student_id = student_data.student_id
                            guardian_id.relation = relation_id.msg_id
                            print('If Id is empty')
                        else:
                            print('skip')
                            guardian_data=GuardianProfile(first_name=first_name[i],last_name=last_name[i],full_name=first_name[i] + ' ' + last_name[i],relation=relation_id.msg_id,
                            email=email[i],phone=phone[i],user_id=guardian_id.user_id,student_id=student_data.student_id)
                            db.session.add(guardian_data)
                    else:
                        guardian_data=GuardianProfile(first_name=first_name[i],last_name=last_name[i],full_name=first_name[i] + ' ' + last_name[i],relation=relation_id.msg_id,
                        email=email[i],phone=phone[i],student_id=student_data.student_id)
                        db.session.add(guardian_data)
                        print('If guardian does not exist')
                db.session.commit()
                flash('Successful upload !')
                return render_template('studentRegistration.html',user_type_val=str(current_user.user_type))

        else:
            teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
            print('School_id:'+str(teacher_id.school_id))
            csv_file=request.files['file-input']
            df1=pd.read_csv(csv_file)
            df1=df1.replace(np.nan, '', regex=True)
            print(df1)
            for index ,row in df1.iterrows():
                if row['first_name']=='' and row['gender']=='' and row['dob']=='' and row['phone'] and row['address_1'] and row['locality'] and row['city'] and row['state'] and row['country'] and row['pin'] and row['class_val'] and row['section'] and row['roll_number'] and row['school_adm_number'] and row['guardian1_first_name'] and row['guardian1_email'] and row['guardian1_phone'] and row['guardian1_relation']:
                    message = Markup("<h5>(a)Enter first name <br/>(b)Enter gender<br/> (c)Enter date of birth <br/> (d)Enter phone number<br/> (e)Enter address 1 <br/>(f)Enter locality<br/> (g)Enter city<br/> (h)Enter state <br/>(i)Enter country<br/>(j)Enter pin code<br/> (k)Enter class<br/> (l)Enter section<br/> (m)Enter roll number<br/> (n)Enter school admission number<br/>(o)Enter guardian first name<br/> (p)Enter guardian email<br/>(q)Enter guardian phone<br/> (r)Enter guardian relation </h5>")
                    flash(message)
                    return render_template('studentRegistration.html')
                address_data=Address(address_1=row['address_1'],address_2=row['address_2'],locality=row['locality'],city=row['city'],state=row['state'],pin=str(row['pin']),country=row['country'])
                db.session.add(address_data)
                address_id=db.session.query(Address).filter_by(address_1=row['address_1'],address_2=row['address_2'],locality=row['locality'],city=row['city'],state=row['state'],pin=str(row['pin']),country=row['country']).first()
                teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
                class_sec=ClassSection.query.filter_by(class_val=str(row['class_val']),section=row['section'],school_id=teacher_id.school_id).first()
                gender=MessageDetails.query.filter_by(description=row['gender']).first()
                date = row['dob']
                li = date.split('/',3)
                print('Date'+str(row['dob']))
                if int(li[1])>12 or int(li[0])>31:
                    flash('Invalid Date formate use dd/mm/yyyy')
                    return render_template('studentRegistration.html')
                if row['dob']!='':
                    date=dt.datetime.strptime(row['dob'], '%d/%m/%Y')
                else:
                    date=''
                student=StudentProfile(first_name=row['first_name'],last_name=row['last_name'],full_name=row['first_name'] +" " + row['last_name'],
                school_id=teacher_id.school_id,class_sec_id=class_sec.class_sec_id,gender=gender.msg_id,
                dob=date,phone=row['phone'],profile_picture=request.form['reference-url'+str(index+1)],address_id=address_id.address_id,school_adm_number=str(row['school_adm_number']),
                roll_number=int(row['roll_number']))
                db.session.add(student)
                student_data=db.session.query(StudentProfile).filter_by(school_adm_number=str(row['school_adm_number'])).first()
                print('Insert into ClassSec table')
                student_class_sec = StudentClassSecDetail(student_id=student_data.student_id, class_sec_id=class_sec.class_sec_id,
                class_val=str(row['class_val']), section=row['section'], is_current='Y',last_modified_date=datetime.today()) 
                db.session.add(student_class_sec)
                for i in range(4):
                    if i==0:
                        option='A'
                        qr_link='https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + str(student_data.student_id) + '-' + str(row['roll_number']) + '-' + student_data.first_name + '@' + option
                    elif i==1:
                        option='B'
                        qr_link='https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + str(student_data.student_id) + '-' + str(row['roll_number']) + '-' + student_data.first_name + '@' + option
                    elif i==2:
                        option='C'
                        qr_link='https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + str(student_data.student_id) + '-' + str(row['roll_number']) + '-' + student_data.first_name + '@' + option
                    else:
                        option='D'
                        qr_link='https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + str(student_data.student_id) + '-' + str(row['roll_number']) + '-' + student_data.first_name + '@' + option
                    student_qr_data=studentQROptions(student_id=student_data.student_id,option=option,qr_link=qr_link)
                    db.session.add(student_qr_data)
                for i in range(2):
                    relation_id=MessageDetails.query.filter_by(description=row['guardian'+str(i+1)+'_relation']).first()
                    print('Inside range')
                    if relation_id is not None:
                        print('If relation id is not empty')
                        guardian_data=GuardianProfile(first_name=row['guardian'+str(i+1)+'_first_name'],last_name=row['guardian'+str(i+1)+'_last_name'],full_name=row['guardian'+str(i+1)+'_first_name'] + ' ' + row['guardian'+str(i+1)+'_last_name'],relation=relation_id.msg_id,
                        email=row['guardian'+str(i+1)+'_email'],phone=row['guardian'+str(i+1)+'_phone'],student_id=student_data.student_id)
                    
                    db.session.add(guardian_data)
                    db.session.commit()
                
            
            flash('Successful upload !')
            return render_template('studentRegistration.html',user_type_val=str(current_user.user_type))
    if studId!='':
        print('inside if Student Id:'+str(studId))
        return render_template('studentRegistration.html',studentId=studId,user_type_val=str(current_user.user_type))
    return render_template('studentRegistration.html',user_type_val=str(current_user.user_type))


'''camera section'''

@app.route('/video_feed')
def video_feed(): 
    cam=VideoCamera()
    #cam.is_record=True
    return Response(cam.gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed_stop')
def video_feed_stop(): 
    #cam.is_record=False
    cam=VideoCamera()
    return Response(cam.closeCam())

'''camera section ends'''

'''new cam section'''


@app.route('/ScanBooks',methods=['GET', 'POST'])
def ScanBooks():
    print ("We're here!")
    return render_template('ScanBook.html',title='Scan Page')


@app.route('/testingOtherVideo',methods=['GET', 'POST'])
def testingOtherVideo():
    print ("We're here!")
    return render_template('testingOtherVideo.html',title='Test Page')

'''
'''
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    #teacher= TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #cityList()

    #cityJSON = json.dumps(cityList())
    #stateJSON = json.dumps(stateList())

    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():        
        current_user.about_me = form.about_me.data        
        current_user.first_name= form.first_name.data
        current_user.last_name= form.last_name.data                
        current_user.education = form.education.data
        current_user.experience = form.experience.data
        current_user.phone=form.phone.data
        #current_user.address=form.address.data
        current_user.city=form.city.data
        current_user.state=form.state.data
        current_user.resume=form.resume.data
        current_user.willing_to_travel = form.willing_to_travel.data
        ##
        db.session.commit()
        flash('Your changes have been saved')        
        if current_user.user_type==161:
            return redirect(url_for('openJobs'))

    elif request.method == 'GET':        
        form.about_me.data = current_user.about_me
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone
        form.education.data = current_user.education
        form.experience.data = current_user.experience
        #form.address.data = current_user.address
        form.city.data = current_user.city
        form.state.data = current_user.state
        form.resume.data = current_user.resume
        form.intro_link.data = current_user.intro_link
        
        print('Inside edit profile')
        print(current_user.about_me)
        print(current_user.first_name)
    return render_template(
        'edit_profile.html', title='Edit Profile', form=form,user_type_val=str(current_user.user_type), willing_to_travel=current_user.willing_to_travel)


@app.route('/index')
@app.route('/dashboard')
@login_required 
def index():
    #print('Inside index')
    #print("########This is the request url: "+str(request.url))
    user = User.query.filter_by(username=current_user.username).first_or_404()        
    school_name_val = schoolNameVal()
    #print('User Type Value:'+str(user.user_type))
    teacher_id = TeacherProfile.query.filter_by(user_id=user.id).first() 
    
    school_id = SchoolProfile.query.filter_by(school_name=school_name_val).first()
    
    if user.user_type==71:
        classExist = ClassSection.query.filter_by(school_id=school_id.school_id).first()
        #print('Insert new school')
        #print(classExist)
        if classExist==None:
            fromSchoolRegistration = True
       
            subjectValues = MessageDetails.query.filter_by(category='Subject').all()
            board = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
            boardRows = MessageDetails.query.filter_by(msg_id=board.board_id).first()
            school_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
            classValues = "SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id = '"+str(teacher_id.school_id)+"' GROUP BY class_val order by s"
            classValues = db.session.execute(text(classValues)).fetchall()
            classValuesGeneral = "SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs GROUP BY class_val order by s"
            classValuesGeneral = db.session.execute(text(classValuesGeneral)).fetchall()
            subjectValues = MessageDetails.query.filter_by(category='Subject').all()
            bookName = BookDetails.query.all()
            chapterNum = Topic.query.distinct().all()
            topicId = Topic.query.all()
            generalBoardId = SchoolProfile.query.filter_by(school_id = teacher_id.school_id).first()
            #print('teacher and board ids')
            #print(teacher_id.school_id)
            #print(generalBoardId.board_id)
            generalBoard = MessageDetails.query.filter_by(msg_id=generalBoardId.board_id).first()
            fromSchoolRegistration = True
            return render_template('syllabus.html',generalBoard=generalBoard,boardRowsId = boardRows.msg_id , boardRows=boardRows.description,subjectValues=subjectValues,school_name=school_id.school_name,classValues=classValues,classValuesGeneral=classValuesGeneral,bookName=bookName,chapterNum=chapterNum,topicId=topicId,fromSchoolRegistration=fromSchoolRegistration)
    #if user.user_type==135:
    #    return redirect(url_for('admin'))
    if user.user_type==234:
    #or ("prep.alllearn" in str(request.url)) or ("alllearnprep" in str(request.url))
        return redirect(url_for('practiceTest'))
    if user.user_type==72:
        #print('Inside guardian')
        return redirect(url_for('disconnectedAccount'))
    if user.user_type=='161':
        return redirect(url_for('openJobs'))
    if user.user_type==134 and user.access_status==145:        
        return redirect(url_for('disconnectedAccount'))

    teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
    classSecCheckVal = classSecCheck()

    if school_name_val ==None:
        #print('did we reach here')
        return redirect(url_for('disconnectedAccount'))
    else:
    #####Fetch school perf graph information##########
        performanceQuery = "select * from fn_class_performance("+str(teacher.school_id)+") order by perf_date"
        performanceRows = db.session.execute(text(performanceQuery)).fetchall()
        if len(performanceRows)>0:
            df = pd.DataFrame( [[ij for ij in i] for i in performanceRows])
            df.rename(columns={0: 'Date', 1: 'Class_1', 2: 'Class_2', 3: 'Class_3', 4:'Class_4',
                5:'Class_5', 6:'Class_6', 7:'Class_7', 8:'Class_8', 9:'Class_9', 10:'Class_10'}, inplace=True)
            #print(df)
            dateRange = list(df['Date'])
            class1Data= list(df['Class_1'])
            class2Data= list(df['Class_2'])
            class3Data= list(df['Class_3'])
            class4Data= list(df['Class_4'])
            class5Data= list(df['Class_5'])
            class6Data= list(df['Class_6'])
            class7Data= list(df['Class_7'])
            class8Data= list(df['Class_8'])
            class9Data= list(df['Class_9'])
            class10Data= list(df['Class_10'])
            #print(dateRange)
            ##Class 1
            graphData = [dict(
                data1=[dict(y=class1Data,x=dateRange,type='scatter', name='Class 1')],
                data2=[dict(y=class2Data,x=dateRange,type='scatter', name='Class 2')],
                data3=[dict(y=class3Data,x=dateRange,type='scatter', name='Class 3')],
                data4=[dict(y=class4Data,x=dateRange,type='scatter', name='Class 4')],
                data5=[dict(y=class5Data,x=dateRange,type='scatter', name='Class 5')],
                data6=[dict(y=class6Data,x=dateRange,type='scatter', name='Class 6')],
                data7=[dict(y=class7Data,x=dateRange,type='scatter', name='Class 7')],
                data8=[dict(y=class8Data,x=dateRange,type='scatter', name='Class 8')],
                data9=[dict(y=class9Data,x=dateRange,type='scatter', name='Class 9')],
                data10=[dict(y=class10Data,x=dateRange,type='scatter', name='Class 10')]
                )]        
            #print(graphData)

            graphJSON = json.dumps(graphData, cls=plotly.utils.PlotlyJSONEncoder)
        else:
            graphJSON="1"
    #####Fetch Top Students infor##########        
        # topStudentsQuery = "select *from fn_monthly_top_students("+str(teacher.school_id)+",8)"
        qclass_val = 'dashboard'
        topStudentsRows = ''
        leaderBoardData = leaderboardContent(qclass_val)
        # print('leaderBoard Data:'+str(leaderBoardData))
        # Convert dataframe to a list
        data = []
        #print(type(leaderBoardData))
        column_names = ["a", "b", "c"]
        datafr = pd.DataFrame(columns = column_names)
        if type(leaderBoardData)==type(datafr):
            #print('if data is not empty')
            df1 = leaderBoardData[['studentid','profile_pic','student_name','class_val','section','total_marks%','total_tests']]
            df2 = leaderBoardData.drop(['profile_pic', 'student_name','class_val','section','total_marks%','total_tests'], axis=1)
            leaderBoard = pd.merge(df1,df2,on=('studentid'))
                
            d = leaderBoard[['studentid','profile_pic','student_name','class_val','section','total_marks%','total_tests']]
            df3 = leaderBoard.drop(['studentid'],axis=1)
            
            df1.rename(columns = {'profile_pic':'Profile Picture'}, inplace = True)
            df1.rename(columns = {'student_name':'Student'}, inplace = True)
            df1.rename(columns = {'class_val':'Class'}, inplace = True)
            df1.rename(columns = {'section':'Section'}, inplace = True)
            df1.rename(columns = {'total_marks%':'Total Marks'}, inplace = True)
            df1.rename(columns = {'total_tests':'Total Tests'}, inplace = True)
            header = [df1.columns.values.tolist()]
            headerAll = [df3.columns.values.tolist()]
            colAll = ''
            subjHeader = [df2.columns.values.tolist()]
            columnNames = ''
            col = ''
            subColumn = ''
            for subhead in subjHeader:
                subColumn = subhead
            for h in header:
                columnNames = h
            for headAll in headerAll: 
                colAll = headAll
            n= int(len(subColumn)/2)
            ndf = df2.drop(['studentid'],axis=1)
            newDF = ndf.iloc[:,0:n]
            new1DF = ndf.iloc[:,n:]
                
            df5 = pd.concat([newDF, new1DF], axis=1)
            DFW = df5[list(sum(zip(newDF.columns, new1DF.columns), ()))]
            
            
            dat = pd.concat([d,DFW], axis=1)
                
            dat = dat.sort_values('total_marks%',ascending=False)  
            
            subHeader = ''
            i=1
            for row in dat.values.tolist():
                if i<9:
                    data.append(row)
                i=i+1
        form  = promoteStudentForm() 
        available_class=ClassSection.query.with_entities(ClassSection.class_val,ClassSection.section).distinct().order_by(ClassSection.class_val,ClassSection.section).filter_by(school_id=teacher.school_id).all()
        class_list=[(str(i.class_val)+"-"+str(i.section),str(i.class_val)+"-"+str(i.section)) for i in available_class]
        
        form.class_section1.choices = class_list 
        form.class_section2.choices = class_list 
        
        EventDetailRows = EventDetail.query.filter_by(school_id=teacher.school_id).all()
    #####Fetch Course Completion infor##########    
        topicToCoverQuery = "select *from fn_topic_tracker_overall("+str(teacher.school_id)+") order by class, section"
        topicToCoverDetails = db.session.execute(text(topicToCoverQuery)).fetchall()
        #print(topicToCoverDetails)

    ##################Fetch Job post details################################
        jobPosts = JobDetail.query.filter_by(school_id=teacher.school_id).order_by(JobDetail.posted_on.desc()).all()
        teacherCount = "select count(*) from teacher_profile tp where school_id = '"+str(teacher.school_id)+"'"
        teacherCount = db.session.execute(teacherCount).first()
        studentCount = "select count(*) from student_profile sp where school_id = '"+str(teacher.school_id)+"'"
        studentCount = db.session.execute(studentCount).first()
        testCount = "select (select count(distinct upload_id) from result_upload ru where school_id = '"+str(teacher.school_id)+"') + "
        testCount = testCount + "(select count(distinct resp_session_id) from response_capture rc2 where school_id = '"+str(teacher.school_id)+"') as SumCount"
        #print(testCount)
        testCount = db.session.execute(testCount).first()
        lastWeekTestCount = "select (select count(distinct upload_id) from result_upload ru where school_id = '"+str(teacher.school_id)+"' and last_modified_date >=current_date - 7) + "
        lastWeekTestCount = lastWeekTestCount + "(select count(distinct resp_session_id) from response_capture rc2 where school_id = '"+str(teacher.school_id)+"' and last_modified_date >=current_date - 7) as SumCount "
        #print(lastWeekTestCount)
        lastWeekTestCount = db.session.execute(lastWeekTestCount).first()
        #print('user type value')
        #print(session['moduleDet'])
        query = "select user_type,md.module_name,description, module_url from module_detail md inner join module_access ma on md.module_id = ma.module_id where user_type = '"+str(current_user.user_type)+"'"
        moduleDetRow = db.session.execute(query).fetchall()
        return render_template('dashboard.html',form=form,title='Home Page',school_id=teacher.school_id, jobPosts=jobPosts,
            graphJSON=graphJSON, classSecCheckVal=classSecCheckVal,topicToCoverDetails = topicToCoverDetails, EventDetailRows = EventDetailRows, topStudentsRows = data,teacherCount=teacherCount,studentCount=studentCount,testCount=testCount,lastWeekTestCount=lastWeekTestCount)

@app.route('/performanceChart',methods=['GET','POST'])
def performanceChart():
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    query = "Select * from fn_overall_performance_summary('"+str(teacher_id.school_id)+"') where class='All'and section='All' and subject='All'"
    
    resultSet = db.session.execute(text(query)).fetchall()
    
    resultArray = []
    if resultSet:
        for result in resultSet:
            Array = {}
            Array['avg_score'] = str(round(result.avg_score,2))
            Array['highest_mark'] = str(result.highest_mark)
            Array['lowest_mark'] = str(result.lowest_mark)
            Array['no_of_students_above_90'] = str(result.no_of_students_above_90)
            Array['no_of_students_80_90'] = str(result.no_of_students_80_90)
            Array['no_of_students_70_80'] = str(result.no_of_students_70_80)
            Array['no_of_students_50_70'] = str(result.no_of_students_50_70)
            Array['no_of_students_below_50'] = str(result.no_of_students_below_50)
            Array['no_of_students_cross_50'] = str(result.no_of_students_cross_50)
            resultArray.append(Array)
        return {'result' : resultArray} 
    else:
        return jsonify(["NA"])

@app.route('/performanceBarChart',methods=['GET','POST'])
def performanceBarChart():
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_v = request.args.get('class_val')
    section = request.args.get('section')
    classSection = ClassSection.query.with_entities(ClassSection.class_sec_id).filter_by(class_val=class_v,section=section,school_id=str(teacher_id.school_id)).first()
    subject = "select distinct subject_id from topic_detail where class_val= '"+str(class_v)+"'"
    totalStudent = "select count(*) from student_profile where class_sec_id='"+str(classSection.class_sec_id)+"' and school_id='"+str(teacher_id.school_id)+"'"
    #print(totalStudent)
    totalStudent = db.session.execute(totalStudent).first()
    subject_id = db.session.execute(subject).fetchall()
    performance_array = []
    for sub in subject_id:
        pass_count = "select count(*) from student_profile sp where student_id in (select studentid from fn_performance_leaderboard_detail_v1('"+str(teacher_id.school_id)+"') pd where class ='"+str(class_v)+"' and section='"+str(section)+"' and subjectid='"+str(sub.subject_id)+"' and marks>50)"
        fail_count = "select count(*) from student_profile sp where student_id in (select studentid from fn_performance_leaderboard_detail_v1('"+str(teacher_id.school_id)+"') pd where class ='"+str(class_v)+"' and section='"+str(section)+"' and subjectid='"+str(sub.subject_id)+"' and marks<=50)"
        #print('pass and fail count:')
        #print(pass_count)
        #print(fail_count)
        passStudents = db.session.execute(pass_count).first()
        failStudents = db.session.execute(fail_count).first()
        presentStudents = passStudents[0] + failStudents[0]
        absentStudents = totalStudent[0] - presentStudents
        #print(absentStudents)
        if absentStudents==totalStudent[0]:
            absentStudents = 0
        #print((passStudents[0]))
        #print((failStudents[0]))
        Array = {}
        Array['pass_count'] = str(passStudents[0])
        Array['fail_count'] = str(failStudents[0])
        Array['absent_students'] = str(absentStudents)
        subjectName = MessageDetails.query.with_entities(MessageDetails.description).filter_by(msg_id=sub.subject_id).first()
        Array['description'] = str(subjectName.description)
        performance_array.append(Array)
    return {'performance':performance_array}
    
    

@app.route('/disconnectedAccount')
@login_required
def disconnectedAccount():    
    print('Inside disconnected Account')
    userDetailRow=User.query.filter_by(username=current_user.username).first()
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()

    #added under the change for practice test module
    boardRows = MessageDetails.query.with_entities(MessageDetails.description).distinct().filter_by(category='Board').all()
    classRows = BoardClassSubject.query.with_entities(BoardClassSubject.class_val).distinct().order_by(BoardClassSubject.class_val.desc()).all()

    if userDetailRow.user_type==72:
        print('Inside Guardian condition')
        return redirect(url_for('guardianDashboard'))
    if teacher==None and userDetailRow.user_type!=161 and userDetailRow.user_type!=134:
        return render_template('disconnectedAccount.html', title='Disconnected Account', disconn = 1, userDetailRow=userDetailRow, boardRows=boardRows,classRows=classRows)
    elif userDetailRow.user_type==161:
        return redirect(url_for('openJobs'))
    elif userDetailRow.user_type==134 and userDetailRow.access_status==145:
        return redirect(url_for('qrSessionScannerStudent'))
    else:
        print('Inside else')
        return redirect(url_for('index'))




@app.route('/postJob',methods=['POST','GET'])
@login_required
def postJob():
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    schoolCityQuery = "select city from address_detail where address_id =(select address_id from school_profile where school_id ="+str(teacherRow.school_id)+")"
    schoolCity = db.session.execute(text(schoolCityQuery)).first()
    form = postJobForm()
    
    availableCategories=MessageDetails.query.filter_by(category='Job Category').all()
    availableJobTypes=MessageDetails.query.filter_by(category='Job Type').all()
    availableStayOptions=MessageDetails.query.filter_by(category='Stay Option').all()
    availableFoodOptions=MessageDetails.query.filter_by(category='Food Option').all()
    availableTeachingTermOption=MessageDetails.query.filter_by(category='Teaching Term Option').all()

    form.category.choices = [(str(i.description),str(i.description)) for i in availableCategories]
    form.job_type.choices = [(str(i.description),str(i.description)) for i in availableJobTypes]
    form.stay.choices = [(str(i.description),str(i.description)) for i in availableStayOptions]
    form.food.choices = [(str(i.description),str(i.description)) for i in availableFoodOptions]
    form.term.choices = [(str(i.description),str(i.description)) for i in availableTeachingTermOption]


    if request.method == 'POST' and form.validate():
        jobData=JobDetail(category=form.category.data,
            posted_by =teacherRow.teacher_id,school_id=teacherRow.school_id,description=form.description.data,min_pay=form.min_pay.data,max_pay=form.max_pay.data,
            start_date=form.start_date.data,subject=form.subject.data, 
            classes= form.classes.data, language= form.language.data,timings= form.timings.data,stay= form.stay.data, 
            fooding= form.food.data,term= form.term.data,status='Open',num_of_openings=form.num_of_openings.data,city =schoolCity.city,
            job_type =form.job_type.data,posted_on = datetime.today(),last_modified_date= datetime.today())
        db.session.add(jobData)
        db.session.commit()
        flash('New job posted created!')
        try:
            job_posted_email(teacherRow.email,teacherRow.teacher_name,form.category.data)
        except:
            pass
    else:
        #flash('Please fix the errors to submit')
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                print(err)
    return render_template('postJob.html',title='Post Job',form=form,classSecCheckVal=classSecCheck())


@app.route('/openJobs')
def openJobs():
    page=request.args.get('page',0, type=int)    
    first_login = request.args.get('first_login','0').strip()
    jobTermOptions = MessageDetails.query.filter_by(category='Teaching Term Option').all()
    jobTypeOptions = MessageDetails.query.filter_by(category='Job Type').all()
    # print('User value in openJobs:'+str(user_type_val))
    if first_login=='1':
        
        print('this is the first login section')
        userRecord = User.query.filter_by(id=current_user.id).first() 
        userRecord.user_type= '161'
        db.session.commit()
        flash('Please complete your profile before applying for jobs')
        return redirect('edit_profile')
    else:
        print('first login not registered')
        if current_user.is_anonymous:
            return render_template('openJobs.html',title='Look for Jobs',first_login=first_login,jobTermOptions=jobTermOptions,jobTypeOptions=jobTypeOptions)
        else:
            return render_template('openJobs.html',title='Look for Jobs',first_login=first_login,jobTermOptions=jobTermOptions,jobTypeOptions=jobTypeOptions,user_type_val=str(current_user.user_type))


@app.route('/openJobsFilteredList')
def openJobsFilteredList():
    page=request.args.get('page',0, type=int)
    recordsOnPage = 5
    offsetVal = page *recordsOnPage
    
    whereClause = ""
    qjob_term = request.args.get('job_term') #all /short term / long term
    qjob_type = request.args.get('job_type') #all /part time/ full time
    qcity =  request.args.get('city')       # all/ home city
   
    print("qterm is "+str(qjob_term))
    print("qtype is "+str(qjob_type))
    print("qcity is "+str(qcity))

    whJobTerm=''
    whJobType=''
    whCity=''

    if qjob_term=='All' or qjob_term==None or qjob_term=='':
        whJobTerm=None
    else:
        whJobTerm=" t1.term=\'"+str(qjob_term)+"\'"
        whereClause = 'where ' + whJobTerm

    
    if qjob_type=='All' or qjob_type==None or qjob_type=='':
        whJobType=None
    else:
        whJobType=" t1.job_type=\'"+str(qjob_type)+"\'"
        if whereClause=='':
            whereClause = 'where '+whJobType
        else:
            whereClause =  whereClause + ' and '+whJobType
    
    if qcity=='All' or qcity==None or qcity=='':
        whCity=None
    else:
        whCity=" t1.city=\'"+ str(qcity)+"\'"
        if whereClause=='':
            whereClause = 'where '+whCity
        else:
            whereClause = whereClause + ' and '+whCity
    
    print('this is the where clause' + whereClause)
    #if whJobTerm!=None and whJobType!=None and whCity!=None:
    #    whereClause = "where " + whJobTerm + "and "+whJobType + "and "+whCity


    #teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    openJobsQuery = "select school_picture, school_name, t2.school_id, min_pay, max_pay, t1.city, t1.category, t1.job_type,t1.term, t1.subject,t1.posted_on, t1.job_id "
    openJobsQuery = openJobsQuery + "from job_detail t1 inner join school_profile t2 on t1.school_id=t2.school_id and t1.status='Open' " + whereClause 
    openJobsQuery = openJobsQuery + " order by t1.posted_on desc "
    #openJobsQuery = openJobsQuery +" OFFSET "+str(offsetVal)+" ROWS FETCH FIRST "+str(recordsOnPage)+" ROW ONLY; "
    #openJobsDataRows = db.session.execute(text(openJobsQuery)).fetchall()    
    openJobsDataRows = db.session.execute(text(openJobsQuery)).fetchall()
    
    if len(openJobsDataRows)==0:
        print('returning 1')
        return jsonify(['1'])
    else:
        next_page=page+1

        if page!=0:
            prev_page=page-1
        else:
            prev_page=None

        prev_url=None
        next_url=None


        if len(openJobsDataRows)==recordsOnPage:
            next_url = url_for('openJobsFilteredList', page = next_page,job_term=qjob_term, job_type=qjob_type,city=qcity)
            prev_url = url_for('openJobsFilteredList', page=prev_page,job_term=qjob_term, job_type=qjob_type,city=qcity)
        elif len(openJobsDataRows)<recordsOnPage:
            next_url = None
            if prev_page!=None:
                prev_url = url_for('openJobsFilteredList', page=prev_page,job_term=qjob_term, job_type=qjob_type,city=qcity)
            else:
                prev_url==None
        else:
            next_url=None
            prev_url=None
        return render_template('_jobList.html',openJobsDataRows=openJobsDataRows,next_url=next_url, prev_url=prev_url)



@app.route('/jobDetail')

def jobDetail():
    job_id = request.args.get('job_id')
    school_id=request.args.get('school_id')  
    #teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()    
    schoolProfileRow = SchoolProfile.query.filter_by(school_id =school_id).first()
    addressRow = Address.query.filter_by(address_id = schoolProfileRow.address_id).first()    
    jobDetailRow = JobDetail.query.filter_by(job_id=job_id).first()
    if current_user.is_anonymous:
        print('user Anonymous')
        jobApplicationRow = ''
    else:
        print('user exist')
        jobApplicationRow = JobApplication.query.filter_by(job_id=job_id, applier_user_id=current_user.id).first()
    if jobApplicationRow:
        applied=1
    else:
        applied=0
    if current_user.is_anonymous:
        return render_template('jobDetail.html', title='Job Detail', 
            schoolProfileRow=schoolProfileRow,addressRow=addressRow,jobDetailRow=jobDetailRow,applied=applied)
    else:
        return render_template('jobDetail.html', title='Job Detail', 
            schoolProfileRow=schoolProfileRow,addressRow=addressRow,jobDetailRow=jobDetailRow,applied=applied,user_type_val=str(current_user.user_type))
    



@app.route('/sendJobApplication',methods=['POST','GET'])
@login_required
def sendJobApplication():
    print('We are in the right place')    
    if request.method=='POST':
        job_id_form = request.form.get('job_id_form')
        available_from=request.form.get("availableFromID")
        available_till=request.form.get("availableTillID")
        if available_from=='':
            available_from=None
        if available_till=='':
            available_till=None
        school_id=request.form.get("school_id")
        #teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        jobApplyData=JobApplication(applier_user_id=current_user.id, job_id=job_id_form,
                applied_on =datetime.today(),status='Applied',school_id=school_id,available_from=available_from,available_till=available_till,
                last_modified_date=date.today())
        db.session.add(jobApplyData)
        db.session.commit()
        flash('Job application submitted!')
        #try:            
        jobDetailRow = JobDetail.query.filter_by(job_id=job_id_form).first()
        teacherRow = TeacherProfile.query.filter_by(teacher_id=jobDetailRow.posted_by).first()
        new_applicant_for_job(teacherRow.email,teacherRow.teacher_name,current_user.first_name + ' '+current_user.last_name,jobDetailRow.category)
        #except:
        #    pass
        return redirect(url_for('openJobs'))

@app.route('/appliedJobs')  # this page shows all the job posts that the user has applied to
@login_required
def appliedJobs():
    appliedQuery = "select applied_on, t3.school_id,school_name, category, subject, t2.job_id, "
    appliedQuery = appliedQuery + "t1.status as application_status, t2.status as job_status "
    appliedQuery = appliedQuery + "from job_application t1 inner join job_detail t2 on "
    appliedQuery = appliedQuery + "t1.job_id=t2.job_id inner join school_profile t3 on "
    appliedQuery = appliedQuery + "t3.school_id=t1.school_id where t1.applier_user_id='"+str(current_user.id)+"'"
    appliedRows = db.session.execute(text(appliedQuery)).fetchall()
    return render_template('appliedJobs.html',title='Applied jobs', user_type_val=str(current_user.user_type),appliedRows=appliedRows)


@app.route('/jobApplications')  # this page shows all the applications received by the job poster for any specifc job post
@login_required
def jobApplications():
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    job_id=request.args.get('job_id')
    #jobApplications = JobApplication.query.filter_by(school_id=teacher.school_id).order_by(JobApplication.applied_on.desc()).all()
    #pending descision
    jobAppQuery = "select t1.applied_on, t2.first_name, t2.last_name, t2.username,t1.applier_user_id,t1.job_id, "
    jobAppQuery=jobAppQuery+"t2.city, t1.available_from, t1.available_till, t2.education, t2.experience from "
    jobAppQuery=jobAppQuery+"job_application t1 inner join public.user t2 on t1.applier_user_id=t2.id inner join job_detail t3 on "
    jobAppQuery=jobAppQuery+" t3.job_id=t1.job_id and t3.school_id='"+str(teacher.school_id)+"' and t1.job_id='"+str(job_id)+"' and t1.status='Applied' order by applied_on desc"
    jobApplications = db.session.execute(text(jobAppQuery)).fetchall()

    #hired descision
    jobAppQueryHired = "select t1.applied_on, t2.first_name, t2.last_name, t2.username,t1.applier_user_id, t1.job_id, "
    jobAppQueryHired=jobAppQueryHired+"t2.city, t1.available_from, t1.available_till, t2.education, t2.experience from "
    jobAppQueryHired=jobAppQueryHired+"job_application t1 inner join public.user t2 on t1.applier_user_id=t2.id inner join job_detail t3 on "
    jobAppQueryHired=jobAppQueryHired+" t3.job_id=t1.job_id and t3.school_id='"+str(teacher.school_id)+"' and t1.job_id='"+str(job_id)+"' and t1.status='Hired' order by applied_on desc"
    jobApplicationsHired = db.session.execute(text(jobAppQueryHired)).fetchall()

    #shortlist descision
    jobAppQueryShortlisted = "select t1.applied_on, t2.first_name, t2.last_name, t2.username,t1.applier_user_id, t1.job_id, "
    jobAppQueryShortlisted=jobAppQueryShortlisted+"t2.city, t1.available_from, t1.available_till, t2.education, t2.experience from "
    jobAppQueryShortlisted=jobAppQueryShortlisted+"job_application t1 inner join public.user t2 on t1.applier_user_id=t2.id inner join job_detail t3 on "
    jobAppQueryShortlisted=jobAppQueryShortlisted+" t3.job_id=t1.job_id and t3.school_id='"+str(teacher.school_id)+"' and t1.job_id='"+str(job_id)+"' and t1.status='Shortlisted' order by applied_on desc"
    jobApplicationsShortlisted = db.session.execute(text(jobAppQueryShortlisted)).fetchall()

    #rejected descision
    jobAppQueryRejected = "select t1.applied_on, t2.first_name, t2.last_name, t2.username,t1.applier_user_id, t1.job_id, "
    jobAppQueryRejected=jobAppQueryRejected+"t2.city, t1.available_from, t1.available_till, t2.education, t2.experience from "
    jobAppQueryRejected=jobAppQueryRejected+"job_application t1 inner join public.user t2 on t1.applier_user_id=t2.id inner join job_detail t3 on "
    jobAppQueryRejected=jobAppQueryRejected+" t3.job_id=t1.job_id and t3.school_id='"+str(teacher.school_id)+"' and t1.job_id='"+str(job_id)+"' and t1.status='Rejected' order by applied_on desc"
    jobApplicationsRejected = db.session.execute(text(jobAppQueryRejected)).fetchall()
    
    return render_template('jobApplications.html', classSecCheckVal=classSecCheck(),title='Job Applications',jobApplications=jobApplications, jobApplicationsHired=jobApplicationsHired,jobApplicationsShortlisted= jobApplicationsShortlisted, jobApplicationsRejected = jobApplicationsRejected )


@app.route('/jobPosts')
@login_required
def jobPosts():
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    jobPosts = JobDetail.query.filter_by(school_id=teacher.school_id).order_by(JobDetail.posted_on.desc()).all()
    return render_template('jobPosts.html',jobPosts=jobPosts, classSecCheckVal=classSecCheck(),school_id=teacher.school_id)

@app.route('/processApplication')
@login_required
def processApplication():
    applier_user_id = request.args.get('applier_user_id')
    job_id = request.args.get('job_id')
    process_type = request.args.get('process_type')
    #try:
    jobApplicationRow = JobApplication.query.filter_by(applier_user_id=applier_user_id, job_id=job_id).first()
    jobDetailRow = JobDetail.query.filter_by(job_id=job_id).first()
    applierRow = User.query.filter_by(id=applier_user_id).first()
    schoolRow = SchoolProfile.query.filter_by(school_id=jobApplicationRow.school_id).first()

    print(process_type)
    if process_type=='shortlist':
        jobApplicationRow.status= 'Shortlisted'
        flash('Application Shortlisted')
        try:
            application_processed(applierRow.email,applierRow.first_name + ' '+ applierRow.last_name, schoolRow.school_name,jobDetailRow.category, 'Shortlisted')
        except:
            pass
    elif process_type=='reject':
        jobApplicationRow.status= 'Rejected'
        flash('Application Rejected')
        try:
            application_processed(applierRow.email,applierRow.first_name + ' '+ applierRow.last_name, schoolRow.school_name,jobDetailRow.category, 'Rejected')
        except:
            pass
    elif process_type =='hire':
        jobApplicationRow.status= 'Hired'
        flash('Application Hired')
        try:
            application_processed(applierRow.email,applierRow.first_name + ' '+ applierRow.last_name, schoolRow.school_name,jobDetailRow.category, 'Hired')
        except:
            pass
    else:
        flash('Error processing application idk')
    db.session.commit()
    
    return redirect(url_for('jobApplications',job_id=job_id))
    #except:
    flash('Error processing application')
    return redirect(url_for('jobApplications',job_id=job_id))


@app.route('/submitPost', methods=['GET', 'POST'])
@login_required
def submitPost():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('submitPost'))
    posts = [{
        'author': {
            'username': 'John'
        },
        'body': 'Beautiful day in Portland!'
    }, {
        'author': {
            'username': 'Susan'
        },
        'body': 'The Avengers movie was so cool!'
    }]
    return render_template(
        "submitPost.html", title='Submit Post', form=form, posts=posts)


@app.route('/explore')
@login_required
def explore():
    #page=request.args.get('page',1, type=int)
    #posts = Post.query.order_by(Post.timestamp.desc()).paginate(page,app.config['POSTS_PER_PAGE'],False)
     #next_url = url_for('explore', page=posts.next_num) \
        #if posts.has_next else None
    #prev_url = url_for('explore', page=posts.prev_num) \
        #if posts.has_prev else None
        #return render_template("index.html", title='Explore', posts=posts.items,
         #                 next_url=next_url, prev_url=prev_url)
    posts = [{
        'author': {
            'username': 'John'
        },
        'body': 'Beautiful day in Portland!'
    }, {
        'author': {
            'username': 'Susan'
        },
        'body': 'The Avengers movie was so cool!'
    }]

    return render_template('explore.html', title='Explore', posts=posts)


#new section for liveClass

@app.route('/archiveLiveClass')
@login_required
def archiveLiveClass():
    live_class_id=request.args.get('live_class_id')
    try:
        liveClassVal = LiveClass.query.filter_by(live_class_id=live_class_id,is_archived='N').first()
        liveClassVal.is_archived='Y'
        db.session.commit()
        return jsonify(['0'])
    except:
        return jsonify(['1'])



@app.route('/liveClass', methods=['GET','POST'])
@login_required
def liveClass():    
    form = AddLiveClassForm()
    #allLiveClasses = LiveClass.query.filter_by(is_archived='N').order_by(LiveClass.last_modified_date.desc()).all()
    if current_user.user_type==71 or current_user.user_type==135 or current_user.user_type==139:
        teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
        school_id = teacherData.school_id 
        studentDetails=""
    elif current_user.user_type==134:
        #studentData = StudentProfile.query.filter_by(user_id=current_user.id).first()  
        studentDetails = StudentProfile.query.filter_by(user_id=current_user.id).first()       
        school_id = studentDetails.school_id
    else:        
        return redirect(url_for('index'))

    print('##########Data:'+str(school_id))
    allLiveClassQuery = "select t1.class_sec_id, t2.class_val, t2.section "
    allLiveClassQuery = allLiveClassQuery + ", t1.subject_id, t3.description as subject, t1.topic_id, t4.topic_name, start_time,end_time, status, teacher_name, "
    allLiveClassQuery = allLiveClassQuery + " conf_link, t1.school_id "
    allLiveClassQuery = allLiveClassQuery + " from live_class t1 "
    allLiveClassQuery = allLiveClassQuery+ " inner join class_section t2 on t1.class_sec_id = t2.class_sec_id "
    allLiveClassQuery= allLiveClassQuery + " inner join message_detail t3 on t1.subject_id = t3.msg_id "
    allLiveClassQuery= allLiveClassQuery + " inner join topic_detail t4 on t1.topic_id = t4.topic_id where t1.school_id= " +str(school_id) 
    allLiveClassQuery= allLiveClassQuery + " and end_time > now() order by end_time desc"
    
    try:
        allLiveClasses = db.session.execute(allLiveClassQuery).fetchall()
        print('##########Data:'+str(allLiveClasses))
    except:
        allLiveClasses = ""

    #if request.method == 'POST':
    #    schoolNameRow = SchoolProfile.query.filter_by(school_id=current_user.school_id).first()
    #    liveClassData=LiveClass(class_val = form.class_val.data,subject = form.subject.data, book_chapter=form.book_chapter.data, 
    #        start_time = form.start_time.data, end_time = form.end_time.data, status = "Active", teacher_id=current_user.id, 
    #        teacher_name = str(current_user.first_name)+' '+str(current_user.last_name), class_link=form.class_link.data,phone_number = form.phone_number.data, school_id = current_user.school_id,
    #        school_name =schoolNameRow.name ,is_archived = 'N',last_modified_date = dt.datetime.now())        
    #    db.session.add(liveClassData)
    #    db.session.commit()     
    #    #adding records to topic tracker while registering school                         
    #    flash('New class listed successfully!')               
    return render_template('liveClass.html',allLiveClasses=allLiveClasses,form=form,user_type_val=str(current_user.user_type),current_time=datetime.now(),studentDetails=studentDetails)    

#end of live class section


#####New section for open class modules

@app.route('/openLiveClass')
def openLiveClass():
    live_class_id = request.args.get('live_class_id')
    return render_template('openLiveClass.html')

@app.route('/courseDetail')
def courseDetail():
    live_class_id = request.args.get('live_class_id')
    return render_template('courseDetail.html')


@app.route('/tutorDashboard')
def tutorDashboard():
    return render_template('tutorDashboard.html')


@app.route('/editCourse')
def editCourse():
    return render_template('editCourse.html')

@app.route('/saveCourse',methods=['GET','POST'])
def saveCourse():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print('inside saveCourse')
    course = request.form.get('course')
    description = request.form.get('description')
    setDate = request.form.get('setDate')
    startTime = request.form.get('startTime')
    endTime = request.form.get('endTime')
    days = request.form.getlist('Days')
    video_url = request.form.get('videoUrl')
    idealfor = request.form.getlist('idealfor')
    level = request.form.get('level')
    private = request.form.get('private')
    print('Course name:'+str(course))
    print('description name:'+str(description))
    print('set date:'+str(setDate))
    print('Start time:'+str(startTime))
    print('End Time:'+str(endTime))
    print('Private:'+str(private))
    course_status = request.args.get('course_status')
    print('course status:'+str(course_status))
    for day in days:
        print('Day:'+str(day))
    print('video_url :'+str(video_url))
    print('Ideal for:'+str(idealfor))
    print('level:'+str(level))
    course_staus_id = MessageDetails.query.filter_by(category='Course Status',description=course_status).first()
    
    if private:
        print('if course status is private')
        courseData = CourseDetail(course_name=course,description=description,summary_url=video_url,teacher_id=teacherData.teacher_id,
        school_id=teacherData.school_id,course_status=course_staus_id.msg_id,is_private='Y',is_archived='N',last_modified_date=datetime.now())
    else:
        print('if course status is public')
        courseData = CourseDetail(course_name=course,description=description,summary_url=video_url,teacher_id=teacherData.teacher_id,
        school_id=teacherData.school_id,course_status=course_staus_id.msg_id,is_private='N',is_archived='N',last_modified_date=datetime.now())
    db.session.add(courseData)
    db.session.commit()
    return jsonify(['1'])

##### end of openClass modules





@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    #new arg added for google login
    #gSigninData = request.args.get

    #default form submit action
    form = RegistrationForm()
    if form.validate_on_submit():
        print('Validated form submit')
        #we're setting the username as email address itself. That way a user won't need to think of a new username to register. 
        user = User(username=form.email.data, email=form.email.data, user_type='140', access_status='144', phone=form.phone.data,
            first_name = form.first_name.data,last_name= form.last_name.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        #if a teacher has already been added during school registration then simply add the new user's id to it's teacher profile value        
        checkTeacherProf = TeacherProfile.query.filter_by(email=form.email.data).first()
        #if a student has already been added during school registration then simply add the new user's id to it's student profile value
        checkStudentProf = StudentProfile.query.filter_by(email=form.email.data).first()

        if checkTeacherProf!=None:
            checkTeacherProf.user_id=user.id
            db.session.commit()        
        elif checkStudentProf!=None:
            checkStudentProf.user_id=user.id
            db.session.commit()
        else:
            pass

        full_name = str(form.first_name.data)+ ' '+str(form.last_name.data)
        flash('Congratulations '+full_name+', you are now a registered user!')
        welcome_email(str(form.email.data), full_name)
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/teachingApplicantProfile/<user_id>')
@login_required
def teachingApplicantProfile(user_id):
    job_id = request.args.get('job_id')
    user = User.query.filter_by(id=user_id).first_or_404()
    accessingUser = User.query.filter_by(id=current_user.id).first_or_404()
    return render_template('teachingApplicantProfile.html',user=user, user_type_val=str(accessingUser.user_type),job_id=job_id)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()    
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    school_name_val = schoolNameVal()        
    disconn = ''
    user_type_val = ''
    if current_user.user_type==72:
        disconn = 1
        user_type_val = current_user.user_type
    if user.user_type==161:        
        return redirect(url_for('teachingApplicantProfile',user_id=user.id))
    else:
        print('Nope we are not')

    if school_name_val ==None:
        print('did we reach here')
        return redirect(url_for('disconnectedAccount'))
    else:        
        schoolAdminRow = db.session.execute(text("select school_admin from school_profile where school_id ='"+ str(teacher.school_id)+"'")).fetchall()
        print(schoolAdminRow[0][0])
        accessRequestListRows=""
        value=0
        if current_user.user_type==72:
            value=1
        if schoolAdminRow[0][0]==teacher.teacher_id:
            accessReqQuery = "select t1.username, t1.email, t1.phone, t2.description as user_type, t1.about_me, t1.school_id from public.user t1 inner join message_detail t2 on t1.user_type=t2.msg_id where t1.school_id='"+ str(teacher.school_id) +"' and t1.access_status=143"
            accessRequestListRows = db.session.execute(text(accessReqQuery)).fetchall()
        teacherData = "select distinct teacher_name, description as subject_name, cs.class_val, cs.section,cs.class_sec_id from teacher_subject_class tsc "
        teacherData = teacherData + "inner join teacher_profile tp on tsc.teacher_id = tp.teacher_id "
        teacherData = teacherData + "inner join class_section cs on tsc.class_sec_id = cs.class_sec_id "
        teacherData = teacherData + "inner join message_detail md on tsc.subject_id = md.msg_id where tsc.school_id = '"+str(teacher.school_id)+"' and tsc.teacher_id = '"+str(teacher.teacher_id)+"' and tsc.is_archived = 'N' order by cs.class_sec_id"
        teacherData = db.session.execute(text(teacherData)).fetchall()
        return render_template('user.html', classSecCheckVal=classSecCheck(),user=user,teacher=teacher,accessRequestListRows=accessRequestListRows, school_id=teacher.school_id,disconn=disconn,user_type_val=str(current_user.user_type),teacherData=teacherData)


@app.route('/login', methods=['GET', 'POST'])
def login():
    print('Inside login')    
    if current_user.is_authenticated:        
        if current_user.user_type=='161':
            return redirect(url_for('openJobs'))
        else:
            return redirect(url_for('index'))

    #new section for google login
    glogin = request.args.get('glogin')
    gemail = request.args.get('gemail')
    ##end of new section

    form = LoginForm()
    if form.validate_on_submit() or glogin=="True":
        if glogin=="True":
            print("###glogin val"+ str(glogin))
            print("###email received from page"+ str(gemail))
            user=User.query.filter_by(email=gemail).first()   
            if user is None:
                flash("Email not registered")
                return redirect(url_for('login'))
        else:
            user=User.query.filter_by(email=form.email.data).first()                
            if user is None or not user.check_password(form.password.data):        
                flash("Invalid email or password")
                return redirect(url_for('login'))

        #logging in the user with flask login
        login_user(user,remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        
        #setting global variables
        session['classSecVal'] = classSecCheck()
        session['schoolName'] = schoolNameVal()
        
        print('user name')
        #print(session['username'])
        school_id = ''
        print('user type')
        #print(session['userType'])
        session['studentId'] = ''
        if current_user.user_type==71:
            school_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
        elif current_user.user_type==134:
            school_id = StudentProfile.query.filter_by(user_id=current_user.id).first()
            session['studentId'] = school_id.student_id
        else:
            school_id = User.query.filter_by(id=current_user.id).first()
        school_pro = SchoolProfile.query.filter_by(school_id=school_id.school_id).first()
        session['school_logo'] = ''
        if school_pro:
            session['school_logo'] = school_pro.school_logo
            session['schoolPicture'] = school_pro.school_picture
        query = "select user_type,md.module_name,description, module_url, module_type from module_detail md inner join module_access ma on md.module_id = ma.module_id where user_type = '"+str(current_user.user_type)+"' and ma.is_archived = 'N' and md.is_archived = 'N' order by module_type"
        print(query)
        print('Modules')
        moduleDetRow = db.session.execute(query).fetchall()
        print('School profile')
        #print(session['schoolPicture'])
        # det_list = [1,2,3,4,5]
        session['moduleDet'] = []
        detList = session['moduleDet']
        
        for det in moduleDetRow:
            eachList = []
            print(det.module_name)
            print(det.module_url)
            eachList.append(det.module_name)
            eachList.append(det.module_url)
            eachList.append(det.module_type)
            # detList.append(str(det.module_name)+":"+str(det.module_url)+":"+str(det.module_type))
            detList.append(eachList)
        session['moduleDet'] = detList
        for each in session['moduleDet']:
            print('module_name'+str(each[0]))
            print('module_url'+str(each[1]))
            print('module_type'+str(each[2]))
        #print(session['schoolName'])

        return redirect(next_page)        
        #return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/success',methods=['POST'])
def success():
    if request.method=='POST':
        email=request.form["email"]
        name=request.form["name"]
        if db.session.query(Survivor).filter(Survivor.sur_email == email).count() == 0:
            #Raw sql example  - db.engine.execute(text("<sql here>")).execution_options(autocommit=True))
            # possibly db.session.execute (text("<sql here>")).execution_options(autocommit=True))
            survivor = Survivor(email, name)
            db.session.add(survivor)
            db.session.commit()
            print(email,name)
            welcome_email(email, name)
            return render_template('newsletterSuccess.html')
        else:
            return render_template('index.html',text='Error: Email already used.')

@app.route('/setFee',methods=['GET','POST'])
def setFee():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first() 
    class_val = request.args.get('class_val')
    section = request.args.get('section')
    total_fee = request.args.get('total_fee')
    classSec_id = ClassSection.query.filter_by(class_val=class_val,section=section,school_id=teacher_id.school_id).first()
    class_sec_id = classSec_id.class_sec_id
    sections = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).all()
    for section in sections:
        insertAmount = FeeClassSecDetail(class_sec_id=section.class_sec_id,class_val=section.class_val,section=section.section,is_current='Y',last_modified_date=datetime.now(),change_date=datetime.now(),amount=total_fee,school_id=teacher_id.school_id)
        db.session.add(insertAmount)
    db.session.commit()
    return jsonify(['0'])

@app.route('/feeManagement')
@login_required
def feeManagement():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first() 
    distinctClasses = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacher_id.school_id)+" GROUP BY class_val order by s")).fetchall() 
    classSections=ClassSection.query.filter_by(school_id=teacher_id.school_id).all()
    qclass_val = request.args.get('class_val')
    qsection=request.args.get('section')
    fee = ''
    amount = FeeClassSecDetail.query.filter_by(class_val=qclass_val,section=qsection,school_id=teacher_id.school_id).first()
    print(amount)
    clas=db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacher_id.school_id)+" GROUP BY class_val order by s")).first() 
    if amount:
        fee = amount.amount
        print('amount:'+str(fee))
    if qclass_val==None or qclass_val=='':
        qclass_val = clas.class_val
        qsection = 'A'
    return render_template('feeManagement.html',qclass_val=qclass_val,qsection=qsection,distinctClasses=distinctClasses,classsections=classSections,fee=fee)


@app.route('/privacyPolicy')
def privacyPolicy():
    return render_template('privacyPolicy.html')

@app.route('/sendPerformanceReportEmail')
def sendPerformanceReportEmail():
    school_id = request.args.get('school_id')
    schoolAdmin = "select teacher_name as admin from school_profile sp inner join teacher_profile tp on sp.school_admin = tp.teacher_id where sp.school_id='"+str(school_id)+"'"
    schoolAdmin = db.session.execute(schoolAdmin).first()
    score = "Select avg_score from fn_overall_performance_summary("+str(school_id)+") where class='All'and section='All' and subject='All'"
    avg_score = db.session.execute(score).first()
    #####Fetch Top 5 Students info##########        
    # topStudentsQuery = "select *from fn_monthly_top_students("+str(teacher.school_id)+",8)"
    qclass_val = 'dashboard'
    topStudentsRows = ''
    leaderBoardData = leaderboardContent(qclass_val)

    # Convert dataframe to a list

    df1 = leaderBoardData[['studentid','profile_pic','student_name','class_val','section','total_marks%','total_tests']]
    df2 = leaderBoardData.drop(['profile_pic', 'student_name','class_val','section','total_marks%','total_tests'], axis=1)
    leaderBoard = pd.merge(df1,df2,on=('studentid'))
            
    d = leaderBoard[['studentid','profile_pic','student_name','class_val','section','total_marks%','total_tests']]
    df3 = leaderBoard.drop(['studentid'],axis=1)
            # print('DF3:')
            # print(df3)
            # print('print new dataframe')
            
    df1.rename(columns = {'profile_pic':'Profile Picture'}, inplace = True)
    df1.rename(columns = {'student_name':'Student'}, inplace = True)
    df1.rename(columns = {'class_val':'Class'}, inplace = True)
    df1.rename(columns = {'section':'Section'}, inplace = True)
    df1.rename(columns = {'total_marks%':'Total Marks'}, inplace = True)
    df1.rename(columns = {'total_tests':'Total Tests'}, inplace = True)
            # print(df1)
            # print('Excluding columns')
            # print(df2)
            # rename(df2)
            # print('LeaderBoard Data:')
            # print(leaderBoardData)
    data = []
            

    header = [df1.columns.values.tolist()]
    headerAll = [df3.columns.values.tolist()]
    colAll = ''
    subjHeader = [df2.columns.values.tolist()]
    columnNames = ''
    col = ''
    subColumn = ''
            # print('Size of dataframe:'+str(len(subjHeader)))
    for subhead in subjHeader:
        subColumn = subhead
                # print('Header with Subject Name')
                # print(subhead)
    for h in header:
        columnNames = h
    for headAll in headerAll: 
        colAll = headAll
            # print(' all header Length:'+str(len(colAll))+'Static length:'+str(len(columnNames))+'sub header length:'+str(len(subColumn)))
    n= int(len(subColumn)/2)
    ndf = df2.drop(['studentid'],axis=1)
    newDF = ndf.iloc[:,0:n]
    new1DF = ndf.iloc[:,n:]
            
    df5 = pd.concat([newDF, new1DF], axis=1)
    DFW = df5[list(sum(zip(newDF.columns, new1DF.columns), ()))]
           
           
    dat = pd.concat([d,DFW], axis=1)
    dat = dat.sort_values('total_marks%',ascending=False)  
    print(dat)        
    subHeader = ''
    i=1
    for row in dat.values.tolist():
        if i<6:
            data.append(row)
        i=i+1

    for d in data:
        print('Print Dataframe Data:')
        print(d[0])
        print(d[1])
        print(d[2])
        print(d[3])
            # print(d[i])

        # End  
    query = "select sum(total) as total_test from "
    query = query + "(select count(*) as total from response_capture rc where last_modified_date >current_date - 7 and school_id='"+str(school_id)+"'"
    query = query + " union all "
    query = query + "select count(*) from (select upload_id from result_upload ru where school_id='"+str(school_id)+"' and last_modified_date >current_date - 7"      
    query = query + " group by ru.upload_id)d ) s"
    test_count = db.session.execute(query).first()
    adminEmail=db.session.execute(text("select t2.email,t2.teacher_name,t1.school_name,t3.username from school_profile t1 inner join teacher_profile t2 on t1.school_admin=t2.teacher_id inner join public.user t3 on t2.email=t3.email where t1.school_id='"+str(school_id)+"'")).first()

    if adminEmail!=None:
        performance_report_email(adminEmail.email,adminEmail.teacher_name, adminEmail.school_name,data,test_count.total_test,avg_score.avg_score,school_id)
        return jsonify(["0"])
    else:
        return jsonify(["1"])
    


@app.route('/requestUserAccess')
def requestUserAccess():
    requestorUsername=request.args.get('username')    
    school_id=request.args.get('school_id')    
    about_me=request.args.get('about_me')    
    quser_type = request.args.get('user_type')        
    adminEmail=db.session.execute(text("select t2.email,t2.teacher_name,t1.school_name,t3.username from school_profile t1 inner join teacher_profile t2 on t1.school_admin=t2.teacher_id inner join public.user t3 on t2.email=t3.email where t1.school_id='"+school_id+"'")).first()
    print(adminEmail)
    print('User Type:'+str(quser_type))
    
    if adminEmail!=None:
        userTableDetails = User.query.filter_by(username=requestorUsername).first()
        userTableDetails.school_id=school_id
        userTableDetails.access_status='143'
        userTableDetails.user_type=quser_type
        userTableDetails.about_me=about_me
        db.session.commit()
        
        user_access_request_email(adminEmail.email,adminEmail.teacher_name, adminEmail.school_name, userTableDetails.first_name+ ''+userTableDetails.last_name, adminEmail.username, quser_type)
        return jsonify(["0"])
    else:
        return jsonify(["1"])



@app.route('/syllabus')
@login_required
def syllabus():
    fromSchoolRegistration = False
    subjectValues = MessageDetails.query.filter_by(category='Subject').all()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    boardRows = MessageDetails.query.filter_by(msg_id=board.board_id).first()
    school_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    classValues = "SELECT class_val,sum(class_sec_id) as s FROM class_section cs where school_id = '"+str(teacher_id.school_id)+"' group by class_val order by s"
    classValues = db.session.execute(text(classValues)).fetchall()
    classValuesGeneral = "SELECT class_val,sum(class_sec_id) as s FROM class_section cs group by class_val order by s"
    classValuesGeneral = db.session.execute(text(classValuesGeneral)).fetchall()
    subjectValues = MessageDetails.query.filter_by(category='Subject').all()
    bookName = BookDetails.query.all()
    chapterNum = Topic.query.distinct().all()
    topicId = Topic.query.all()
    generalBoardId = SchoolProfile.query.with_entities(SchoolProfile.board_id).filter_by(school_id=teacher_id.school_id).first()
    generalBoard = MessageDetails.query.filter_by(msg_id=generalBoardId.board_id).first()
    for clas in classValues:
        print('Class value:'+str(clas.class_val))
    return render_template('syllabus.html',generalBoard=generalBoard,boardRowsId = boardRows.msg_id , boardRows=boardRows.description,subjectValues=subjectValues,school_name=school_id.school_name,classValues=classValues,classValuesGeneral=classValuesGeneral,bookName=bookName,chapterNum=chapterNum,topicId=topicId,fromSchoolRegistration=fromSchoolRegistration,user_type_val=str(current_user.user_type))

@app.route('/addSyllabus',methods=['GET','POST'])
def addSyllabus():
    print('inside add syllabus')
    classes = request.get_json()
    # class_val = request.args.get('class_val')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    for class_val in classes:
        classExist = ClassSection.query.filter_by(class_val=class_val,section='A',school_id=teacher_id.school_id).first()
        if classExist == None:
            addClass = ClassSection(class_val=class_val,section='A',school_id=teacher_id.school_id,student_count=0,class_teacher=teacher_id.teacher_id,last_modified_date=datetime.now())
            db.session.add(addClass)
            db.session.commit()
    # class_sec_id = ClassSection.query.filter_by(class_val=class_val,section='A',school_id=teacher_id.school_id,student_count=0,class_teacher=teacher_id.teacher_id).first()
    # for subject in subjects:
    #     subject_id = MessageDetails.query.filter_by(description=subject,category='Subject').first()
    #     subjExist = ''
    #     subjExist = BoardClassSubject.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,school_id=teacher_id.school_id).first()
    #     print(subjExist)
    #     if subjExist == None:
    #         print('is subjExist is null')
    #         addSubject = BoardClassSubject(board_id=board_id.board_id,class_val=class_val,subject_id=subject_id.msg_id,is_archived='N',school_id=teacher_id.school_id,last_modified_date=datetime.now())
    #         db.session.add(addSubject)
    #         db.session.commit()
        # bookNames = BookDetails.query.distinct(BookDetails.book_name).filter_by(subject_id=subject_id.msg_id,class_val=class_val).all()
        print('after add subjects')
        # for book_name in bookNames:
        #     book_id = BookDetails.query.filter_by(subject_id=subject_id.msg_id,class_val=class_val,book_name=book_name.book_name).first()
        #     addBook = BoardClassSubjectBooks(school_id=teacher_id.school_id,class_val=class_val,subject_id=subject_id.msg_id,book_id=book_id.book_id,is_archived='N')
        #     db.session.add(addBook)
        #     db.session.commit()
        # insertRow = "insert into topic_tracker (subject_id, class_sec_id, is_covered, topic_id, school_id, reteach_count,is_archived, last_modified_date) (select subject_id, '"+str(class_sec_id.class_sec_id)+"', 'N', topic_id, '"+str(teacher_id.school_id)+"', 0,'N',current_date from Topic_detail where class_val="+str(class_val)+")"
        # db.session.execute(text(insertRow))
        # db.session.commit()
    return ("Syllabus added successfully")


@app.route('/generalSyllabusClasses')
def generalSyllabusClasses():
    board_id=request.args.get('board_id')
    classArray = []
    distinctClasses = "SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs GROUP BY class_val order by s"
    distinctClasses = db.session.execute(text(distinctClasses)).fetchall()
    for val in distinctClasses:
        classArray.append(val.class_val)
    if classArray:
        return jsonify([classArray])
    else:
        return ""

@app.route('/syllabusClasses')
@login_required
def syllabusClasses():
    board_id=request.args.get('board_id')
    classSectionArray = []
    sectionArray = []
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    distinctClasses = "SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id = '"+str(teacher_id.school_id)+"' GROUP BY class_val order by s"
    distinctClasses = db.session.execute(text(distinctClasses)).fetchall()
    for val in distinctClasses:
        #print(val.class_val)
        sections = ClassSection.query.distinct(ClassSection.section).filter_by(school_id=teacher_id.school_id,class_val=val.class_val).all()
        # sectionsString = ''
        sectionsString = '['
        i=1
        for section in sections:
            #print(len(sections))
            if i<len(sections):
                sectionsString = sectionsString + str(section.section)+';'
            else:
                sectionsString = sectionsString + str(section.section)
            i = i + 1
        sectionsString = sectionsString + ']'
        classSectionArray.append(str(val.class_val)+':'+str(sectionsString))
    if classSectionArray:
        return jsonify([classSectionArray])
    else:
        return ""


@app.route('/generalSyllabusSubjects',methods=['GET','POST'])
def generalSyllabusSubjects():
    board_id=request.args.get('board_id')
    class_val=request.args.get('class_val')
    sujectArray=[]
    subjects = "select distinct description,msg_id from message_detail md inner join topic_detail td on md.msg_id = td.subject_id where td.class_val = '"+str(class_val)+"' order by description"
    subjects = db.session.execute(text(subjects)).fetchall()
    for val in subjects:
        # subject = MessageDetails.query.filter_by(msg_id=val.subject_id).first()
        sujectArray.append(str(val.msg_id)+":"+str(val.description))
    if sujectArray:
        return jsonify([sujectArray])   
    else:
        return ""

@app.route('/syllabusSubjects')
@login_required
def syllabusSubjects():
    board_id=request.args.get('board_id')
    class_val=request.args.get('class_val')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    distinctSubject = BoardClassSubject.query.filter_by(class_val=class_val,board_id=board_id,school_id=teacher_id.school_id,is_archived='N').all()
    sujectArray=[]
    subjects = "select distinct description,msg_id from message_detail md inner join board_class_subject bcs on md.msg_id = bcs.subject_id where bcs.class_val = '"+str(class_val)+"' and school_id='"+str(teacher_id.school_id)+"' and bcs.is_archived= 'N' order by description"
    subjects = db.session.execute(text(subjects)).fetchall()
    for val in subjects:
        # subject = MessageDetails.query.filter_by(msg_id=val.subject_id).first()
        sujectArray.append(str(val.msg_id)+":"+str(val.description))
    if sujectArray:
        return jsonify([sujectArray])   
    else:
        return ""

@app.route('/fetchSubjects',methods=['GET','POST'])
def fetchSubjects():
    class_val = request.args.get('class_val')
    board = request.args.get('board')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    distinctSubject = BoardClassSubject.query.filter_by(class_val=class_val,board_id=board,school_id=teacher_id.school_id,is_archived='N').all()
    sujectArray=[]
    subjects = "select distinct description,msg_id from message_detail md inner join board_class_subject bcs on md.msg_id = bcs.subject_id where bcs.class_val = '"+str(class_val)+"' and school_id='"+str(teacher_id.school_id)+"' and bcs.is_archived= 'N' order by description"
    subjects = db.session.execute(text(subjects)).fetchall()
    for val in subjects:
        # subject = MessageDetails.query.filter_by(msg_id=val.subject_id).first()
        sujectArray.append(str(val.msg_id)+":"+str(val.description))
    if sujectArray:
        return jsonify([sujectArray])   
    else:
        return "" 

@app.route('/fetchRemSubjects',methods=['GET','POST'])
def fetchRemSubjects():
    print('inside fetchRemSubjects')
    class_val = request.args.get('class_val')
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher.school_id).first()
    distinctSubject = BoardClassSubject.query.filter_by(class_val=class_val,board_id=board_id.board_id,school_id=teacher.school_id,is_archived='Y').all()
    subjectArray=[]
    generalSubjects = "select distinct msg_id,description from topic_detail td inner join message_detail md on md.msg_id=td.subject_id "
    generalSubjects = generalSubjects + "where md.msg_id not in (select distinct msg_id from message_detail md "
    generalSubjects = generalSubjects + "inner join board_class_subject bcs on md.msg_id = bcs.subject_id where bcs.class_val = '"+str(class_val)+"' and school_id='"+str(teacher.school_id)+"' "
    generalSubjects = generalSubjects + ")  order by description"
    print('Query: '+str(generalSubjects))
    generalSubjects = db.session.execute(text(generalSubjects)).fetchall()
    subjects = "select distinct description,msg_id from message_detail md inner join board_class_subject bcs on md.msg_id = bcs.subject_id where bcs.class_val = '"+str(class_val)+"' and school_id='"+str(teacher.school_id)+"' and bcs.is_archived= 'Y' order by description"
    print(subjects)
    subjects = db.session.execute(text(subjects)).fetchall()
    for val in subjects:
        # subject = MessageDetails.query.filter_by(msg_id=val.subject_id).first()
        subjectArray.append(str(val.msg_id)+":"+str(val.description))
    for val in generalSubjects:
        subjectArray.append(str(val.msg_id)+":"+str(val.description))
    if subjectArray:
        return jsonify([subjectArray])   
    else:
        return ""

@app.route('/addSubject',methods=['GET','POST'])
def addSubject():
    subject_id = request.args.get('subject')
    board_id=request.args.get('board')
    class_val=request.args.get('class_val')
    print('Subject:'+str(subject_id))
    # subject_id = MessageDetails.query.filter_by(description=subjectVal,category='Subject').first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    subjExist = BoardClassSubject.query.filter_by(class_val=class_val,board_id=board_id,subject_id=subject_id,school_id=teacher_id.school_id).first()
    if subjExist==None:
        addSubject = BoardClassSubject(class_val=class_val,subject_id=subject_id,school_id=teacher_id.school_id,board_id=board_id,is_archived='N')
        db.session.add(addSubject)
        db.session.commit()
    else:
        insertSubject = BoardClassSubject.query.filter_by(class_val=class_val,subject_id=subject_id,school_id=teacher_id.school_id,board_id=board_id,is_archived='Y').first()
        insertSubject.is_archived = 'N'
        db.session.add(insertSubject)
        db.session.commit()
    return ('update data successfully')

@app.route('/addChapter',methods=['GET','POST'])
def addChapter():
    topics=request.get_json()
    print('inside add Chapter')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    chapterName = request.args.get('chapterName')
    
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    chapter_num = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,chapter_name=chapterName).first()
    print(topics)
    print('School id:'+str(teacher_id.school_id))
    for topic in topics:
        print('inside for')
        print(topic)
        # topic_id = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,topic_name=topic).first()
        existInTT = TopicTracker.query.filter_by(topic_id=topic,school_id=teacher_id.school_id,class_sec_id=class_sec_id.class_sec_id,subject_id=subject_id.msg_id).first()
        
        if existInTT:
            updateTT = "update topic_tracker set is_archived='N' where school_id='"+str(teacher_id.school_id)+"' and subject_id='"+str(subject_id.msg_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and topic_id='"+str(topic_id.topic_id)+"'"
            print(updateTT)
            updateTT = db.session.execute(text(updateTT))
        else:
            insertTT = TopicTracker(subject_id=subject_id.msg_id,class_sec_id=class_sec_id.class_sec_id,is_covered='N',topic_id=topic,school_id=teacher_id.school_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(insertTT)
        db.session.commit()
    return ("data updated successfully")

@app.route('/addBook',methods=['GET','POST'])
def addBook():
    book_id = request.args.get('book')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    print("class_val"+str(class_val))
    print("subject id"+str(subject_id.msg_id))
    print("book id"+str(book_id))
    book = BookDetails.query.filter_by(book_id=book_id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id).all()
    
    for book_id in bookIds:
        updateBCSB = BoardClassSubjectBooks.query.filter_by(school_id=teacher_id.school_id,class_val=class_val,
        subject_id=subject_id.msg_id,book_id=book_id.book_id).first()
        if updateBCSB:
            updateBCSB.is_archived = 'N'
        else:
            addBook = BoardClassSubjectBooks(school_id=teacher_id.school_id,class_val=class_val,subject_id=subject_id.msg_id,book_id=book_id.book_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(addBook)
        db.session.commit()
    return ("data updated successfully")



@app.route('/addNewSubject',methods=['GET','POST'])
def addNewSubject():
    subject = request.args.get('subject')
    subject = subject.title()
    class_val = request.args.get('class_val')
    board = request.args.get('board')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    insertSubject = MessageDetails(category='Subject',description=subject)
    db.session.add(insertSubject)
    db.session.commit()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    insertBCS = BoardClassSubject(class_val=class_val,subject_id=subject_id.msg_id,school_id=teacher_id.school_id,board_id=board,is_archived='N')
    db.session.add(insertBCS)
    db.session.commit()
    return ('New Subject added successfully')

@app.route('/addNewBook',methods=['GET','POST'])
def addNewBook():
    bookName = request.args.get('book')
    bookLink = request.args.get('bookLink')
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    bookName = bookName.strip()
    for x in bookName.lower(): 
        if x in punctuations: 
            bookName = bookName.replace(x, "") 
            print(bookName)
        else:
            break
    if bookName==None or bookName=='':
        return "NA"
    bookName = bookName.strip()
    bookLink = bookLink.strip()
    for x in bookLink.lower(): 
        if x in punctuations: 
            bookLink = bookLink.replace(x, "") 
            print(bookLink)
        else:
            break
    bookLink = bookLink.strip()
    book = bookName.title()
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    print('class in addNewBook:'+str(class_val))
    subject_id= MessageDetails.query.filter_by(description=subject).first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    bookExist = BookDetails.query.filter_by(board_id=board_id.board_id,book_name=bookName,class_val=class_val,subject_id=subject_id.msg_id).first()
    if bookExist==None:
        if bookLink:
            insertBook = BookDetails(board_id=board_id.board_id,book_name=book,class_val=class_val,subject_id=subject_id.msg_id,teacher_id=teacher_id.teacher_id,book_link=bookLink,last_modified_date=datetime.now())
        else:
            insertBook = BookDetails(board_id=board_id.board_id,book_name=book,class_val=class_val,subject_id=subject_id.msg_id,teacher_id=teacher_id.teacher_id,last_modified_date=datetime.now())
        db.session.add(insertBook)
        db.session.commit()
        book_id = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_name=book).first()
        insertInBCSB = BoardClassSubjectBooks(school_id=teacher_id.school_id,class_val=class_val,subject_id=subject_id.msg_id,
        book_id=book_id.book_id,is_archived='N',last_modified_date=datetime.now())
        db.session.add(insertInBCSB)
        db.session.commit()
    return ('New Book added successfully')

@app.route('/checkForChapter',methods=['GET','POST'])
def checkForChapter():
    print('inside checkForChapter')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    chapterNum = request.args.get('chapter_num')
    bookId = request.args.get('bookId')
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    for x in chapterNum: 
        if x in punctuations: 
            chapterNum = chapterNum.replace(x, "") 
            print(chapterNum)
            return "NA"
        else:
            break
    chapterName = request.args.get('chapter_name')
    for x in chapterName.lower(): 
        if x in punctuations: 
            chapterName = chapterName.replace(x, "") 
            print(chapterName)
            return "NA"
        else:
            break
    subject_id= MessageDetails.query.filter_by(description=subject).first()
    print('Book Id:'+str(bookId))
    book = BookDetails.query.filter_by(book_id=bookId).first()
    bookIds = BookDetails.query.filter_by(class_val=class_val,book_name=book.book_name,subject_id=subject_id.msg_id).all()
    print('class_val:'+str(class_val)+'subject:'+str(subject_id.msg_id)+'Book name:'+str(book.book_name))
    # bookIds = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_name=book.book_name).all()
    k = 0
    print(book.book_name)
    for book_id in bookIds:
        print(str(class_val)+' '+str(subject_id.msg_id)+' '+str(chapterNum)+' '+str(book_id.book_id))
        topic1 = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,chapter_num=chapterNum,book_id=book_id.book_id).first()
        topic2 = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,chapter_name=chapterName,book_id=book_id.book_id).first()
        print('inside for')
        print(book_id.book_id)
        print(topic1)
        if topic1 or topic2:
            k = 1
    print(k)
    if k==1:
        return ""
    else:
        return "1"

@app.route('/addClassSection',methods=['POST'])
def addClassSection():
    print('inside addClassSection')
    sections=request.get_json()
    class_val = request.args.get('class_val')
    print('class values:'+str(class_val))
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    for section in sections:
        # class_section = class_section.split(':')
        # class_val = class_section[0]
        # section = class_section[1]
        checkClass = ClassSection.query.filter_by(class_val=str(class_val),section=section.upper(),school_id=teacher_id.school_id).first()
        if checkClass:
            return ""
    for section in sections:
        # print(section)
        # class_section = class_section.split(':')
        # class_val = class_section[0]
        # section = class_section[1]
        
        print('Class:'+str(class_val)+' Section:'+str(section))
        class_data=ClassSection(class_val=str(class_val),section=str(section).upper(),student_count=0,school_id=teacher_id.school_id,last_modified_date=datetime.now())
        db.session.add(class_data)
        db.session.commit()
    
    for section in sections:
        # class_section = class_section.split(':')
        # class_val = class_section[0]
        # section = class_section[1]
        class_id = ClassSection.query.filter_by(class_val=str(class_val),section=section.upper(),school_id=teacher_id.school_id).first()
        topic_tracker = TopicTracker.query.filter_by(class_sec_id=class_id.class_sec_id,school_id=teacher_id.school_id).first()
        if topic_tracker:
            print('data already present')
        else:
            print('insert data into topic tracker')
            insertRow = "insert into topic_tracker (subject_id, class_sec_id, is_covered, topic_id, school_id, reteach_count, last_modified_date) (select subject_id, '"+str(class_id.class_sec_id)+"', 'N', topic_id, '"+str(teacher_id.school_id)+"', 0,current_date from Topic_detail where class_val='"+str(class_val)+"')"
            db.session.execute(text(insertRow))
        db.session.commit()   

    return "success"

@app.route('/checkForBook',methods=['GET','POST'])
def checkForBook():
    book = request.args.get('book')
    book = book.title()
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    bookName = book.strip()
    for x in bookName.lower(): 
        if x in punctuations: 
            bookName = bookName.replace(x, "") 
            print(bookName)
        else:
            break
    if bookName==None or bookName=='':
        return "NA"
    subject_id = MessageDetails.query.filter_by(category='Subject',description=subject).first()
    checkBook = BookDetails.query.filter_by(book_name=bookName,class_val=class_val,subject_id=subject_id.msg_id).first()
    if checkBook:
        return (book)
    else:
        return ""

@app.route('/checkForSubject',methods=['GET','POST'])
def checkForSubject():
    subject = request.args.get('subject')
    subject = subject.title()
    print('inside check for subject:'+str(subject))
    class_val = request.args.get('class_val')
    board = request.args.get('board')
    checkSubject = MessageDetails.query.filter_by(category='Subject',description=subject).first()
    if checkSubject:
        return (subject)
    else:
        return ""

@app.route('/checkforClassSection',methods=['GET','POST'])
def checkforClassSection():
    sections=request.get_json()
    class_val = request.args.get('class_val')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print('inside checkforClassSection')
    print(sections)
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    class_val = class_val.strip()
    print('before remove punc class:'+str(class_val))
    if class_val==None or class_val=='':
        print('if clas_val is none')
        return "NB"
    
    for x in class_val: 
        if x in punctuations: 
            class_val = class_val.replace(x, "") 
            print('after remove punc class:'+str(class_val))
            return "NA"
        else:
            break
    for section in sections:
        # class_section = class_section.split(':')
        # class_val = class_section[0]
        # section = class_section[1]
        punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
        section = section.strip()
        for x in section.lower(): 
            if x in punctuations: 
                section = section.replace(x, "") 
                print(section)
                return "NA"
            else:
                break
        if section==None or section=='':
            print('if section is none')
            return "NB"
        print('class_val:'+class_val)
        print('section:'+section.upper())
        checkClass = ClassSection.query.filter_by(class_val=str(class_val),section=section.upper(),school_id=teacher_id.school_id).first()
        if checkClass:
            return str(class_val)+':'+str(section.upper())
    return ""


@app.route('/addNewTopic',methods=['GET','POST'])
def addNewTopic():
    print('inside add new topic')
    topics=request.get_json()
    book_id = request.args.get('book_id')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    chapter = request.args.get('chapter')
    chapter_num = request.args.get('chapter_num')
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    subject_id = MessageDetails.query.filter_by(description = subject).first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    book = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_id=book_id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    bookId = "select distinct bd.book_id from book_details bd inner join topic_detail td on td.book_id = bd.book_id where td.subject_id = '"+str(subject_id.msg_id)+"' and td.class_val  = '"+str(class_val)+"' and chapter_num = '"+str(chapter_num)+"' and bd.book_name = '"+str(book.book_name)+"'"
    bookId = db.session.execute(text(bookId)).first()
    print(topics)
    print('Book ID:'+str(bookId.book_id))
    for topic in topics:
        print(topic)
        topic = topic.strip()
        for x in topic: 
            if x in punctuations: 
                topic = topic.replace(x, "") 
                print(topic)
            else:
                break
        topic = topic.strip()
        topic = topic.capitalize()
        if bookId:
            insertTopic = Topic(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=chapter_num,class_val=class_val,book_id=bookId.book_id,teacher_id=teacher_id.teacher_id)
        db.session.add(insertTopic)
        db.session.commit()
        if bookId:
            topic_id = Topic.query.filter_by(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=chapter_num,class_val=class_val,book_id=bookId.book_id).first()
        insertTopicTracker = TopicTracker(subject_id=subject_id.msg_id,class_sec_id=class_sec_id.class_sec_id,is_covered='N',topic_id=topic_id.topic_id,school_id=teacher_id.school_id,is_archived='N',last_modified_date=datetime.now())
        db.session.add(insertTopicTracker)
        db.session.commit()
    return ("Add new Topic")
  
@app.route('/addNewChapter',methods=['GET','POST'])
def addNewChapter():
    print('inside add new chapter')
    topics=request.get_json()
    book_id = request.args.get('book_id')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    chapter = request.args.get('chapter')
    chapter = chapter.strip()
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    for x in chapter.lower(): 
        if x in punctuations: 
            chapter = chapter.replace(x, "") 
            print(chapter)
        else:
            break
    chapter = chapter.strip()
    chapter = chapter.capitalize() 
    chapter_num = request.args.get('chapter_num')
    chapter_num = chapter_num.strip()
    for x in chapter_num: 
        if x in punctuations: 
            chapter_num = chapter_num.replace(x, "") 
            print(chapter_num)
        else:
            break
    chapter_num = chapter_num.strip()
    subject_id = MessageDetails.query.filter_by(description = subject).first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    # bookId = "select distinct bd.book_id from book_details bd inner join topic_detail td on td.book_id = bd.book_id where td.subject_id = '"+str(subject_id.msg_id)+"' and td.class_val  = '"+str(class_val)+"' and chapter_num = '"+str(chapter_num)+"'"
    # bookId = db.session.execute(text(bookId)).first()
    print(topics)
    # print('Book ID:'+str(bookId))
    maxChapterNum = "select max(chapter_num) from topic_detail td"
    maxChapterNum = db.session.execute(text(maxChapterNum)).first()
    print('Max chapter no')
    print(maxChapterNum[0])
    maxChapterNum = int(maxChapterNum[0]) + 1
    for topic in topics:
        print(topic)
        topic = topic.strip()
        for x in topic: 
            if x in punctuations: 
                topic = topic.replace(x, "") 
                print(topic)
            else:
                break
        topic = topic.strip()
        topic = topic.capitalize()
        if chapter_num:
            insertTopic = Topic(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=chapter_num,class_val=class_val,book_id=book_id,teacher_id=teacher_id.teacher_id)
        else:
            insertTopic = Topic(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=maxChapterNum,class_val=class_val,book_id=book_id,teacher_id=teacher_id.teacher_id)
        db.session.add(insertTopic)
        db.session.commit()
        if chapter_num:
            topic_id = Topic.query.filter_by(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=chapter_num,class_val=class_val,book_id=book_id).first()
        else:
            topic_id = Topic.query.filter_by(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=maxChapterNum,class_val=class_val,book_id=book_id).first()
        insertTopicTracker = TopicTracker(subject_id=subject_id.msg_id,class_sec_id=class_sec_id.class_sec_id,is_covered='N',topic_id=topic_id.topic_id,school_id=teacher_id.school_id,is_archived='N',last_modified_date=datetime.now())
        db.session.add(insertTopicTracker)
        db.session.commit()
    return ("Add new Chapter")


@app.route('/spellCheckBook',methods=['GET','POST'])
def spellCheckBook():
    print('inside spellCheckBox')
    bookText = request.args.get('bookText')
    return ""
    #if bookText=='':
    #    return ""
    #spell = SpellChecker()
    #correct = spell.correction(bookText)
    #print('correct word:'+str(correct))
    #if bookText==correct:
    #    return ""
    #else:
    #    print('inside if')
    #    print(bookText)
    #    print(correct)
    #    return correct

@app.route('/deleteSubject',methods=['GET','POST'])
def deleteSubject():
    subject_id = request.args.get('subjectId')
    class_val = request.args.get('class_val')
    board = request.args.get('board')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    deleteSubject = BoardClassSubject.query.filter_by(class_val=class_val,school_id=teacher_id.school_id,subject_id=subject_id,board_id=board).first()
    deleteSubject.is_archived = 'Y'
    db.session.commit()
    return ("delete subject successfully")

@app.route('/deleteBook',methods=['GET','POST'])
def deleteBook():
    subject = request.args.get('subject')
    class_val = request.args.get('class_val')
    bookId = request.args.get('bookId')
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    book = BookDetails.query.filter_by(book_id=bookId,subject_id=subject_id.msg_id,class_val= class_val).first()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id).all()
    print('book name:'+str(book.book_name))
    for book_id in bookIds:
        print(book_id.book_id)
        updateBook = BoardClassSubjectBooks.query.filter_by(book_id=book_id.book_id,school_id=teacher_id.school_id,class_val=class_val,subject_id=subject_id.msg_id).first()
        print(updateBook)
        updateBook.is_archived = 'Y'
        db.session.commit()
    return ("delete book successfully")

@app.route('/deleteTopics',methods=['GET','POST'])
def deleteTopics():
    subject = request.args.get('subject')
    class_val = request.args.get('class_val')
    bookId = request.args.get('bookId')
    chapter_num = request.args.get('chapter_num')
    topic_id = request.args.get('topic_id')
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    updateTT = "update topic_tracker set is_archived='Y' where school_id='"+str(teacher_id.school_id)+"' and subject_id='"+str(subject_id.msg_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and topic_id='"+str(topic_id)+"'"
    print(updateTT)
    updateTT = db.session.execute(text(updateTT))
    db.session.commit()
    return ("delete topic successfully")

@app.route('/deleteChapters',methods=['GET','POST'])
def deleteChapters():
    subject = request.args.get('subject')
    bookId = request.args.get('bookId')
    class_val = request.args.get('class_val')
    chapter_num = request.args.get('chapter_num')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    book  = BookDetails.query.filter_by(book_id=bookId,class_val=class_val,subject_id=subject_id.msg_id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id).all()
    book_id = Topic.query.filter_by(subject_id=subject_id.msg_id,class_val=class_val,chapter_num=chapter_num).first()
    # for book_id in bookIds:
    #     print('inside for of deleteChapters')
    print('subID:'+str(subject_id.msg_id)+' class_val:'+str(class_val)+' chapter num:'+str(chapter_num)+' bookName:'+str(book.book_name))
    topic_ids = "select topic_id from topic_detail td where td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id.msg_id)+"' and chapter_num = '"+str(chapter_num)+"' "
    topic_ids = topic_ids + "and td.book_id in (select book_id from book_details bd2 where book_name = '"+str(book.book_name)+"' and class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id.msg_id)+"')"
    topic_ids = db.session.execute(text(topic_ids)).fetchall()
    for topic_id in topic_ids:
        print('Topic id:'+str(topic_id.topic_id))
        # updateTT = TopicTracker.query.filter_by(school_id=teacher_id.school_id,subject_id=subject_id.msg_id,class_sec_id=class_sec_id.class_sec_id,topic_id=topic_id.topic_id).all()
        updateTT = "update topic_tracker set is_archived='Y' where school_id='"+str(teacher_id.school_id)+"' and subject_id='"+str(subject_id.msg_id)+"' and class_sec_id in (select class_sec_id from class_section where class_val='"+str(class_val)+"' and school_id='"+str(teacher_id.school_id)+"') and topic_id='"+str(topic_id.topic_id)+"'"
        print(updateTT)
        updateTT = db.session.execute(text(updateTT))
        db.session.commit()
    return ("delete chapter successfully")

@app.route('/generalSyllabusBooks')
def generalSyllabusBooks():
    subject_name=request.args.get('subject_name')
    class_val=request.args.get('class_val')
    board_id = request.args.get('board_id')
    subject_id = MessageDetails.query.filter_by(description=subject_name).first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    distinctBooks = "select distinct bd.book_name from book_details bd inner join topic_detail td on "
    distinctBooks = distinctBooks + "bd.book_id = td.book_id where bd.subject_id='"+str(subject_id.msg_id)+"' and td.class_val = '"+str(class_val)+"' order by bd.book_name"
    distinctBooks = db.session.execute(text(distinctBooks)).fetchall()
    bookArray=[]
    for val in distinctBooks:
        print(val.book_name)
        book_id = BookDetails.query.filter_by(book_name=val.book_name).first()
        bookArray.append(str(book_id.book_id)+':'+str(val.book_name))
    if bookArray:
        return jsonify([bookArray])  
    else:
        return ""

@app.route('/syllabusBooks')
@login_required
def syllabusBooks():
    subject_name=request.args.get('subject_name')
    class_val=request.args.get('class_val')
    board_id = request.args.get('board_id')
    subject_id = MessageDetails.query.filter_by(description=subject_name).first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    distinctBooks = "select distinct bd.book_name from book_details bd inner join board_class_subject_books bcsb on "
    distinctBooks = distinctBooks + "bd.book_id = bcsb.book_id where bcsb.school_id='"+str(teacher_id.school_id)+"' and bcsb.subject_id='"+str(subject_id.msg_id)+"' and bcsb.class_val = '"+str(class_val)+"' and bcsb.is_archived = 'N' order by bd.book_name"
    print(distinctBooks)
    distinctBooks = db.session.execute(text(distinctBooks)).fetchall()
    bookArray=[]
    for val in distinctBooks:
        book_id = BookDetails.query.filter_by(book_name=val.book_name,class_val=class_val).first()
        print(str(book_id.book_id)+':'+str(val.book_name))
        bookArray.append(str(book_id.book_id)+':'+str(val.book_name))
    if bookArray:
        return jsonify([bookArray])  
    else:
        return ""

@app.route('/fetchRemBooks',methods=['GET','POST'])
def fetchRemBooks():
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    
    distinctBooks = ''
    distinctBooks = "select distinct book_name from book_details bd where class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id.msg_id)+"' and "
    distinctBooks = distinctBooks + "book_name not in (select distinct book_name from book_details bd inner join board_class_subject_books bcsb on bd.book_id = bcsb.book_id "
    distinctBooks = distinctBooks + "where bd.class_val = '"+str(class_val)+"' and bd.subject_id = '"+str(subject_id.msg_id)+"' and bcsb.school_id = '"+str(teacher_id.school_id)+"')"
    distinctBooks = db.session.execute(text(distinctBooks)).fetchall()
    distinctBooksInBCSB = "select distinct bd.book_name from book_details bd inner join board_class_subject_books bcsb on "
    distinctBooksInBCSB = distinctBooksInBCSB + "bd.book_id = bcsb.book_id where bcsb.subject_id='"+str(subject_id.msg_id)+"' and bcsb.class_val = '"+str(class_val)+"' and bcsb.school_id='"+str(teacher_id.school_id)+"' and bcsb.is_archived = 'Y' order by bd.book_name"
    distinctBooksInBCSB = db.session.execute(text(distinctBooksInBCSB)).fetchall()
    bookArray=[]
    for val in distinctBooks:
        print(val.book_name)
        book_id = BookDetails.query.filter_by(book_name=val.book_name).first()
        bookArray.append(str(book_id.book_id)+':'+str(val.book_name))
    for value in distinctBooksInBCSB:
        book_id = BookDetails.query.filter_by(book_name=value.book_name).first()
        bookArray.append(str(book_id.book_id)+':'+str(value.book_name))
    if bookArray:
        return jsonify([bookArray])
    else:
        return "" 

@app.route('/selectedChapter',methods=['GET','POST'])
def selectedChapter():
    chapterNum = request.args.get('chapterNum')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    book_id = request.args.get('bookId')
    print('inside selected chapter')
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    book = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_id=book_id).first()
    # chapter = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,chapter_num=chapterNum,book_id=book_id).first()
    chapter = "select chapter_num,chapter_name from topic_detail td inner join book_details bd on td.book_id = bd.book_id where "
    chapter = chapter + "td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id.msg_id)+"' and chapter_num = '"+str(chapterNum)+"' and book_name  = '"+str(book.book_name)+"'"
    print(chapter)
    chapter = db.session.execute(text(chapter)).first()
    # chapter = "select chapter_name,chapter_num from topic_detail td inner join book_details bd on "
    # chapter = chapter + "td.book_id = bd.book_id where td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id.msg_id)+"' and chapter_num = '"+str(chapterNum)+"' and book_name ='"+str(book.book_name)+"'"
    # chapter = db.session.execute(text(chapter)).fetchall()
    selectedChapterArray = []
    # for chapt in chapter:
    selectedChapterArray.append(str(chapter.chapter_name)+':'+str(chapter.chapter_num))
    return jsonify([selectedChapterArray])


@app.route('/fetchRemChapters',methods=['GET','POST'])
def fetchRemChapters():
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    bookId = request.args.get('bookId')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val).first()
    book = BookDetails.query.filter_by(book_id=bookId).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id).all()
    
    chapterArray=[]
    print('Book:'+str(book.book_name)+' class:'+str(class_val)+' subId:'+str(subject_id.msg_id))
    
    queryChapters = "select distinct chapter_name,chapter_num from topic_detail td where td.subject_id = '"+str(subject_id.msg_id)+"' and td.class_val = '"+str(class_val)+"'  and book_id in (select book_id from book_details bd where book_name = '"+str(book.book_name)+"' and subject_id = '"+str(subject_id.msg_id)+"' and class_val = '"+str(class_val)+"') "
    queryChapters = queryChapters + "and td.topic_id not in (select td.topic_id from topic_detail td inner join topic_tracker tt on "
    queryChapters = queryChapters + "td.topic_id = tt.topic_id where td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id.msg_id)+"' and tt.school_id = '"+str(teacher_id.school_id)+"') order by chapter_num"
    print('print chapters from general')
    print(queryChapters)
    queryChapters = db.session.execute(text(queryChapters)).fetchall()
    
            # chapterArray.append(str(chapter.chapter_num)+":"+str(chapter.chapter_name))
    queryBookDetails = "select distinct chapter_name,chapter_num from topic_detail td inner join topic_tracker tt on "
    queryBookDetails = queryBookDetails + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id.msg_id)+"' and tt.school_id='"+str(teacher_id.school_id)+"' and td.class_val = '"+str(class_val)+"' and tt.is_archived = 'Y' and td.book_id in "
    queryBookDetails = queryBookDetails + "(select book_id from book_details bd where class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id.msg_id)+"' and book_name='"+str(book.book_name)+"') order by chapter_num"
    print('deleted chapters')
    print(queryBookDetails)
    queryBookDetails = db.session.execute(text(queryBookDetails)).fetchall()
    j=1
    for chapter in queryChapters:
        chapters = chapter.chapter_name
        chapters = chapters.replace("'","\'")
        num = chapter.chapter_num
        if len(queryChapters)>1:
            if j==1:
                chapters = chapters + "/"
                print(chapters)
            elif j==len(queryChapters):
                if len(queryBookDetails)>0:
                    num = "/"+str(num)
                    chapters = chapters+"/"
                else:
                    num = "/"+str(num)
                    print(chapters)
            else:
                num = "/"+str(num)
                chapters = chapters+"/"
                print(chapters)
            j=j+1
        else:
            if len(queryBookDetails)>0:
                chapters = chapters+"/"
        chapterArray.append(str(num)+":"+str(chapters))
    i=1
    for book in queryBookDetails:
        print('inside for queryBookDetails'+str(len(queryChapters)))
        chapter = book.chapter_name
        chapter = chapter.replace("'","\'")
        num = book.chapter_num
        if len(queryBookDetails)>1:
            if i==1:
                if len(queryChapters)>0:
                    print('if queryChapters is not null')
                    num = "/"+str(num)
                    chapter = chapter + "/"
                else:
                    chapter = chapter + "/"
                    print(chapter)
            elif i==len(queryBookDetails):
                num = "/"+str(num)
                print(chapter)
            else:
                num = "/"+str(num)
                chapter = chapter+"/"
                print(chapter)
            i=i+1
        else:
            if len(queryChapters)>0:
                num = "/"+str(num)
        print(chapter)
        chapterArray.append(str(num)+":"+str(chapter))
    for ch in chapterArray:
        print(ch)
    if chapterArray:
        return jsonify([chapterArray]) 
    else:
        return ""


@app.route('/fetchBooks',methods=['GET','POST'])
def fetchBooks():
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    distinctBooks = "select distinct bd.book_name from book_details bd inner join board_class_subject_books bcsb on "
    distinctBooks = distinctBooks + "bd.book_id = bcsb.book_id where bcsb.school_id='"+str(teacher_id.school_id)+"' and bcsb.subject_id='"+str(subject_id.msg_id)+"' and bcsb.class_val = '"+str(class_val)+"' and bcsb.is_archived = 'N' order by bd.book_name"
    print(distinctBooks)
    distinctBooks = db.session.execute(text(distinctBooks)).fetchall()
    bookArray=[]
    for val in distinctBooks:
        print(val.book_name)
        book_id = BookDetails.query.filter_by(book_name=val.book_name).first()
        bookArray.append(str(book_id.book_id)+':'+str(val.book_name))
    if bookArray:
        return jsonify([bookArray])
    else:
        return ""

@app.route('/generalSyllabusChapters')
def generalSyllabusChapters():
    book_id=request.args.get('book_id')
    class_val=request.args.get('class_val')
    board_id=request.args.get('board_id')
    subject_id=request.args.get('subject_id')
    print('Book id:'+str(book_id))
    class_sec_id = ClassSection.query.filter_by(class_val=class_val).first()
    book = BookDetails.query.filter_by(book_id=book_id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id,board_id=board_id).all()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    chapterArray=[]
    # print('Book:'+str(book.book_name)+' class:'+str(class_val)+' subId:'+str(subject_id)+' boardId:'+str(board_id))
    queryBookDetails = "select distinct chapter_name,chapter_num from topic_detail td where td.subject_id = '"+str(subject_id)+"' and td.class_val = '"+str(class_val)+"' and td.board_id='"+str(board_id)+"' and td.book_id in "
    queryBookDetails = queryBookDetails + "(select book_id from book_details bd where class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id)+"' and book_name='"+str(book.book_name)+"') order by chapter_num"
    print('inside general syllabus chapter:')
    print(queryBookDetails)
    queryBookDetails = db.session.execute(text(queryBookDetails)).fetchall()
    i=1
    for book in queryBookDetails:
        chapter = book.chapter_name
        chapter = chapter.replace("'","\'")
        num = book.chapter_num
        if len(queryBookDetails)>1:
            if i==1:
                chapter = chapter + "/"
                print(chapter)
            elif i==len(queryBookDetails):
                num = "/"+str(num)
                print(chapter)
            else:
                num = "/"+str(num)
                chapter = chapter+"/"
                print(chapter)
            i=i+1
        chapterArray.append(str(num)+":"+str(chapter))
    if chapterArray:
        return jsonify([chapterArray]) 
    else:
        return ""

@app.route('/syllabusChapters') 
@login_required
def syllabusChapters():
    book_id=request.args.get('book_id')
    class_val=request.args.get('class_val')
    board_id=request.args.get('board_id')
    subject_id=request.args.get('subject_id')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    book = BookDetails.query.filter_by(book_id=book_id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id,board_id=board_id).all()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    chapterArray=[]
    print('Book:'+str(book.book_name)+' class:'+str(class_val)+' subId:'+str(subject_id)+' boardId:'+str(board_id))
    queryBookDetails = "select distinct chapter_name,chapter_num from topic_detail td inner join topic_tracker tt on "
    queryBookDetails = queryBookDetails + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id)+"' and tt.school_id='"+str(teacher_id.school_id)+"' and td.class_val = '"+str(class_val)+"' and tt.is_archived = 'N' and td.book_id in "
    queryBookDetails = queryBookDetails + "(select book_id from book_details bd where class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id)+"' and book_name='"+str(book.book_name)+"') order by chapter_num"
    # queryBookDetails = queryBookDetails + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id)+"' and tt.school_id='"+str(teacher_id.school_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' "
    # queryBookDetails = queryBookDetails + "order by chapter_num"
    print(queryBookDetails)
    queryBookDetails = db.session.execute(text(queryBookDetails)).fetchall()
    i=1
    for book in queryBookDetails:
        chapter = book.chapter_name
        chapter = chapter.replace("'","\'")
        num = book.chapter_num
        book = Topic.query.filter_by(chapter_name=book.chapter_name,chapter_num=book.chapter_num).first()
        bookId = book.book_id
        if len(queryBookDetails)>1:
            if i==1:
                bookId = str(bookId) + "/"
                print(chapter)
            elif i==len(queryBookDetails):
                num = "/"+str(num)
                print(chapter)
            else:
                num = "/"+str(num)
                bookId = str(bookId) + "/"
                print(chapter)
            i=i+1
        chapterArray.append(str(num)+":"+str(chapter)+';'+str(book.book_id))
    for chapters in chapterArray:
        print(chapters)
    if chapterArray:
        return jsonify([chapterArray]) 
    else:
        return ""

@app.route('/chapterTopic',methods=['GET','POST'])
def chapterTopic():
    print('inside chapterTopic')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    chapter_num = request.args.get('chapter_num')
    book_id = request.args.get('book_id')
    print('Book id:'+str(book_id))
    print('class value:'+str(class_val))
    try:
        subject_id = MessageDetails.query.filter_by(description=subject).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
        book = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_id=book_id).first()
        print('class:'+str(class_val)+' subject_id:'+str(subject_id.msg_id)+' book_id:'+str(book_id))
        remTopics = "select distinct topic_name ,topic_id from topic_detail td where class_val = '"+str(class_val)+"' and subject_id  = '"+str(subject_id.msg_id)+"' and chapter_num = '"+str(chapter_num)+"' and topic_id not in "
        remTopics = remTopics + "(select distinct td.topic_id from topic_detail td inner join topic_tracker tt on "
        remTopics = remTopics + "td.topic_id = tt.topic_id where td.class_val = '"+str(class_val)+"' and "
        remTopics = remTopics + "td.subject_id = '"+str(subject_id.msg_id)+"' and td.chapter_num = '"+str(chapter_num)+"' and tt.school_id = '"+str(teacher_id.school_id)+"') and book_id in (select book_id from book_details bd where book_name = '"+str(book.book_name)+"' and class_val='"+str(class_val)+"' and subject_id='"+str(subject_id.msg_id)+"') order by topic_id"
        print('inside Rem topics')
        print('Rem Topics:'+str(remTopics))
        remTopics = db.session.execute(text(remTopics)).fetchall()
        topics = "select distinct td.topic_id,td.topic_name from topic_detail td inner join topic_tracker tt on "
        topics = topics + "td.topic_id = tt.topic_id where td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id.msg_id)+"' and td.chapter_num = '"+str(chapter_num)+"' and tt.is_archived = 'Y' and tt.school_id = '"+str(teacher_id.school_id)+"' and td.book_id in (select book_id from book_details bd where book_name = '"+str(book.book_name)+"') order by td.topic_id"
        topics = db.session.execute(text(topics)).fetchall()
    except:
        return ""
    topicArray = []
    i=1
    for topic in topics:
        print('for topic list')
        print(topic.topic_name)
        print(len(remTopics))
        topic_name = topic.topic_name
        topic_name = topic_name.replace("'","\'")
        topic_id = topic.topic_id
        if len(topics)>1:
            if i==1:
                topic_name = topic_name + "/"
            elif i==len(topics):
                if len(remTopics)>0:
                    topic_id = "/"+str(topic_id)
                    topic_name = topic_name + "/"
                else:
                    topic_id = "/"+str(topic_id)
            else:
                topic_id = "/"+str(topic_id)
                topic_name = topic_name+"/"
            i=i+1
        else:
            if len(remTopics)>0:
                topic_name = topic_name+"/"
        topicArray.append(str(topic_id)+":"+str(topic_name))
        # topicArray.append(str(topic.topic_id)+':'+str(topic.topic_name))
    j=1
    for remTopic in remTopics:
        print('rem list')
        print(remTopic.topic_name)
        topic_name = remTopic.topic_name
        topic_name = remTopic.topic_name.replace("'","\'")
        topic_id = remTopic.topic_id
        if len(remTopics)>1:
            if j==1:
                if len(topics)>0:
                    topic_id = "/"+str(topic_id)
                    topic_name = topic_name + "/"
                else:
                    topic_name = topic_name + "/"
            elif j==len(remTopics):
                topic_id = "/"+str(topic_id)
            else:
                topic_id = "/"+str(topic_id)
                topic_name = topic_name+"/"
            j=j+1
        else:
            if len(topics)>0:
                topic_id = "/"+str(topic_id)
        topicArray.append(str(topic_id)+":"+str(topic_name))
        # topicArray.append(str(remTopic.topic_id)+':'+str(remTopic.topic_name))
    for top in topicArray:
        print(top)
    if topicArray:
        return jsonify([topicArray])
    else:
        return ""

@app.route('/fetchChapters',methods=['GET','POST'])
def fetchChapters():
    book_id=request.args.get('bookId')
    print('inside fetchChapters')
    print('Book Id:'+str(book_id))
    class_val=request.args.get('class_val')
    # board_id=request.args.get('board_id')
    subject=request.args.get('subject')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    book = BookDetails.query.filter_by(book_id=book_id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id).all()
    
    chapterArray=[]
    print('Book:'+str(book.book_name)+' class:'+str(class_val)+' subId:'+str(subject_id.msg_id))
    queryBookDetails = "select distinct chapter_name,chapter_num from topic_detail td inner join topic_tracker tt on "
    queryBookDetails = queryBookDetails + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id.msg_id)+"' and tt.school_id='"+str(teacher_id.school_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' and td.book_id in "
    queryBookDetails = queryBookDetails + "(select book_id from book_details bd where class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id.msg_id)+"' and book_name='"+str(book.book_name)+"') order by chapter_num"
    # queryBookDetails = queryBookDetails + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id.msg_id)+"' and tt.school_id='"+str(teacher_id.school_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' "
    # queryBookDetails = queryBookDetails + "order by chapter_num"
    print(queryBookDetails)
    queryBookDetails = db.session.execute(text(queryBookDetails)).fetchall()
    i=1
    for book in queryBookDetails:
        chapter = book.chapter_name
        chapter = chapter.replace("'","\'")
        num = book.chapter_num
        book = Topic.query.filter_by(chapter_name=book.chapter_name,chapter_num=book.chapter_num).first()
        bookId = book.book_id
        if len(queryBookDetails)>1:
            if i==1:
                bookId = str(bookId) + "/"
                print(chapter)
            elif i==len(queryBookDetails):
                num = "/"+str(num)
                print(chapter)
            else:
                num = "/"+str(num)
                bookId = str(bookId) + "/"
                print(chapter)
            i=i+1
        chapterArray.append(str(num)+":"+str(chapter)+';'+str(book.book_id))
    if chapterArray:
        return jsonify([chapterArray]) 
    else:
        return ""

@app.route('/fetchTopics',methods=['GET','POST'])
def fetchTopics():
    subject=request.args.get('subject')
    chapter_num=request.args.get('chapter_num')
    
    class_val = request.args.get('class_val')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    bookId = request.args.get('bookId')
    # chapter_name = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,chapter_num=chapter_num).first()
    book = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_id=bookId).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id,board_id=board_id.board_id).all()
    # topicArray=[]
    # chapter_name = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,chapter_num=chapter_num).first()
    # queryTopics = "select distinct td.topic_id ,td.topic_name from topic_detail td inner join topic_tracker tt on "
    # queryTopics = queryTopics + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id.msg_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' and tt.school_id = '"+str(teacher_id.school_id)+"' and td.topic_id in "
    # queryTopics = queryTopics + "(select topic_id from topic_detail td where subject_id = '"+str(subject_id.msg_id)+"' and class_val = '"+str(class_val)+"' and chapter_name = '"+str(chapter_name.chapter_name)+"') order by td.topic_id"
    # queryTopics = db.session.execute(text(queryTopics)).fetchall()
    # for topic in queryTopics:
    #     topicArray.append(str(topic.topic_id)+":"+str(topic.topic_name))
    # if topicArray:
    #     return jsonify([topicArray]) 
    # else:
    #     return ""
    topicArray=[]
    chapter_name = "select chapter_name,td.book_id from topic_detail td inner join book_details bd on td.book_id = bd.book_id where "
    chapter_name = chapter_name + "td.subject_id = '"+str(subject_id.msg_id)+"' and td.class_val = '"+str(class_val)+"' and td.chapter_num = '"+str(chapter_num)+"' and bd.book_name = '"+str(book.book_name)+"'"
    chapter_name = db.session.execute(text(chapter_name)).first()
    chapterName = chapter_name.chapter_name.replace("'","''")
    queryTopics = "select distinct td.topic_id ,td.topic_name from topic_detail td inner join topic_tracker tt on "
    queryTopics = queryTopics + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id.msg_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' and tt.school_id = '"+str(teacher_id.school_id)+"' and td.topic_id in "
    queryTopics = queryTopics + "(select topic_id from topic_detail td where subject_id = '"+str(subject_id.msg_id)+"' and class_val = '"+str(class_val)+"' and chapter_name = '"+str(chapterName)+"') order by td.topic_id"
    queryTopics = db.session.execute(text(queryTopics)).fetchall()
    i=1
    for topic in queryTopics:
        topic_name = topic.topic_name
        topic_name = topic_name.replace("'","\'")
        topic_id = topic.topic_id
        if len(queryTopics)>1:
            if i==1:
                topic_name = topic_name + "/"
                print(topic_name)
            elif i==len(queryTopics):
                topic_id = "/"+str(topic_id)
            else:
                topic_id = "/"+str(topic_id)
                topic_name = topic_name+"/"
                print(topic_name)
            i=i+1
        topicArray.append(str(topic_id)+":"+str(topic_name))
        # topicArray.append(str(topic.topic_id)+":"+str(topic.topic_name))
    if topicArray:
        return jsonify([topicArray]) 
    else:
        return ""

@app.route('/generalSyllabusTopics',methods=['GET','POST'])
def generalSyllabusTopics():
    subject_id=request.args.get('subject_id')
    board_id=request.args.get('board_id')
    chapter_num=request.args.get('chapter_num')
    bookId = request.args.get('selectedBookId')
    class_val = request.args.get('class_val')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val).first()
    
    print('BookID:'+str(bookId))
    book = BookDetails.query.filter_by(book_id=bookId).first()
    print('book name:')
    print(book.book_name)
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id,board_id=board_id).all()
    topicArray=[]
    chapter_name = "select chapter_name,td.book_id from topic_detail td inner join book_details bd on td.book_id = bd.book_id where "
    chapter_name = chapter_name + "td.subject_id = '"+str(subject_id)+"' and td.class_val = '"+str(class_val)+"' and td.chapter_num = '"+str(chapter_num)+"' and bd.book_name = '"+str(book.book_name)+"'"
    chapter_name = db.session.execute(text(chapter_name)).first()
    # queryTopics = "select distinct td.topic_id ,td.topic_name from topic_detail td inner join topic_tracker tt on "
    # queryTopics = queryTopics + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and td.topic_id in "
    # queryTopics = queryTopics + "(select topic_id from topic_detail td where subject_id = '"+str(subject_id)+"' and class_val = '"+str(class_val)+"' and chapter_name = '"+str(chapter_name.chapter_name)+"') order by td.topic_id"
    chapterName = chapter_name.chapter_name.replace("'","''")
    queryTopics = "select distinct topic_id, topic_name from topic_detail td where class_val = '"+str(class_val)+"' and board_id = '"+str(board_id)+"' and subject_id = '"+str(subject_id)+"' and chapter_name ='"+str(chapterName)+"' order by topic_id"
    print('inside generalsyllabustopics')
    print(queryTopics)
    queryTopics = db.session.execute(text(queryTopics)).fetchall()
    i=1
    for topic in queryTopics:
        topic_name = topic.topic_name
        topic_name = topic_name.replace("'","\'")
        topic_id = topic.topic_id
        if len(queryTopics)>1:
            if i==1:
                topic_name = topic_name + "/"
                print(topic_name)
            elif i==len(queryTopics):
                topic_id = "/"+str(topic_id)
            else:
                topic_id = "/"+str(topic_id)
                topic_name = topic_name+"/"
                print(topic_name)
            i=i+1
        topicArray.append(str(topic_id)+":"+str(topic_name))
    if topicArray:
        return jsonify([topicArray]) 
    else:
        return ""

@app.route('/syllabusTopics')
@login_required
def syllabusTopics():
    subject_id=request.args.get('subject_id')
    board_id=request.args.get('board_id')
    chapter_num=request.args.get('chapter_num')
    bookId = request.args.get('selectedBookId')
    class_val = request.args.get('class_val')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    print('BookID:'+str(bookId))
    book = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id,book_id=bookId).first()
    # bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id,board_id=board_id).all()
    topicArray=[]
    chapter_name = "select chapter_name,td.book_id from topic_detail td inner join book_details bd on td.book_id = bd.book_id where "
    chapter_name = chapter_name + "td.subject_id = '"+str(subject_id)+"' and td.class_val = '"+str(class_val)+"' and td.chapter_num = '"+str(chapter_num)+"' and bd.book_name = '"+str(book.book_name)+"'"
    chapter_name = db.session.execute(text(chapter_name)).first()
    chapterName = chapter_name.chapter_name.replace("'","''")
    queryTopics = "select distinct td.topic_id ,td.topic_name from topic_detail td inner join topic_tracker tt on "
    queryTopics = queryTopics + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' and tt.school_id = '"+str(teacher_id.school_id)+"' and td.topic_id in "
    queryTopics = queryTopics + "(select topic_id from topic_detail td where subject_id = '"+str(subject_id)+"' and class_val = '"+str(class_val)+"' and chapter_name = '"+str(chapterName)+"') order by td.topic_id"
    queryTopics = db.session.execute(text(queryTopics)).fetchall()
    i=1
    print(len(queryTopics))
    for topic in queryTopics:
        topic_name = topic.topic_name
        topic_name = topic_name.replace("'","\'")
        topic_id = topic.topic_id
        if len(queryTopics)>1:
            if i==1:
                topic_name = topic_name + "/"
                print(topic_name)
            elif i==len(queryTopics):
                topic_id = "/"+str(topic_id)
            else:
                topic_id = "/"+str(topic_id)
                topic_name = topic_name+"/"
                print(topic_name)
            i=i+1
        topicArray.append(str(topic_id)+":"+str(topic_name))
    if topicArray:
        return jsonify([topicArray]) 
    else:
        return ""

@app.route('/syllabusQuestionsDetails',methods=['GET','POST'])
def syllabusQuestionsDetails():
    class_val = request.args.get('class_val')
    subject_id = request.args.get('subject_id')
    topic_id = request.args.get('topic_id')
    chapter_num=request.args.get('chapter_num')
    print('inside syllabusQuestionsDetails')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    boardName = MessageDetails.query.filter_by(msg_id=board.board_id).first()
    # questions = QuestionDetails.query.filter_by(subject_id=subject_id,class_val=class_val,topic_id=topic_id).all()
    topic_name = Topic.query.filter_by(topic_id=topic_id,subject_id=subject_id,class_val=class_val).first()
    chapter_name = Topic.query.filter_by(subject_id=subject_id,class_val=class_val,chapter_num=chapter_num).first()
    subQuestion = "select count(*) from question_details qd where subject_id = '"+str(subject_id)+"' and class_val = '"+str(class_val)+"' and topic_id = '"+str(topic_id)+"' and archive_status = 'N' and question_type = 'Subjective'"
    subQuestion = db.session.execute(text(subQuestion)).first()
    objQuestion = "select count(*) from question_details qd where subject_id = '"+str(subject_id)+"' and class_val = '"+str(class_val)+"' and topic_id = '"+str(topic_id)+"' and archive_status = 'N' and question_type = 'MCQ1'"
    objQuestion = db.session.execute(text(objQuestion)).first()
    refContent = "select count(*) from content_detail cd where class_val = '"+str(class_val)+"' and archive_status = 'N' and subject_id = '"+str(subject_id)+"' and topic_id = '"+str(topic_id)+"'"
    refContent = db.session.execute(text(refContent)).first()
    questionDetailsArray = []
    print('subQuestion:'+str(subQuestion[0])+' objQuestion:'+str(objQuestion[0])+' refContent:'+str(refContent[0]))
    # for question in questions:
    #     questionArray.append(question.question_description)
    questionDetailsArray.append(str(topic_name.topic_name)+':'+str(subQuestion[0])+':'+str(objQuestion[0])+':'+str(refContent[0])+':'+str(boardName.description)+':'+str(chapter_name.chapter_name))
    if questionDetailsArray:
        return jsonify([questionDetailsArray])
    else:
        return ""


@app.route('/grantSchoolAdminAccess')
def grantSchoolAdminAccess():
    school_id=request.args.get('school_id')
    teacher_id=request.args.get('teacher_id')
    schoolTableDetails = SchoolProfile.query.filter_by(school_id=school_id).first()
    schoolTableDetails.school_admin=teacher_id
    db.session.commit()
    return jsonify(["String"])


@app.route('/grantUserAccess')
def grantUserAccess():
    username=request.args.get('username')    
    school_id=request.args.get('school_id')
    school=schoolNameVal()
    print("we're in grant access request. ")
    userTableDetails = User.query.filter_by(username=username).first()
    print("#######User Type: "+ str(userTableDetails.user_type))
    userTableDetails.access_status='145'
    userFullName = userTableDetails.first_name + " "+ userTableDetails.last_name
    if userTableDetails.user_type==71:
        print('#########Gotten into 71')
        checkTeacherProfile=TeacherProfile.query.filter_by(user_id=userTableDetails.id).first()
        if checkTeacherProfile==None:
            teacherData=TeacherProfile(teacher_name=userFullName,school_id=school_id, registration_date=datetime.now(), email=userTableDetails.email, phone=userTableDetails.phone, device_preference='195', user_id=userTableDetails.id)
            db.session.add(teacherData)    
            db.session.commit()
    elif userTableDetails.user_type==134:
        print('#########Gotten into 134')
        checkStudentProfile=StudentProfile.query.filter_by(user_id=userTableDetails.id).first()
        if checkStudentProfile==None:
            studentData=StudentProfile(full_name=userFullName,school_id=school_id, registration_date=datetime.now(), last_modified_date=datetime.now(), email=userTableDetails.email, phone=userTableDetails.phone, user_id=userTableDetails.id)
            db.session.add(studentData)    
            db.session.commit()
    elif userTableDetails.user_type==72:
        print('#########Gotten into 72')
        print('Email:'+str(userTableDetails.email))
        checkGuardianProfile=GuardianProfile.query.filter_by(email=userTableDetails.email).all()
        print(checkGuardianProfile)
        if checkGuardianProfile:
            for gprofile in checkGuardianProfile:
                print('If guardian profile is not empty')
                gprofile.user_id=userTableDetails.id
                db.session.commit()
        else:
            print('If guardian profile is empty')
            guardianData=GuardianProfile(full_name=userFullName,first_name=userTableDetails.first_name, last_name=userTableDetails.last_name,email=userTableDetails.email,phone=userTableDetails.phone, user_id=userTableDetails.id)
            db.session.add(guardianData)    
            db.session.commit()
    else:
        print('#########Gotten into else')
        pass
    access_granted_email(userTableDetails.email,userTableDetails.username,school )
    return jsonify(["String"])



@app.route('/questionBank',methods=['POST','GET'])
@login_required
def questionBank():
    topic_list=None
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form=QuestionBankQueryForm()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().order_by(ClassSection.class_val).filter_by(school_id=teacher_id.school_id).all()]
    form.subject_name.choices= ''
    form.chapter_num.choices= ''
    form.test_type.choices= [(i.description,i.description) for i in MessageDetails.query.filter_by(category='Test type').all()]
    if request.method=='POST':
        topic_list=Topic.query.filter_by(class_val=str(form.class_val.data),subject_id=int(form.subject_name.data),chapter_num=int(form.chapter_num.data)).all()
        subject=MessageDetails.query.filter_by(msg_id=int(form.subject_name.data)).first()
        session['class_val']=form.class_val.data
        session['sub_name']=subject.description
        session['test_type_val']=form.test_type.data
        session['chapter_num']=form.chapter_num.data    
        form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(int(form.class_val.data))]
        form.chapter_num.choices= [(int(i['chapter_num']), str(i['chapter_num'])+' - '+str(i['chapter_name'])) for i in chapters(str(form.class_val.data),int(form.subject_name.data))]
        return render_template('questionBank.html',form=form,topics=topic_list,user_type_val=str(current_user.user_type))
    return render_template('questionBank.html',form=form,classSecCheckVal=classSecCheck(),user_type_val=str(current_user.user_type))

@app.route('/visitedQuestions',methods=['GET','POST'])
def visitedQuestions():
    retake = request.args.get('retake')
    questions=[]
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    topicList=request.get_json() 
    for topic in topicList:
        print(str(retake)+'Retake')
        topicFromTracker = TopicTracker.query.filter_by(school_id = teacher_id.school_id, topic_id=int(topic)).first()
        topicFromTracker.is_covered='Y'
        if topicFromTracker.reteach_count:
            topicFromTracker.reteach_count=topicFromTracker.reteach_count+1
        db.session.commit()

    return jsonify(['1'])
    
@app.route('/questionBankQuestions',methods=['GET','POST'])
def questionBankQuestions():
    questions=[]
    topicList=request.get_json()
    for topic in topicList:
        # question_Details=QuestionDetails.query.filter_by(QuestionDetails.topic_id == int(topic)).first()
        # questionList = QuestionDetails.query.join(QuestionOptions, QuestionDetails.question_id==QuestionOptions.question_id).add_columns(QuestionDetails.question_id, QuestionDetails.question_description, QuestionDetails.question_type, QuestionDetails.suggested_weightage).filter(QuestionDetails.topic_id == int(topic)).filter(QuestionOptions.is_correct=='Y').all()
        questionList = QuestionDetails.query.filter_by(topic_id=int(topic),archive_status='N').all()
        questions.append(questionList)
        for q in questionList:
            print("Question List"+str(q))    
    if len(questionList)==0:
        print('returning 1')
        return jsonify(['1'])
    else:
        print('returning template'+ str(questionList))
        return render_template('questionBankQuestions.html',questions=questions)

@app.route('/questionBankFileUpload',methods=['GET','POST'])
def questionBankFileUpload():
    #question_list=request.get_json()
    data=request.get_json()
    question_list=data[0]
    count_marks=data[1]
    document = Document()
    document.add_heading(schoolNameVal(), 0)
    document.add_heading('Class '+session.get('class_val',None)+" - "+session.get('test_type_val',None)+" - "+str(session.get('date',None)) , 1)
    document.add_heading("Subject : "+session.get('sub_name',None),2)
    document.add_heading("Total Marks : "+str(count_marks),3)
    p = document.add_paragraph()
    for question in question_list:
        data=QuestionDetails.query.filter_by(question_id=int(question), archive_status='N').first()
        document.add_paragraph(
            data.question_description, style='List Number'
        )    
        options=QuestionOptions.query.filter_by(question_id=data.question_id).all()
        for option in options:
            if option.option_desc is not None:
                document.add_paragraph(
                    option.option+". "+option.option_desc)     
    #document.add_page_break()
    file_name='S'+'1'+'C'+session.get('class_val',"0")+session.get('sub_name',"0")+session.get('test_type_val',"0")+str(datetime.today().strftime("%d%m%Y"))+'.docx'
    if not os.path.exists('tempdocx'):
        os.mkdir('tempdocx')
    document.save('tempdocx/'+file_name)
    client = boto3.client('s3', region_name='ap-south-1')
    client.upload_file('tempdocx/'+file_name , os.environ.get('S3_BUCKET_NAME'), 'test_papers/{}'.format(file_name),ExtraArgs={'ACL':'public-read'})
    os.remove('tempdocx/'+file_name)

    return render_template('testPaperDisplay.html',file_name='https://'+os.environ.get('S3_BUCKET_NAME')+'.s3.ap-south-1.amazonaws.com/test_papers/'+file_name)

@app.route('/testBuilder',methods=['POST','GET'])
@login_required
def testBuilder():
    topic_list=None
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form=TestBuilderQueryForm()
    print(teacher_id.school_id)
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().order_by(ClassSection.class_val).filter_by(school_id=teacher_id.school_id).all()]
    form.subject_name.choices= ''
    form.chapter_num.choices= ''
    # [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.test_type.choices= [(i.description,i.description) for i in MessageDetails.query.filter_by(category='Test type').all()]
    test_papers = MessageDetails.query.filter_by(category='Test type').all()
    # print(request.form['class_val'])
    # print(request.form['subject_id'])
    available_class = "select distinct class_val from class_section where school_id='"+str(teacher_id.school_id)+"'"
    available_class = db.session.execute(text(available_class)).fetchall()
    if request.method=='POST':
        if request.form['test_date']=='':
            # flash('Select Date')
            # form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(int(form.class_val.data))]
            return render_template('testBuilder.html',form=form)
        topic_list=Topic.query.filter_by(class_val=str(form.class_val.data),subject_id=int(form.subject_name.data),chapter_num=int(form.chapter_num.data)).all()
        subject=MessageDetails.query.filter_by(msg_id=int(form.subject_name.data)).first()
        session['class_val']=form.class_val.data
        session['date']=request.form['test_date']
        session['sub_name']=subject.description
        session['sub_id']=form.subject_name.data
        session['test_type_val']=form.test_type.data
        session['chapter_num']=form.chapter_num.data 
        form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(str(form.class_val.data))]
        form.chapter_num.choices= [(int(i['chapter_num']), str(i['chapter_num'])+' - '+str(i['chapter_name'])) for i in chapters(str(form.class_val.data),int(form.subject_name.data))]
        return render_template('testBuilder.html',form=form,topics=topic_list,user_type_val=str(current_user.user_type))
    return render_template('testBuilder.html',form=form,available_class=available_class,test_papers=test_papers,classSecCheckVal=classSecCheck(),user_type_val=str(current_user.user_type))

@app.route('/filterQuestionsfromTopic',methods=['GET','POST'])
def filterQuestionsfromTopic():
    topics = request.get_json()
    for topic in topics:
        print('topic:'+str(topic))
    class_val = request.args.get('class_val')
    subject_id = request.args.get('subject_id')
    test_type = request.args.get('test_type')
    print('Class feedback:'+str(test_type))
    questions = []
    if topics:
        for topic in topics:
            if test_type == 'Class Feedback':
                if class_val!=None:
                    if subject_id!=None:
                        questionList = QuestionDetails.query.filter_by(class_val = str(class_val),subject_id=subject_id,archive_status='N',topic_id=topic,question_type='MCQ1').all()
                    else:
                        questionList = QuestionDetails.query.filter_by(class_val = str(class_val),archive_status='N',topic_id=topic,question_type='MCQ1').all()
                else:
                    if subject_id!=None:
                        questionList = QuestionDetails.query.filter_by(archive_status='N',subject_id=subject_id,topic_id=topic,question_type='MCQ1').all()
                    else:
                        questionList = QuestionDetails.query.filter_by(archive_status='N',topic_id=topic,question_type='MCQ1').all()
            else:
                if class_val!=None:
                    if subject_id!=None:
                        questionList = QuestionDetails.query.filter_by(class_val = str(class_val),subject_id=subject_id,archive_status='N',topic_id=topic).all()
                    else:
                        questionList = QuestionDetails.query.filter_by(class_val = str(class_val),archive_status='N',topic_id=topic).all()
                else:
                    if subject_id!=None:
                        questionList = QuestionDetails.query.filter_by(archive_status='N',subject_id=subject_id,topic_id=topic).all()
                    else:
                        questionList = QuestionDetails.query.filter_by(archive_status='N',topic_id=topic).all() 
            if questionList:  
                questions.append(questionList)
    else:
        if test_type == 'Class Feedback':
            if class_val!=None:
                if subject_id!=None:
                    questionList = QuestionDetails.query.filter_by(class_val = str(class_val),subject_id=subject_id,archive_status='N',question_type='MCQ1').all()
                else:
                    questionList = QuestionDetails.query.filter_by(class_val = str(class_val),archive_status='N',question_type='MCQ1').all()
            else:
                if subject_id!=None:
                    questionList = QuestionDetails.query.filter_by(archive_status='N',subject_id=subject_id,question_type='MCQ1').all()
                else:
                    questionList = QuestionDetails.query.filter_by(archive_status='N',question_type='MCQ1').all()
        else:
            if class_val!=None:
                if subject_id!=None:
                    questionList = QuestionDetails.query.filter_by(class_val = str(class_val),subject_id=subject_id,archive_status='N').all()
                else:
                    questionList = QuestionDetails.query.filter_by(class_val = str(class_val),archive_status='N').all()
            else:
                if subject_id!=None:
                    questionList = QuestionDetails.query.filter_by(archive_status='N',subject_id=subject_id).all()
                else:
                    questionList = QuestionDetails.query.filter_by(archive_status='N').all() 
        return render_template('testBuilderQuestions.html',questions=questionList)
    if len(questions)==0:
        print('returning 1')
        return jsonify(['1']) 
    else:
        return render_template('testBuilderQuestions.html',questions=questions,flagTopic = 'true')


@app.route('/fetchRequiredQues',methods=['GET','POST'])
def fetchRequiredQues():
    class_val = request.args.get('class_val')
    subject_id = request.args.get('subject_id')
    
    if class_val!=None:
        if subject_id!=None:
            questionList = QuestionDetails.query.filter_by(class_val = str(class_val),subject_id=subject_id,archive_status='N').all()
        else:
            questionList = QuestionDetails.query.filter_by(class_val = str(class_val),archive_status='N').all()
    else:
        if subject_id!=None:
            questionList = QuestionDetails.query.filter_by(archive_status='N',subject_id=subject_id).all()
        else:
            questionList = QuestionDetails.query.filter_by(archive_status='N').all()
    if len(questionList)==0:
        print('returning 1')
        return jsonify(['1'])
    else:
        print('returning template'+ str(questionList))
        return render_template('testBuilderQuestions.html',questions=questionList)

@app.route('/testBuilderQuestions',methods=['GET','POST'])  
def testBuilderQuestions():
    questions=[]
    topicList=request.get_json()
    for topic in topicList:
        # questionList = QuestionDetails.query.join(QuestionOptions, QuestionDetails.question_id==QuestionOptions.question_id).add_columns(QuestionDetails.question_id, QuestionDetails.question_description, QuestionDetails.question_type, QuestionOptions.weightage).filter(QuestionDetails.topic_id == int(topic),QuestionDetails.archive_status=='N' ).filter(QuestionOptions.is_correct=='Y').all()
        questionList = QuestionDetails.query.filter_by(topic_id = int(topic),archive_status='N').all()
        questions.append(questionList)
    if len(questionList)==0:
        print('returning 1')
        return jsonify(['1'])
    else:
        print('returning template'+ str(questionList))
        return render_template('testBuilderQuestions.html',questions=questions)

@app.route('/testBuilderFileUpload',methods=['GET','POST'])
def testBuilderFileUpload():
    class_val = request.args.get('class_val')
    test_type = request.args.get('test_type')
    subject_id = request.args.get('subject_id')
    subject_name = MessageDetails.query.filter_by(msg_id=subject_id).first()
    date = request.args.get('date')
    print('class_val:'+str(class_val))
    print('test_type:'+str(test_type))
    print('subject_id:'+str(subject_id))
    print('Date:'+str(date))
    print('Inside Test builder file upload Test Type value:'+str(test_type))
    #question_list=request.get_json()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id = teacher_id.school_id).first()
    data=request.get_json()
    question_list=data[0]
    count_marks=data[1]
    document = Document()
    print('Date')
    print(date)
    document.add_heading(schoolNameVal(), 0)
    document.add_heading('Class '+str(class_val)+" - "+str(test_type)+" - "+str(date) , 1)
    document.add_heading("Subject : "+str(subject_name.description),2)
    document.add_heading("Total Marks : "+str(count_marks),3)
    p = document.add_paragraph()
    #For every selected question add the question description
    for question in question_list:
        data=QuestionDetails.query.filter_by(question_id=int(question), archive_status='N').first()
        #for every question add it's options
        options=QuestionOptions.query.filter_by(question_id=data.question_id).all()
        #add question desc
        document.add_paragraph(
            data.question_description, style='List Number'
        )    
    #Add the image associated with the question
        if data.reference_link!='' and data.reference_link!=None:
            try:
                response = requests.get(data.reference_link, stream=True)
                image = BytesIO(response.content)
                document.add_picture(image, width=Inches(1.25))
            except:
                pass

        for option in options:
            if option.option_desc is not None:
                document.add_paragraph(
                    option.option+". "+option.option_desc)     
    #document.add_page_break()
    #naming file here
    file_name=str(teacher_id.school_id)+str(class_val)+str(subject_name.description)+str(test_type)+str(datetime.today().strftime("%Y%m%d"))+str(count_marks)+'.docx'
    file_name = file_name.replace(" ", "")
    if not os.path.exists('tempdocx'):
        os.mkdir('tempdocx')
    document.save('tempdocx/'+file_name)
    #uploading to s3 bucket
    client = boto3.client('s3', region_name='ap-south-1')
    client.upload_file('tempdocx/'+file_name , os.environ.get('S3_BUCKET_NAME'), 'test_papers/{}'.format(file_name),ExtraArgs={'ACL':'public-read'})
    #deleting file from temporary location after upload to s3
    os.remove('tempdocx/'+file_name)

    ###### Inserting record in the Test Detail table
    file_name_val='https://'+os.environ.get('S3_BUCKET_NAME')+'.s3.ap-south-1.amazonaws.com/test_papers/'+file_name

    testDetailsUpd = TestDetails(test_type=str(test_type), total_marks=str(count_marks),last_modified_date= datetime.now(),
        board_id=str(board_id.board_id), subject_id=int(subject_id),class_val=str(class_val),date_of_creation=datetime.now(),
        date_of_test=str(date), school_id=teacher_id.school_id,test_paper_link=file_name_val, teacher_id=teacher_id.teacher_id)
    db.session.add(testDetailsUpd)
    db.session.commit()

    ##### This section to insert values into test questions table #####
    #try:
    createdTestID = TestDetails.query.filter_by(teacher_id=teacher_id.teacher_id).order_by(TestDetails.last_modified_date.desc()).first()
    for questionVal in question_list:
        testQuestionInsert= TestQuestions(test_id=createdTestID.test_id, question_id=questionVal, last_modified_date=datetime.now())
        db.session.add(testQuestionInsert)
    db.session.commit()
    #except:
    #    print('error inserting values into the test questions table')
    #### End of section ####
    testPaperData= TestDetails.query.filter_by(school_id=teacher_id.school_id,teacher_id=teacher_id.teacher_id).order_by(TestDetails.date_of_creation.desc()).first()
    return render_template('testPaperDisplay.html',file_name=file_name_val,testPaperData=testPaperData)

@app.route('/testPapers')
@login_required
def testPapers():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()    
    testPaperData= TestDetails.query.filter_by(school_id=teacher_id.school_id).order_by(TestDetails.date_of_creation.desc()).all()
    subjectNames=MessageDetails.query.filter_by(category='Subject')

    return render_template('testPapers.html',testPaperData=testPaperData,subjectNames=subjectNames,classSecCheckVal=classSecCheck(),user_type_val=str(current_user.user_type))

@app.route('/getChapterDetails')
def getChapterDetails():
    qtest_id=request.args.get('test_id')
    getChapterQuery = "select distinct topic_name, chapter_name, chapter_num from test_questions tq "
    getChapterQuery= getChapterQuery+ "inner join question_details qd  on "
    getChapterQuery= getChapterQuery+ " qd.question_id=tq.question_id inner join "
    getChapterQuery= getChapterQuery+ " topic_detail td on td.topic_id=qd.topic_id "
    getChapterQuery= getChapterQuery+ "where tq.test_id='"+str(qtest_id)+"'"

    getChapterRows = db.session.execute(text(getChapterQuery)).fetchall()

    return render_template('_getChapterDetails.html', getChapterRows=getChapterRows)

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@app.route('/schoolPerformanceRanking')
@login_required
def schoolPerformanceRanking():
    return render_template('schoolPerformanceRanking.html')

@app.route('/recommendations')
@login_required
def recommendations():
    return render_template('recommendations.html')


@app.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html')

@app.route('/guardianDashboard')
@login_required
def guardianDashboard():
    print('Id:'+str(current_user.id))
    user_type_val = ''
    if current_user.user_type==72:
        user_type_val = 72
        print('User Type:'+str(user_type_val))
    guardian=GuardianProfile.query.filter_by(user_id=current_user.id).all()
    print(guardian)
    print('Id:'+str(current_user.id))
    school= User.query.filter_by(id=current_user.id).first()
    student=[]
    
    for g in guardian:
        if g.student_id!=None:
            query = "select fn.score as marks,fn.strong_2_subjects as subjects,sp.full_name as student,spro.school_name as school,cs.class_val as class,cs.section as section,sp.profile_picture as pic,sp.student_id from student_profile sp "
            query = query + "inner join class_section cs on cs.class_sec_id=sp.class_sec_id "
            query = query + "left join fn_guardian_dashboard_summary('"+str(school.school_id)+"') fn on fn.student_name=sp.full_name "
            query = query + "inner join school_profile spro on spro.school_id = sp.school_id where student_id='"+str(g.student_id)+"' order by marks desc limit 1"
            student_data = db.session.execute(text(query)).first()
            student.append(student_data)
    
    return render_template('guardianDashboard.html',students=student,disconn = 1,user_type_val=user_type_val)

@app.route('/performanceDetails/<student_id>',methods=['POST','GET'])
@login_required
def performanceDetails(student_id):
    user = User.query.filter_by(username=current_user.username).first_or_404()        
    teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
    form1=studentPerformanceForm()
    
    available_class=ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher.school_id).all()
    available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher.school_id).all()    
    available_test_type=MessageDetails.query.filter_by(category='Test type').all()
    available_student_list=StudentProfile.query.filter_by(school_id=teacher.school_id).all()


    class_list=[(str(i.class_val), "Class "+str(i.class_val)) for i in available_class]
    section_list=[(i.section,i.section) for i in available_section]    
    test_type_list=[(i.msg_id,i.description) for i in available_test_type]
    student_list=[(i.student_id,i.full_name) for i in available_student_list]

    #selectfield choices
    form1.class_val1.choices = class_list
    form1.section1.choices= section_list    
    form1.test_type1.choices=test_type_list
    form1.student_name1.choices = student_list

    student=StudentProfile.query.filter_by(student_id=student_id).first()
    if request.method=='POST':
        student=StudentProfile.query.filter_by(student_id=student_id).first()
        class_sec=ClassSection.query.filter_by(class_sec_id=student.class_sec_id).first()
        subject=subjectPerformance(class_sec.class_val,class_sec.school_id)
        print(subject)
        date=request.form['performace_date']        


        return render_template('studentPerfDetails.html',date=date,subjects=subject,students=student)
    return render_template('performanceDetails.html',students=student, student_id=student_id,form1=form1)


@app.route('/studentfeedbackreporttemp')
def studentfeedbackreporttemp():
    student_name=request.args.get('student_name')
    return render_template('studentfeedbackreporttemp.html',student_name=student_name)

@app.route('/unpaidStudentsList',methods=["GET","POST"])
def unpaidStudentsList():
    class_val = request.args.get('class_val')
    section = request.args.get('section')
    
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,section=section,school_id=teacherData.school_id).first()
    studentData = "select sp.full_name from student_profile sp where class_sec_id ='"+str(class_sec_id.class_sec_id)+"' and school_id='"+str(teacherData.school_id)+"' and student_id not in (select student_id from fee_detail where paid_status='Y' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and school_id='"+str(teacherData.school_id)+"')"
    print(studentData)
    studentList = db.session.execute(text(studentData)).fetchall()
    return render_template('_studentList.html',studentList=studentList)

@app.route('/sendFeeSMS',methods=["GET","POST"])
def sendFeeSMS():
    if request.method=="POST":
        commType = request.form.get('commType')
        message = request.form.get('message')
        class_val = request.form.get('qclass_val')
        section = request.form.get('qsection')
        teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
        class_sec = ClassSection.query.filter_by(school_id=teacherData.school_id,class_val=class_val,section=section).first()
        class_sec_id = class_sec.class_sec_id
        if class_sec_id !=None and class_sec_id !="":
            commDataAdd=CommunicationDetail(message = message,status=231 , school_id=teacherData.school_id,             
            teacher_id=teacherData.teacher_id,last_modified_date =datetime.today())
            db.session.add(commDataAdd)
            #db.session.flush()
            db.session.commit()
            getStudNumQuery = "select student_id , phone from student_profile sp where class_sec_id ='"+str(class_sec_id)+"' and school_id='"+str(teacherData.school_id)+"' and student_id not in (select student_id from fee_detail where paid_status='Y' and class_sec_id='"+str(class_sec_id)+"' and school_id='"+str(teacherData.school_id)+"')"            
            studentPhones = db.session.execute(getStudNumQuery).fetchall()
            phoneList =[]
            for phoneRow in studentPhones:
                if phoneRow.phone!=None and phoneRow.phone!='':
                    phoneList.append(phoneRow.phone)
            if studentPhones!=None:
                if commType=='sms':
                    apiPath = "http://173.212.233.109/app/smsapisr/index.php?key=35EF8379A04DB8&"
                    apiPath = apiPath + "campaign=9967&routeid=6&type=text&"
                    apiPath = apiPath + "contacts="+str(phoneList).replace('[','').replace(']','').replace('\'','').replace(' ','')+"&senderid=GLOBAL&"
                    apiPath = apiPath + "msg="+ quote(message)
                    print(apiPath)
                    ##Sending message here
                    try:
                        r = requests.post(apiPath)                    
                        returnData = str(r.text)
                        print(returnData)
                        if "SMS-SHOOT-ID" in returnData:
                            for val in studentPhones:
                                commTransAdd = CommunicationTransaction(comm_id=commDataAdd.comm_id, student_id=val.student_id,last_modified_date = datetime.today())
                                db.session.add(commTransAdd)
                            commDataAdd.status=232
                            db.session.commit()                                        
                            return jsonify(['0'])
                        else:
                            return jsonify(['1'])                    
                    except:
                        return jsonify(['1'])
                    ##Message sent 
    return jsonify(['1']) 

@app.route('/sendComm',methods=["GET","POST"])
def sendComm():
    if request.method=="POST":
        commType = request.form.get('commType')
        message = request.form.get('message')
        class_sec_id = request.form.get('class_sec_id')
        if class_sec_id !=None and class_sec_id !="":
            teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
            #insert into communication detail table
            commDataAdd=CommunicationDetail(message = message,status=231 , school_id=teacherData.school_id,             
            teacher_id=teacherData.teacher_id,last_modified_date =datetime.today())
            db.session.add(commDataAdd)
            #db.session.flush()
            db.session.commit() 
            getStudNumQuery = "select student_id, phone from student_profile sp where class_sec_id ="+ str(class_sec_id)            
            studentPhones = db.session.execute(getStudNumQuery).fetchall()
            phoneList =[]
            for phoneRow in studentPhones:
                if phoneRow.phone!=None and phoneRow.phone!='':
                    phoneList.append(phoneRow.phone)
            if studentPhones!=None:
                if commType=='sms':
                    apiPath = "http://173.212.233.109/app/smsapisr/index.php?key=35EF8379A04DB8&"
                    apiPath = apiPath + "campaign=9967&routeid=6&type=text&"
                    apiPath = apiPath + "contacts="+str(phoneList).replace('[','').replace(']','').replace('\'','').replace(' ','')+"&senderid=GLOBAL&"
                    apiPath = apiPath + "msg="+ quote(message)
                    print(apiPath)
                    ##Sending message here
                    try:
                        r = requests.post(apiPath)                    
                        returnData = str(r.text)
                        print(returnData)
                        if "SMS-SHOOT-ID" in returnData:
                            for val in studentPhones:
                                commTransAdd = CommunicationTransaction(comm_id=commDataAdd.comm_id, student_id=val.student_id,last_modified_date = datetime.today())
                                db.session.add(commTransAdd)
                            commDataAdd.status=232
                            db.session.commit()                                        
                            return jsonify(['0'])
                        else:
                            return jsonify(['1'])                    
                    except:
                        return jsonify(['1'])
                    ##Message sent                    
    return jsonify(['1'])


@app.route('/class')
@login_required
def classCon(): 
    if current_user.is_authenticated:        
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
        qclass_val = request.args.get('class_val')
        qsection=request.args.get('section')

        #db query

        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).all()
        count = 0
        for section in classSections:
            #print("Class Section:"+section.section)
            #this section is to load the page for the first class section if no query value has been provided
            if count==0:
                getClassVal = section.class_val
                getSection = section.section
                count+=1

        distinctClasses = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacher.school_id)+" GROUP BY class_val order by s")).fetchall()
        #if no value has been passed for class and section in query string then use the values fetched from db
        if qclass_val==None:
            qclass_val = getClassVal
            qsection=getSection
            
        selectedClassSection=ClassSection.query.filter_by(school_id=teacher.school_id, class_val=str(qclass_val), section=qsection).order_by(ClassSection.class_val).first()
        topicTrackerQuery = "with cte_total_topics as "
        topicTrackerQuery = topicTrackerQuery + "(select subject_id,  "
        topicTrackerQuery = topicTrackerQuery +"count(is_covered) as total_topics , max(last_modified_Date) as last_updated_date "
        topicTrackerQuery = topicTrackerQuery +"  from topic_tracker where class_sec_id = '"+ str(selectedClassSection.class_sec_id)+"' group by subject_id)  "
        topicTrackerQuery = topicTrackerQuery +"select c1.subject_id,  t2.description as subject_name, c1.last_updated_date, "
        topicTrackerQuery = topicTrackerQuery +"CASE WHEN COUNT(t1.subject_id) <> 0 THEN COUNT(c1.subject_id) ELSE 0 END "
        topicTrackerQuery = topicTrackerQuery +"topics_covered, c1.total_topics  "
        topicTrackerQuery = topicTrackerQuery +"from topic_tracker t1  "
        topicTrackerQuery = topicTrackerQuery +"right outer join cte_total_topics c1  "
        topicTrackerQuery = topicTrackerQuery +"on c1.subject_id=t1.subject_id and class_sec_id= '"+ str(selectedClassSection.class_sec_id)+"'  "
        topicTrackerQuery = topicTrackerQuery +"and t1.is_covered='Y'  "
        topicTrackerQuery = topicTrackerQuery +"inner join   "
        topicTrackerQuery = topicTrackerQuery +"message_detail t2 on   "
        topicTrackerQuery = topicTrackerQuery +"c1.subject_id=t2.msg_id  "
        topicTrackerQuery = topicTrackerQuery +"group by c1.subject_id, t2.description, c1.total_topics,  c1.last_updated_date"                
        topicRows  = db.session.execute(text(topicTrackerQuery)).fetchall()
        #print('this is the number of topicRows' + str(len(topicRows)))

        ##Section for login info
        loginDataQuery = "select *from fn_student_last_login("+str(selectedClassSection.class_sec_id)+")"
        loginData = db.session.execute(loginDataQuery).fetchall()
        ##
        
        #Summary query
        summaryQuery = "with perfCTE as(select round(avg(student_score ),2) as avgClassPerfomance "
        summaryQuery = summaryQuery + " from performance_detail pd where class_sec_id ="+ str(selectedClassSection.class_sec_id)
        summaryQuery = summaryQuery + "), studCountCTE as (select count(student_id) studcount from student_profile "
        summaryQuery = summaryQuery + " sp where class_sec_id =" + str(selectedClassSection.class_sec_id) 
        summaryQuery = summaryQuery + ") select t1.avgclassperfomance as avgclassperfomance, t2.studcount as studcount "
        summaryQuery = summaryQuery +" from perfCTE t1, studCountCTE t2"
        #print(summaryQuery)
        summaryData = db.session.execute(text(summaryQuery)).first()
        # End of query section 
        
        return render_template('class.html', classSecCheckVal=classSecCheck(),classsections=classSections,summaryData=summaryData, 
            qclass_val=qclass_val, qsection=qsection, class_sec_id=selectedClassSection.class_sec_id, distinctClasses=distinctClasses,
            topicRows=topicRows, user_type_val=str(current_user.user_type), loginData=loginData)
    else:
        return redirect(url_for('login'))    

@app.route('/topicList')
def topicList():
    class_sec_id = request.args.get('class_sec_id','1')
    subject_id = request.args.get('subject_id','15')
    #topicList = TopicTracker.query.filter_by(subject_id=subject_id, class_sec_id=class_sec_id).all()
    topicListQuery = "select t1.subject_id, t3.description as subject_name, t1.topic_id, t2.topic_name,t1.is_covered, "
    topicListQuery = topicListQuery + "t2.chapter_num, t2.unit_num, t4.book_name from topic_tracker t1 "
    topicListQuery = topicListQuery + "inner join topic_detail t2 on t1.topic_id=t2.topic_id "
    topicListQuery = topicListQuery + "inner join message_detail t3 on t1.subject_id=t3.msg_id "
    topicListQuery = topicListQuery + "inner join book_details t4 on t4.book_id=t2.book_id "
    topicListQuery = topicListQuery + "where t1.subject_id = '" + subject_id+"' and t1.class_sec_id='" +class_sec_id+"' order by  t2.chapter_num, is_covered desc"
    topicList= db.session.execute(text(topicListQuery)).fetchall()

    return render_template('_topicList.html', topicList=topicList, class_sec_id=class_sec_id)



@app.route('/qrSessionScanner')
@login_required
def qrSessionScanner():
    return render_template('qrSessionScanner.html')


@app.route('/qrSessionScannerStudent')
@login_required
def qrSessionScannerStudent():
    studentDetails = StudentProfile.query.filter_by(user_id=current_user.id).first()
    return render_template('qrSessionScannerStudent.html',user_type_val=str(current_user.user_type),studentDetails=studentDetails)



@app.route('/viewHomework')
@login_required
def viewHomework():
    return render_template('viewHomework.html')

@app.route('/mobFeedbackCollection', methods=['GET', 'POST'])
def mobQuestionLoader():

    resp_session_id=request.args.get('resp_session_id')
    print('Response Session Id in mobFeedbackCollection:'+str(resp_session_id))
    sessionDetailRow = SessionDetail.query.filter_by(resp_session_id=str(resp_session_id)).first()
    if sessionDetailRow:
        if sessionDetailRow.session_status=='80':
            sessionDetailRow.session_status='81'        
            db.session.commit()    
        classSectionRow = ClassSection.query.filter_by(class_sec_id=sessionDetailRow.class_sec_id).first()        
        testDetailRow = TestDetails.query.filter_by(test_id = sessionDetailRow.test_id).first()
        testQuestions = TestQuestions.query.filter_by(test_id=sessionDetailRow.test_id).all()

        if testQuestions!=None:
            questionListSize = len(testQuestions)
        return render_template('mobFeedbackCollection.html',class_val = classSectionRow.class_val, 
            section=classSectionRow.section,questionListSize=questionListSize,
            resp_session_id=str(resp_session_id), questionList=testQuestions, subject_id=testDetailRow.subject_id, test_type=testDetailRow.test_type,disconn=1)
    else:
        flash('This is not a valid id')
        return render_template('qrSessionScanner.html')




@app.route('/startPracticeTest', methods=['GET', 'POST'])
def startPracticeTest():
    #topics = request.get_json()
    #for topic in topics:
    
    topics = request.args.getlist('topics')
    print('topic:'+str(topics))
    topicsList = str(topics).replace('[','').replace(']','').replace('\'','')
    difficulty = request.args.get('difficulty')    
    qcount = request.args.get('qcount')
    subject_id = request.args.get('subject_id')
    class_val = request.args.get('class_val')
    print('difficulty:'+str(difficulty))
    print('qcount:'+str(qcount))
    print('subject_id:'+str(subject_id))
    print('class_val:'+str(class_val))
    #subject_id
    #board_id = request.args.get('board_id')
    #topicList = request.form.getlist('topicList')adsfsdfasdf

    if current_user.is_anonymous:
        print('for anonymous user')
        studentData = StudentProfile.query.filter_by(user_id=app.config['ANONYMOUS_USERID']).first()
    else:
        print('for student:'+str(current_user.id))
        studentData = StudentProfile.query.filter_by(user_id=current_user.id).first()
    schoolData = SchoolProfile.query.filter_by(school_id = studentData.school_id).first()
    classSecData = ClassSection.query.filter_by(school_id=studentData.school_id, class_val=str(class_val)).first()
    #Collection Questions
    questions = []
    total_marks = 0
    questionIDList = []
    if topics:
        #for topic in topics:
            #questionList = QuestionDetails.query.filter_by(archive_status='N',topic_id=topic,question_type='MCQ1').all()
        questionListQuery = "select *from question_details where archive_status='N' and question_type='MCQ1' and topic_id in (" + str(topicsList) + ")"
        questionListQuery = questionListQuery + " order by random() " #limit " +  str(qcount)
        questionList = db.session.execute(text(questionListQuery)).fetchall()
        if questionList:  
            for q in questionList:
                if len(questions)< int(qcount):
                    questions.append(q)  
    for val in questions:        
        print(str(val))
        total_marks = total_marks + val.suggested_weightage
        questionIDList.append(val.question_id)
    ##Create test
    testDetailsAdd = TestDetails(test_type='238', total_marks=str(total_marks),last_modified_date= datetime.today(),
        board_id=str(schoolData.board_id), subject_id=int(subject_id),class_val=str(class_val),date_of_creation=datetime.today(),
        date_of_test=str(datetime.today()), school_id=studentData.school_id)        
    db.session.add(testDetailsAdd)
    if current_user.is_anonymous==False:
        if studentData.points:
            studentData.points= int(studentData.points) + 1
    db.session.commit()
    print('test_id:'+str(testDetailsAdd.test_id))
    print('Data feed to test details complete')

    ##### This section to insert values into test questions table #####        
    for questionVal in questions:
        testQuestionInsert= TestQuestions(test_id=testDetailsAdd.test_id, question_id=questionVal.question_id, last_modified_date=datetime.now())
        db.session.add(testQuestionInsert)
    db.session.commit()
    
    print('Data feed to test questions complete')
    ##Create response session ID
    dateVal= datetime.today().strftime("%d%m%Y%H%M%S")
    #if current_user.is_anonymous:
    responseSessionID = str(subject_id).strip()+ str(dateVal).strip() + str(classSecData.class_sec_id).strip()
    #else:
    #    responseSessionID = str(subject_id).strip()+ str(dateVal).strip() + str(studentData.class_sec_id).strip()
    print('resp session id:'+str(responseSessionID))
    print('Response ID generated')
    #print("This is the value of anon user before setup: " + session['anonUser'])
    #if session['anonUser']:
    #    print('###########session is true')
    #    print(session['anonUser'])
    #else:
    #    print('###########session is false')
    #    print(session['anonUser'])
    if current_user.is_anonymous:
        if session.get('anonUser'):
            print('the anon user is true')
            #this section forces a user to take an unsigned test only once
            #flash('Please login to start any further tests') 
            #return jsonify(['2']) 
        else:
            session['anonUser'] = "user_"+ str(responseSessionID) + '_'+str(random.randint(1,100))
            print("This is the value of anon user: " + session['anonUser'])            
    else:
        print('last segment. anon user is false')
        session['anonUser']==False

    ##Create session
    if len(questions) >0:        
        sessionDetailRowInsert=SessionDetail(resp_session_id=responseSessionID,session_status='80',
            class_sec_id=classSecData.class_sec_id,test_id=testDetailsAdd.test_id, last_modified_date=datetime.today(),correct_marks=10,incorrect_marks=0,test_time=0,total_marks=total_marks )
        db.session.add(sessionDetailRowInsert)
        db.session.commit()        

        print('Data feed to session detail completed')
        ## Start test
        return jsonify([responseSessionID])    
    else:
        return jsonify(['1'])    


@app.route('/feedbackCollectionStudDev', methods=['GET', 'POST'])
def feedbackCollectionStudDev():
    resp_session_id=request.args.get('resp_session_id')
    print('Response Session Id:'+str(resp_session_id))
    sessionDetailRow = SessionDetail.query.filter_by(resp_session_id=str(resp_session_id)).first()
    if sessionDetailRow!=None:
        print("This is the session status - "+str(sessionDetailRow.session_status))
        if sessionDetailRow.session_status=='80':
            sessionDetailRow.session_status='81'        
            db.session.commit()    
        classSectionRow = ClassSection.query.filter_by(class_sec_id=sessionDetailRow.class_sec_id).first()        
        testDetailRow = TestDetails.query.filter_by(test_id = sessionDetailRow.test_id).first()
        testQuestions = TestQuestions.query.filter_by(test_id=sessionDetailRow.test_id).all()

        if testQuestions!=None:
            questionListSize = len(testQuestions)
        return render_template('feedbackCollectionStudDev.html',class_val = classSectionRow.class_val, 
            section=classSectionRow.section,questionListSize=questionListSize,
            resp_session_id=str(resp_session_id), questionList=testQuestions, subject_id=testDetailRow.subject_id, test_type=testDetailRow.test_type,disconn=1)
    else:
        flash('This is not a valid id or there are no question in this test')
        return redirect('index')
        #return render_template('qrSessionScannerStudent.html',disconn=1)


@app.route('/updateQuestion')
def updateQuestion():
    question_id = request.args.get('question_id')
    updatedCV = request.args.get('updatedCV')
    topicId = request.args.get('topicName')
    subId = request.args.get('subName')
    qType = request.args.get('qType')
    qDesc = request.args.get('qDesc')
    corrans = request.args.get('corrans')
    weightage = request.args.get('weightage')
    print('Weightage:'+str(weightage))
    print('Correct option:'+str(str(corrans)))
    preview = request.args.get('preview')
    options = request.args.get('options')
    op1 = request.args.get('op1')
    op2 = request.args.get('op2')
    op3 = request.args.get('op3')
    op4 = request.args.get('op4')
    print(op1)
    print(op2)
    print(op3)
    print(op4)
    form = QuestionBuilderQueryForm()
    print("Updated class Value+:"+updatedCV)
    print(str(updatedCV)+" "+str(topicId)+" "+str(subId)+" "+str(qType)+" "+str(qDesc)+" "+str(preview)+" "+str(corrans)+" "+str(weightage))
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).order_by(ClassSection.class_val).all()]
    form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.topics.choices=[(str(i['topic_id']), str(i['topic_name'])) for i in topics(1,54)]
    flag = False
    # updateQuery = "update question_details t1 set topic_id='" + str(topicId) + "' where question_id='" + question_id + "'"
    updateQuery = "update question_details set class_val='" + str(updatedCV) +  "',topic_id='"+ str(topicId) + "',subject_id='"+ str(subId) + "',question_type='" + str(qType) + "',question_description='"+ str(qDesc) + "',reference_link='"+ str(preview) +"' where question_id='" + str(question_id) + "'"

    queryOneExe = db.session.execute(text(updateQuery))
    updateWeightage = "update question_details set suggested_weightage='" + str(weightage) + "' where question_id='" + str(question_id) + "'" 
    querytwoExe = db.session.execute(text(updateWeightage))
    

    option_id_list = QuestionOptions.query.filter_by(question_id=question_id).order_by(QuestionOptions.option_id).all()
    if corrans:
        print(option_id_list)
        i=0
        opId1=''
        opId2=''
        opId3=''
        opId4=''
        for opt in option_id_list:
            if i==0:
                opId1 = opt.option_id
            elif i==1:
                opId2 = opt.option_id
            elif i==2:
                opId3 = opt.option_id
            else:
                opId4 = opt.option_id
            i=i+1
        print("Options order of id:"+str(opId1)+' '+str(opId2)+' '+str(opId3)+' '+str(opId4))
        # print(option_id) 
        # option = "select option_id from question_options where question_id='"+ str(question_id) + "'"
        # opt = db.session.execute(text(option))
        # print("Updated options "+str(opt))
        if opId1 and opId2 and opId3 and opId4:
            updateOption1 = "update question_options set option_desc='"+str(op1)+"' where option_id='"+ str(opId1) + "'"
            print(updateOption1)
            updateOpt1Exe = db.session.execute(text(updateOption1))
            updateOption2 = "update question_options set option_desc='"+str(op2)+"' where option_id='"+ str(opId2) + "'"
            print(updateOption2)
            updateOpt2Exe = db.session.execute(text(updateOption2))
            updateOption3 = "update question_options set option_desc='"+str(op3)+"' where option_id='"+ str(opId3) + "'"
            print(updateOption3)
            updateOpt3Exe = db.session.execute(text(updateOption3))
            updateOption4 = "update question_options set option_desc='"+str(op4)+"' where option_id='"+ str(opId4) + "'"
            print(updateOption4)
            updateOpt4Exe = db.session.execute(text(updateOption4))
            if str(corrans)!='':
                updatequery1 = "update question_options set is_correct='N' where is_correct='Y' and question_id='" +str(question_id)+"'"
                print(updatequery1)
                update1 = db.session.execute(text(updatequery1))
                updateCorrectOption = "update question_options set is_correct='Y' where option_desc='"+str(corrans)+"' and question_id='"+str(question_id)+"'"
                print(updateCorrectOption)
                updateOp = db.session.execute(text(updateCorrectOption))
        else:
            optionlist = []
            optionlist.append(op1)
            optionlist.append(op2)
            optionlist.append(op3)
            optionlist.append(op4)
            corrAns = 'Y'
            for optionDesc in optionlist:
                if optionDesc==corrans:
                    query = "insert into question_options(option_desc,question_id,weightage,is_correct,option) values('"+optionDesc+"','"+question_id+"','"+weightage+"','Y','A')"
                else:
                    query = "insert into question_options(option_desc,question_id,weightage,option) values('"+optionDesc+"','"+question_id+"','"+weightage+"','A')"
                    db.session.execute(query)

    print('Inside Update Questions')
    db.session.commit()
    print(updateQuery)
    # updateSecondQuery = "update question_options set weightage='" + str(weightage) +"' where question_id='" + str(question_id) + "'"
    # querySecondExe = db.session.execute(text(updateSecondQuery)) 
    # db.session.commit()
    print("Question Id in update Question:"+question_id)
    # print(updatedData)
    return render_template('questionUpload.html', form=form, flag=flag)


@app.route('/questionOptions')
def questionOptions():
    question_id_arg=request.args.get('question_id')
    questionOptionResults = QuestionOptions.query.filter_by(question_id=question_id_arg).all()
    questionOptionsList=[]
    for value in questionOptionResults:
        print("This is the value: "+str(value))        
        questionOptionsList.append(value.option+". "+value.option_desc)

    print(questionOptionsList)

    return jsonify([questionOptionsList])


@app.route('/deleteQuestion')
def deleteQuestion():
    question_id = request.args.get('question_id')
    print('Delete Question Id:'+question_id)
    print("Question Id:-"+question_id)

    updateQuery = "update question_details set archive_status='Y' where question_id='"+question_id+"'"
    print(updateQuery)
    db.session.execute(updateQuery)
    db.session.commit()
    return "text" 




@app.route('/questionDetails')
def questionDetails():
    flag = True
    question_id = request.args.get('question_id')
    print("Question Id-:"+question_id)
    form = QuestionBuilderQueryForm()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).order_by(ClassSection.class_val).all()]
    form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.topics.choices=[(str(i['topic_id']), str(i['topic_name'])) for i in topics(1,54)]

    questionDetailsQuery = "select t2.class_val, t1.question_id, t2.subject_id, t1.reference_link, t1.suggested_weightage, t2.topic_name, t2.topic_id, t1.question_type, t1.question_description, t4.description from question_details t1 "
    questionDetailsQuery = questionDetailsQuery + "inner join topic_detail t2 on t1.topic_id=t2.topic_id "
    questionDetailsQuery = questionDetailsQuery + "inner join message_detail t4 on t1.subject_id = t4.msg_id"
    questionDetailsQuery = questionDetailsQuery + " where t1.question_id ='" + question_id + "' order by t1.question_id"

    questionUpdateUploadSubjective = db.session.execute(text(questionDetailsQuery)).first()   
    question_desc = questionUpdateUploadSubjective.question_description.replace('\n', ' ').replace('\r', '')
    print(questionUpdateUploadSubjective)
    questionUpdateUpload=questionUpdateUploadSubjective
    if questionUpdateUpload.question_type=='MCQ1':
       
        query = "select option_desc from question_options where question_id='" + question_id + "' order by option_id"
        #print(query)
        avail_options = db.session.execute(text(query)).fetchall()
        queryCorrectoption = "select option_desc from question_options where is_correct='Y' and question_id='" + question_id + "'"  
        #print(queryCorrectoption)
        correctoption = db.session.execute(text(queryCorrectoption)).fetchall()
        print(correctoption)
        correctOption = ''
        for c in correctoption:
            print(c.option_desc)
            correctOption = c.option_desc
        print('Correct Option:'+correctOption)
        for q in questionUpdateUploadSubjective:
            print('this is check for MCQ ' + str(q))
        for a in avail_options:
            print(a)
        print('Correct Option Again:'+correctOption)
        return render_template('questionUpload.html', question_id=question_id, questionUpdateUpload=questionUpdateUpload, form=form, flag=flag, avail_options=avail_options, correctOption=correctOption,question_desc=question_desc)
        # return render_template('questionUpload.html',question_id=question_id, questionUpdateUploadSubjective=questionUpdateUploadSubjective,form=form,flag=flag,avail_options=avail_options,correctOption=correctOption)

    for q in questionUpdateUpload:
        print('this is check for Subjective ' + str(q))
    
    return render_template('questionUpload.html', question_id=question_id, questionUpdateUpload=questionUpdateUpload, form=form, flag=flag,question_desc=question_desc)


@app.route('/updateStudentProfile')
def updateStudentProfile():
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    gender = request.args.get('gender')
    birthdate = request.args.get('birthdate')
    phone = request.args.get('phone')
    address2 = request.args.get('address2')
    address1 = request.args.get('address1')
    locality = request.args.get('locality')
    city = request.args.get('city')
    state = request.args.get('state')
    country = request.args.get('country')
    pincode = request.args.get('pincode')
    class_val = request.args.get('class_val')
    section = request.args.get('section')
    school_admn_no = request.args.get('school_admn_no')
    roll_number = request.args.get('roll_number')
    preview = request.args.get('preview')
    student_id = request.args.get('student_id')
    url = request.args.get('preview')

    # query = "update student_profile set g"
    print('StudentId:'+str(student_id)+"fName:"+str(first_name)+"lName:"+str(last_name)+"gender:"+str(gender)+"bdate:"+str(birthdate)+"phone:"+str(phone)+"add1:"+str(address1)+"add2:"+str(address2)+"loc:"+str(locality)+"city:"+str(city)+"state:"+str(state)+"country:"+str(country)+"pincode:"+str(pincode)+"class:"+str(class_val)+"sect:"+str(section)+"Sch_num:"+str(school_admn_no)+"roll:"+str(roll_number)+"url:"+str(url))
    form=SingleStudentRegistration()
    return render_template('studentRegistration.html',form=form)
# @app.route('/topperListAll')
# def topperListAll():
#     user = User.query.filter_by(username=current_user.username).first_or_404()
#     teacher= TeacherProfile.query.filter_by(user_id=user.id).first() 
#     query = "select  * from fn_performance_leaderboard_detail('"+ str(teacher.school_id)+"') order by marks desc, student_name "
#     #print('Query:'+query)
#     leaderBoardData = db.session.execute(text(query)).fetchall()
#     return render_template('_leaderBoardTable.html',leaderBoardData=leaderBoardData)
def rename(dataframe):
    subject = MessageDetails.query.with_entities(MessageDetails.msg_id,MessageDetails.description).distinct().filter_by(category='Subject').all()
    # df = df.drop(['studentid'],axis=1)
    df = dataframe.columns.values.tolist()
    i=0
    for col in df:
        if i!=0:
            
            c = col.split('_')
            for sub in subject:
                if c[0]==str(sub.msg_id) and c[1]=='x':
                    dataframe.rename(columns = {col:sub.description}, inplace = True)
                elif c[1]=='y':
                    dataframe.rename(columns = {col:'Total Test'}, inplace = True)
                else:
                    print(col)
        i = i +1
    return dataframe
@app.route('/leaderBoard')
def leaderBoard():
    form = LeaderBoardQueryForm()
    qclass_val = request.args.get("class_val")
    #print('class:'+str(qclass_val))
    if current_user.is_authenticated:        
        user = User.query.filter_by(username=current_user.username).first_or_404()
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first() 
        distinctClasses = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacher_id.school_id)+" GROUP BY class_val order by s")).fetchall()    
        form.subject_name.choices = [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
        class_sec_id=ClassSection.query.filter_by(class_val='1',school_id=teacher_id.school_id).first()
        form.test_type.choices= [(i.description,i.description) for i in MessageDetails.query.filter_by(category='Test type').all()]

        form.testdate.choices = [(i.exam_date,i.exam_date) for i in ResultUpload.query.filter_by(class_sec_id=class_sec_id.class_sec_id).all()]
        available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher_id.school_id).all()  
        form.section.choices= [(i.section,i.section) for i in available_section]
        

        leaderBoardData = leaderboardContent(qclass_val)
        #print('Type')
        #print(type(leaderBoardData))
        column_names = ["a", "b", "c"]
        datafr = pd.DataFrame(columns = column_names)
        if type(leaderBoardData)!=type(datafr):
            classSecCheckVal=''
            colAll = ''
            columnNames = ''
            qclass_val = ''
            subj = ''
            subColumn = ''
            subHeader = ''
            data = ''
            classSecCheckVal = ''
            return render_template('leaderBoard.html',classSecCheckVal=classSecCheckVal,form=form,distinctClasses=distinctClasses,leaderBoardData=leaderBoardData,colAll=colAll,columnNames=columnNames, qclass_val=qclass_val,subject=subj,subColumn=subColumn,subHeader=subHeader,user_type_val=str(current_user.user_type))

        else:
            df1 = leaderBoardData[['studentid','profile_pic','student_name','class_val','section','total_marks%','total_tests']]
            df2 = leaderBoardData.drop(['profile_pic', 'student_name','class_val','section','total_marks%','total_tests'], axis=1)
            leaderBoard = pd.merge(df1,df2,on=('studentid'))
            
            d = leaderBoard[['studentid','profile_pic','student_name','class_val','section','total_marks%','total_tests']]
            df3 = leaderBoard.drop(['studentid'],axis=1)
            #print('DF3:')
            #print(df3)
            #print('print new dataframe')
            
            df1.rename(columns = {'profile_pic':'Profile Picture'}, inplace = True)
            df1.rename(columns = {'student_name':'Student'}, inplace = True)
            df1.rename(columns = {'class_val':'Class'}, inplace = True)
            df1.rename(columns = {'section':'Section'}, inplace = True)
            df1.rename(columns = {'total_marks%':'Total Marks'}, inplace = True)
            df1.rename(columns = {'total_tests':'Total Tests'}, inplace = True)
            #print(df1)
            #print('Excluding columns')
            #print(df2)
            ## rename(df2)
            #print('LeaderBoard Data:')
            #print(leaderBoardData)
            data = []
            

            header = [df1.columns.values.tolist()]
            headerAll = [df3.columns.values.tolist()]
            colAll = ''
            subjHeader = [df2.columns.values.tolist()]
            columnNames = ''
            col = ''
            subColumn = ''
            #print('Size of dataframe:'+str(len(subjHeader)))
            for subhead in subjHeader:
                subColumn = subhead
                #print('Header with Subject Name')
                #print(subhead)
            for h in header:
                columnNames = h
            for headAll in headerAll: 
                colAll = headAll
            #print(' all header Length:'+str(len(colAll))+'Static length:'+str(len(columnNames))+'sub header length:'+str(len(subColumn)))
            n= int(len(subColumn)/2)
            ndf = df2.drop(['studentid'],axis=1)
            newDF = ndf.iloc[:,0:n]
            new1DF = ndf.iloc[:,n:]
            
            df5 = pd.concat([newDF, new1DF], axis=1)
            DFW = df5[list(sum(zip(newDF.columns, new1DF.columns), ()))]
            #print('New DF')
            #print(DFW)
            dat = pd.concat([d,DFW], axis=1)
            #print(dat)
            subHeader = ''
            for row in dat.values.tolist():
                data.append(row)
            subH = [DFW.columns.values.tolist()]

            for s in subH:
                subHeader = s
            subHead = [dat.columns.values.tolist()]
            for column in subHead:
                col = column
            subject = MessageDetails.query.with_entities(MessageDetails.msg_id,MessageDetails.description).distinct().filter_by(category='Subject').order_by(MessageDetails.msg_id).all()
            #print(subject)
            subj = []

            #for d in data:
            #    print('In data Student id')
            #    print(data[0])
            
            for sub in subject:
                li = []
                i=0
                for col in subColumn:
                    if i!=len(subColumn)/2:
                        c = col.split('_')
                        #print(c[0])
                        #print(sub.msg_id)
                        if(c[0]==str(sub.msg_id)):
                            #print(c[0])
                            #print(sub.msg_id)                                                        
                            li.append(sub.msg_id)
                            li.append(sub.description)
                            subj.append(li)
                            break
                    i=i+1
                    
            #print('List with Subjects')
            #print(subj)
            #for s in subj:
            #    print(s[0])
            #    print(s[1])
            #print('Inside subjects')
            classSecCheckVal=classSecCheck()
            return render_template('leaderBoard.html',classSecCheckVal=classSecCheckVal,form=form,distinctClasses=distinctClasses,leaderBoardData=data,colAll=colAll,columnNames=columnNames, qclass_val=qclass_val,subject=subj,subColumn=subColumn,subHeader=subHeader,user_type_val=str(current_user.user_type))


    return render_template('leaderBoard.html',classSecCheckVal=classSecCheckVal,form=form,distinctClasses=distinctClasses,leaderBoardData=data,colAll=colAll,columnNames=columnNames, qclass_val=qclass_val,subject=subj,subColumn=subColumn,subHeader=subHeader,user_type_val=str(current_user.user_type))


@app.route('/classDelivery',methods=['GET','POST'])
@login_required
def classDelivery():
    form = ContentManager()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).order_by(ClassSection.class_val).all()]
    form.subject_name.choices = ''
    
    form.chapter_num.choices = ''
    
    form.topics.choices = ''
    
    form.content_type.choices = ''
    #if current_user.is_authenticated:        
    user = User.query.filter_by(username=current_user.username).first_or_404()        
    teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
    qtopic_id=request.args.get('topic_id')
    qsubject_id=request.args.get('subject_id')
    qclass_sec_id = request.args.get('class_sec_id')
    retake = request.args.get('retake')
  
    contentData = ContentDetail.query.filter_by(topic_id=int(qtopic_id),archive_status='N').all()
    subject_name = MessageDetails.query.filter_by(msg_id=qsubject_id).all()
    subName = ''
    for sub in subject_name:
        subName = sub.description
        break
    q=0
    for content in contentData:            
        q=q+1
    classSections=ClassSection.query.filter_by(school_id=teacher.school_id).order_by(ClassSection.class_val).all()
    
    currClassSecDet = ClassSection.query.filter_by(class_sec_id=qclass_sec_id).first()
    distinctClasses = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacher_id.school_id)+" GROUP BY class_val order by s")).fetchall()        
        # end of sidebar        
    #for curr in currClass:        
    #topicTrack = TopicTracker.query.filter_by(class_sec_id=currClass.class_sec_id, subject_id=qsubject_id).first()
    #print ("this is topic Track: " + topicTrack)
    topicDet = Topic.query.filter_by(topic_id=qtopic_id).order_by(Topic.chapter_num).first()
    bookDet= BookDetails.query.filter_by(book_id = topicDet.book_id).first()
    #if retake is true then set is_covered to No
    if retake == 'Y':
        topicFromTracker = TopicTracker.query.filter_by(school_id = teacher.school_id, topic_id=qtopic_id).first()
        topicFromTracker.is_covered='N'
        topicFromTracker.reteach_count=int(topicFromTracker.reteach_count)+1
        db.session.commit()
    
    topicTrackerQuery = "select t1.topic_id, t1.topic_name, t1.chapter_name, t1.chapter_num, " 
    topicTrackerQuery = topicTrackerQuery + " t1.unit_num, t1.book_id, t2.is_covered, t1.subject_id, t2.class_sec_id "
    topicTrackerQuery = topicTrackerQuery + " from "
    topicTrackerQuery = topicTrackerQuery + " topic_detail t1, "
    topicTrackerQuery = topicTrackerQuery + " topic_tracker t2"
    topicTrackerQuery = topicTrackerQuery + " where"
    topicTrackerQuery = topicTrackerQuery + " t1.topic_id=t2.topic_id"
    topicTrackerQuery = topicTrackerQuery + " and t2.class_sec_id = '" + str(qclass_sec_id) + "'"
    topicTrackerQuery = topicTrackerQuery + " and t1.subject_id= '" + str(qsubject_id ) + "' order by chapter_num"
    topicTrackerDetails= db.session.execute(text(topicTrackerQuery)).fetchall()
    # new changes for live classes
    if request.method=='POST':
        print('post method')
        # print(request.form('duration'))
        # print(request.form('conferenceLink'))
        qconf_link = request.args.get('conf_link')
        qduration = request.args.get('duration')
        print(qconf_link)
        print(qduration)
        if qduration!=None or qduration!='':
            print('if duration is not empty')
            print(int(qduration))
            end_time = datetime.now() + timedelta(hours=int(qduration))
            print(end_time)
        else:
            print('if duration is empty') 
            end_time = datetime.now() + timedelta(hours=1)
        print('Start time')
        
        format = "%Y-%m-%d %H:%M:%S"
    # Current time in UTC
        now_utc = datetime.now(timezone('UTC'))
        print(now_utc.strftime(format))
    # Convert to local time zone
        now_local = now_utc.astimezone(get_localzone())
        print(now_local.strftime(format))
        end_utc = end_time.now(timezone('UTC'))
        end_local = end_time.astimezone(get_localzone())
        print(end_local.strftime(format))
        print('end time')
        
        liveClassData=LiveClass(class_sec_id = qclass_sec_id,subject_id = qsubject_id, topic_id=qtopic_id, 
            start_time = now_local.strftime(format), end_time = end_local.strftime(format), status = "Active", teacher_id=teacher.teacher_id, 
            teacher_name = str(current_user.first_name)+' '+str(current_user.last_name), conf_link=str(qconf_link), school_id = teacher.school_id,
            is_archived = 'N',last_modified_date = now_local.strftime(format))        
        db.session.add(liveClassData)
        db.session.commit() 
        return render_template('classDelivery.html', classSecCheckVal=classSecCheck(),classsections=classSections, currClassSecDet= currClassSecDet, distinctClasses=distinctClasses,form=form ,topicDet=topicDet ,bookDet=bookDet,topicTrackerDetails=topicTrackerDetails,contentData=contentData,subName=subName,retake=retake,user_type_val=str(current_user.user_type))
    return render_template('classDelivery.html', classSecCheckVal=classSecCheck(),classsections=classSections, currClassSecDet= currClassSecDet, distinctClasses=distinctClasses,form=form ,topicDet=topicDet ,bookDet=bookDet,topicTrackerDetails=topicTrackerDetails,contentData=contentData,subName=subName,retake=retake,user_type_val=str(current_user.user_type))



@app.route('/contentManager',methods=['GET','POST'])
@login_required
def contentManager():
    topic_list=None
    user_type_val = current_user.user_type
    formContent = ContentManager()
    studentDetails = StudentProfile.query.filter_by(user_id=current_user.id).first()
    teacher_id = ''
    if user_type_val==134:
        teacher_id = StudentProfile.query.filter_by(user_id=current_user.id).first()
    else:
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    formContent.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).order_by(ClassSection.class_val).all()]
    formContent.subject_name.choices = ''
    formContent.chapter_num.choices = ''
    formContent.topics.choices = ''    
    formContent.content_type.choices = ''    
    form=QuestionBankQueryForm() # resusing form used in question bank 
    available_class = "select distinct class_val from class_section where school_id='"+str(teacher_id.school_id)+"'"
    available_class = db.session.execute(text(available_class)).fetchall()
 
    if request.method=='POST':
        topic_list=Topic.query.filter_by(class_val=str(form.class_val.data),subject_id=int(form.subject_name.data),chapter_num=int(form.chapter_num.data)).all()
        subject=MessageDetails.query.filter_by(msg_id=int(form.subject_name.data)).first()
        session['class_val']=form.class_val.data
        session['sub_name']=subject.description
        session['test_type_val']=form.test_type.data
        session['chapter_num']=form.chapter_num.data    
        form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(str(form.class_val.data))]
        form.chapter_num.choices= [(int(i['chapter_num']), str(i['chapter_num'])+' - '+str(i['chapter_name'])) for i in chapters(str(form.class_val.data),int(form.subject_name.data))]
        if user_type_val==134:
            return render_template('contentManager.html',form=form,formContent=formContent,topics=topic_list,disconn=1,user_type_val=str(current_user.user_type),studentDetails=studentDetails)
        else:
            return render_template('contentManager.html',form=form,formContent=formContent,topics=topic_list,user_type_val=str(current_user.user_type),studentDetails=studentDetails)
    if user_type_val==134:
        return render_template('contentManager.html',classSecCheckVal=classSecCheck(),form=form,formContent=formContent,disconn=1,user_type_val=str(current_user.user_type),studentDetails=studentDetails)
    else:
        return render_template('contentManager.html',classSecCheckVal=classSecCheck(),form=form,formContent=formContent,user_type_val=str(current_user.user_type),studentDetails=studentDetails,available_class=available_class)


@app.route('/loadContent',methods=['GET','POST'])
def loadContent():
    class_val = request.args.get('selected_class_value')
    selected_subject = request.args.get('selected_subject_value')
    selected_chapter = request.args.get('selected_chapter_value')
    selected_topic = request.args.get('selected_topic_value')
    contentName = request.args.get('contentName')
    contentTypeId = request.args.get('contentTypeId')
    contentUrl = request.args.get('contentUrl')
    reference = request.args.get('reference')
    public = request.args.get('public')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    today = date.today()
    d4 = today.strftime("%b-%d-%Y")
    print(d4)
    print('public check value')
    print(public)
    if public=='true':
        if reference!='':
            contentData = ContentDetail(content_name=str(contentName),class_val=int(class_val),subject_id=int(selected_subject),
            topic_id=int(selected_topic),is_private='N',content_type=contentTypeId,school_id=teacher_id.school_id,reference_link=reference,archive_status='N',last_modified_date=d4,uploaded_by=teacher_id.teacher_id)
            db.session.add(contentData)
        else:
            contentData = ContentDetail(content_name=str(contentName),class_val=int(class_val),subject_id=int(selected_subject),
            topic_id=int(selected_topic),is_private='N',school_id=teacher_id.school_id,content_type=contentTypeId,reference_link=contentUrl,archive_status='N',last_modified_date=d4,uploaded_by=teacher_id.teacher_id)
            db.session.add(contentData)
    else:
        if reference!='':
            contentData = ContentDetail(content_name=str(contentName),class_val=int(class_val),subject_id=int(selected_subject),
            topic_id=int(selected_topic),is_private='Y',school_id=teacher_id.school_id,content_type=contentTypeId,reference_link=reference,archive_status='N',last_modified_date=d4,uploaded_by=teacher_id.teacher_id)
            db.session.add(contentData)
        else:
            contentData = ContentDetail(content_name=str(contentName),class_val=int(class_val),subject_id=int(selected_subject),
            topic_id=int(selected_topic),is_private='Y',school_id=teacher_id.school_id,content_type=contentTypeId,reference_link=contentUrl,archive_status='N',last_modified_date=d4,uploaded_by=teacher_id.teacher_id)
            db.session.add(contentData)
    db.session.commit()
    return "Upload"

@app.route('/contentDetails',methods=['GET','POST'])
def contentDetails():
    teacher= TeacherProfile.query.filter_by(user_id=current_user.id).first()
    content = "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
    content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
    content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
    content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='N' "
    content = content + "union "
    content = content + "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
    content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
    content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
    content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='Y' and cd.school_id='"+str(teacher.school_id)+"' and content_id not in (select content_id from content_detail cd where is_private = 'N' and archive_status = 'N') order by content_id desc limit 5"
    print('query:'+str(content))
    contentDetail = db.session.execute(text(content)).fetchall()
    
    if len(contentDetail)==0:
        print("No data present in the content manager details")
        return jsonify(["NA"])
    else:
        print(len(contentDetail))
        for c in contentDetail:
            print("Content List"+str(c.content_name))    
        
        return render_template('_contentDetails.html',contents=contentDetail)

@app.route('/filterContentfromTopic',methods=['GET','POST'])
def filterContentfromTopic():
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_value = request.args.get('class_val')
    subject_id = request.args.get('subject_id')
    print(class_value)
    print(subject_id)
    topic_list = request.get_json()
    for topic in topic_list:
        print(topic)
        if topic:
            print('topic exist')
        else:
            print('topic not exist')
    # contentList = "select *from content_detail cd where is_private = 'N' "
    # contentList = contentList + " and archive_status = 'N' "
    content = ''
    contents = []
    l=1
    for topic in topic_list:
        if class_value != None:
            if subject_id!=None:
                content = "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
                content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
                content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
                content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='N' and cd.class_val='"+str(class_value)+"' and cd.subject_id='"+str(subject_id)+"' and cd.topic_id='"+str(topic)+"' "
                content = content + "union "
                content = content + "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
                content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
                content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
                content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='Y' and cd.school_id='"+str(teacher.school_id)+"' and cd.class_val='"+str(class_value)+"' and cd.subject_id='"+str(subject_id)+"' and cd.topic_id='"+str(topic)+"' and content_id not in (select content_id from content_detail cd where is_private = 'N' and archive_status = 'N' and cd.class_val='"+str(class_value)+"' and cd.subject_id='"+str(subject_id)+"' and cd.topic_id='"+str(topic)+"' ) order by content_id desc"
            else:
                content = "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
                content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
                content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
                content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='N' and cd.class_val='"+str(class_value)+"' and cd.topic_id='"+str(topic)+"' "
                content = content + "union "
                content = content + "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
                content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
                content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
                content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='Y' and cd.school_id='"+str(teacher.school_id)+"' and cd.class_val='"+str(class_value)+"' and cd.topic_id='"+str(topic)+"' and content_id not in (select content_id from content_detail cd where is_private = 'N' and archive_status = 'N' and cd.class_val='"+str(class_value)+"' and cd.topic_id='"+str(topic)+"' ) order by content_id desc"
        else:
            if subject_id!=None:
                content = "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
                content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
                content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
                content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='N' and cd.subject_id= '"+str(subject_id)+"' and cd.topic_id='"+str(topic)+"' "
                content = content + "union "
                content = content + "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
                content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
                content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
                content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='Y' and cd.school_id='"+str(teacher.school_id)+"' and cd.subject_id= '"+str(subject_id)+"' and cd.topic_id='"+str(topic)+"' and content_id not in (select content_id from content_detail cd where is_private = 'N' and archive_status = 'N' and cd.subject_id= '"+str(subject_id)+"' and cd.topic_id='"+str(topic)+"' ) order by content_id desc"
            else:
                content = "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
                content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
                content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
                content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='N' and cd.topic_id='"+str(topic)+"' "
                content = content + "union "
                content = content + "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
                content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
                content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
                content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='Y' and cd.school_id='"+str(teacher.school_id)+"' and cd.topic_id='"+str(topic)+"' and content_id not in (select content_id from content_detail cd where is_private = 'N' and archive_status = 'N' and cd.topic_id='"+str(topic)+"') order by content_id desc limit 10"
        contentDetail = db.session.execute(text(content)).fetchall()
        if contentDetail:
            contents.append(contentDetail)

    # if contents:
    #     contentDetail = db.session.execute(text(content)).fetchall()
    # else:
    #     return jsonify(["NS"])
    print('length of list:'+str(len(contentDetail)))
    if len(contents)==0:
        print("No data present in the content manager details")
        return jsonify(["NA"])
    else:
        print(len(contents))
        # for c in contentDetail:
        #     print("Content List"+str(c.content_name)) 
        flag = 'true'
        flagTopic = 'true'
        return render_template('_contentDetails.html',contents=contents,flag=flag,flagTopic=flagTopic)

@app.route('/recentContentDetails',methods=['GET','POST'])
def recentContentDetails():
    teacher = ''
    if current_user.user_type==71 or current_user.user_type==135 :
        teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    elif current_user.user_type==134:
        teacher = StudentProfile.query.filter_by(user_id=current_user.id).first()
    class_value = request.args.get('class_val')
    subject_id = request.args.get('subject_id')
    print(class_value)
    print(subject_id)
    # contentList = "select *from content_detail cd where is_private = 'N' "
    # contentList = contentList + " and archive_status = 'N' "

    if class_value != None:
        if subject_id!=None:
            content = "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
            content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
            content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
            content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='N' and cd.class_val='"+str(class_value)+"' and cd.subject_id='"+str(subject_id)+"' "
            content = content + "union "
            content = content + "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
            content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
            content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
            content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='Y' and cd.school_id='"+str(teacher.school_id)+"' and cd.class_val='"+str(class_value)+"' and cd.subject_id='"+str(subject_id)+"' and content_id not in (select content_id from content_detail cd where is_private = 'N' and archive_status = 'N' and cd.class_val='"+str(class_value)+"' and cd.subject_id='"+str(subject_id)+"' ) order by content_id desc"
        else:
            content = "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
            content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
            content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
            content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='N' and cd.class_val='"+str(class_value)+"' "
            content = content + "union "
            content = content + "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
            content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
            content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
            content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='Y' and cd.school_id='"+str(teacher.school_id)+"' and cd.class_val='"+str(class_value)+"' and content_id not in (select content_id from content_detail cd where is_private = 'N' and archive_status = 'N' and cd.class_val='"+str(class_value)+"' ) order by content_id desc"
    else:
        if subject_id!=None:
            content = "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
            content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
            content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
            content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='N' and cd.subject_id= '"+str(subject_id)+"' "
            content = content + "union "
            content = content + "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
            content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
            content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
            content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='Y' and cd.school_id='"+str(teacher.school_id)+"' and cd.subject_id= '"+str(subject_id)+"' and content_id not in (select content_id from content_detail cd where is_private = 'N' and archive_status = 'N' and cd.subject_id= '"+str(subject_id)+"' ) order by content_id desc"
        else:
            content = "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
            content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
            content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
            content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='N' "
            content = content + "union "
            content = content + "select cd.last_modified_date,cd.content_id, cd.content_type,cd.reference_link, cd.content_name,td.topic_name,md.description subject_name, cd.class_val,tp.teacher_name uploaded_by from content_detail cd "
            content = content + "inner join topic_detail td on cd.topic_id = td.topic_id "
            content = content + "inner join message_detail md on md.msg_id = cd.subject_id "
            content = content + "inner join teacher_profile tp on tp.teacher_id = cd.uploaded_by where cd.archive_status = 'N' and is_private='Y' and cd.school_id='"+str(teacher.school_id)+"' and content_id not in (select content_id from content_detail cd where is_private = 'N' and archive_status = 'N') order by content_id desc limit 10"

    contentDetail = db.session.execute(text(content)).fetchall()
    
    if len(contentDetail)==0:
        print("No data present in the content manager details")
        return jsonify(["NA"])
    else:
        print(len(contentDetail))
        for c in contentDetail:
            print("Content List"+str(c.content_name)) 
        flag = 'true'
        return render_template('_contentDetails.html',contents=contentDetail,flag=flag)
    # if contentList:
    #     return render_template('_contentManagerDetails.html',contents=contentList)
    # else:
    #     return jsonify(["NA"])
 
@app.route('/contentManagerDetails',methods=['GET','POST'])
def contentManagerDetails():
    contents=[]
    topicList=request.get_json()
    user_type_val = current_user.user_type
    teacher_id = ''
    if user_type_val == 134:
        teacher_id = StudentProfile.query.filter_by(user_id=current_user.id).first()
    else:
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    for topic in topicList:

        contentList = "select *from content_detail cd where is_private = 'N' and archive_status = 'N' and topic_id='"+str(topic)+"' union select *from content_detail cd2 where is_private = 'Y' and archive_status = 'N' and topic_id='"+str(topic)+"' and school_id = '"+str(teacher_id.school_id)+"' and content_id not in (select content_id from content_detail cd where is_private = 'N' and archive_status = 'N' and topic_id='"+str(topic)+"')"
        print(contentList)
        contentList = db.session.execute(text(contentList)).fetchall()
        
        if len(contentList)!=0:
            contents.append(contentList)
    if len(contents)==0:
        print("No data present in the content manager details")
        return jsonify(["NA"])
    else:
        print(len(contents))
        for c in contents:
            print("Content List"+str(c))    
        return render_template('_contentManagerDetails.html',contents=contents)

@app.route('/feedbackCollection', methods=['GET', 'POST'])
@login_required
def feedbackCollection():    
    if request.method=='GET':
        teacher= TeacherProfile.query.filter_by(user_id=current_user.id).first()  
        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).order_by(ClassSection.class_val).all()  
        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val order by class_val")).fetchall()
        teacherProfile = teacher
        #using today's date to build response session id
        dateVal= datetime.today().strftime("%d%m%Y%H%M%S")
        qtest_id = request.args.get('test_id')
        weightage = request.args.get('weightage')
        NegMarking = request.args.get('negativeMarking')
        duration = request.args.get('duration')
        print('Test Id:'+str(qtest_id))
        qclass_val = request.args.get('class_val')
        qsection = request.args.get('section')
        qsubject_id = request.args.get('subject_id')
        print("this is the section, class_val and teacher: "+ str(qsection).upper() + ' ' + str(qclass_val).strip() + ' '+ str(teacher.school_id))
        if all(v is not None for v in [qtest_id, qclass_val, qsection, qsubject_id]):
            qsection = str(qsection).upper()
            currClassSecRow=ClassSection.query.filter_by(school_id=str(teacher.school_id),class_val=str(qclass_val).strip(),section=str(qsection).strip()).first()
            #queryCurrClassSecRow=ClassSection.query.filter_by(school_id=teacher.school_id,class_val=str(qclass_val).strip(),section=qsection)
            #print("Here's the query: "+str(queryCurrClassSecRow))
            if currClassSecRow is None:
                flash('Class and section value not valid')
                return redirect(url_for('testPapers'))
            #building response session ID
            print('This is the class section id found in DB:'+ str(currClassSecRow.class_sec_id))
            responseSessionID = str(qsubject_id).strip()+ str(dateVal).strip() + str(currClassSecRow.class_sec_id).strip()
            responseSessionIDQRCode = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="+responseSessionID

            subjectQueryRow = MessageDetails.query.filter_by(msg_id=qsubject_id).first()

            questionIDList = TestQuestions.query.filter_by(test_id=qtest_id).all()  
            qId = TestQuestions.query.filter_by(test_id=qtest_id).first()
            qWeightage = QuestionDetails.query.filter_by(question_id=qId.question_id).first()
            print('Inside question id list')
            print(questionIDList)          
            questionListSize = len(questionIDList)

            print('Question list size:'+str(questionListSize))
            total_marks = int(weightage)*questionListSize
            #creating a record in the session detail table  
            if questionListSize !=0:
                sessionDetailRowCheck = SessionDetail.query.filter_by(resp_session_id=responseSessionID).first()
                print('Date:'+str(dateVal))
                print('Response Session ID:'+str(responseSessionID))
                print('If Question list size is not zero')
                #print(sessionDetailRowCheck)
                if sessionDetailRowCheck==None:
                    print('if sessionDetailRowCheck is none')
                    #print(sessionDetailRowCheck)
                    if weightage:
                        sessionDetailRowInsert=SessionDetail(resp_session_id=responseSessionID,session_status='80',teacher_id= teacherProfile.teacher_id,
                        class_sec_id=currClassSecRow.class_sec_id, test_id=str(qtest_id).strip(),correct_marks=weightage,incorrect_marks=NegMarking, test_time=duration,total_marks=total_marks, last_modified_date = date.today())
                        db.session.add(sessionDetailRowInsert)
                    else:
                        sessionDetailRowInsert=SessionDetail(resp_session_id=responseSessionID,session_status='80',teacher_id= teacherProfile.teacher_id,
                        class_sec_id=currClassSecRow.class_sec_id, test_id=str(qtest_id).strip(),correct_marks=qWeightage.suggested_weightage,incorrect_marks=NegMarking, test_time=duration,total_marks=total_marks, last_modified_date = date.today())
                        db.session.add(sessionDetailRowInsert)
                    print('Adding to the db')
                    db.session.commit()

            questionList = []
            for questValue in questionIDList:
                print('Question ID:'+str(questValue.question_id))
                questionList.append(questValue.question_id)
            

            testDetailRow = TestDetails.query.filter_by(test_id=qtest_id).first()
            testType = testDetailRow.test_type
            #testTypeNameRow = MessageDetails.query.filter_by(msg_id=testTypeID).first()


            questions = QuestionDetails.query.filter(QuestionDetails.question_id.in_(questionList)).all()  
            for  question in questions:
                print('Question:'+str(question.question_description))         
            totalMarks = 0
            for eachQuest in questions:
                totalMarks = totalMarks + int(eachQuest.suggested_weightage)
            responseSessionIDQRCode = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="+responseSessionID
            if teacherProfile.device_preference==195:
                print('the device preference is as expected:' + str(teacherProfile.device_preference))
                return render_template('feedbackCollectionTeachDev.html',classSecCheckVal=classSecCheck(), subject_id=qsubject_id, class_val = qclass_val, section = qsection,questions=questions, questionListSize = questionListSize, resp_session_id = responseSessionID,responseSessionIDQRCode=responseSessionIDQRCode,subjectName = subjectQueryRow.description, totalMarks=total_marks,weightage=weightage, testType=testType)
            elif teacherProfile.device_preference==78:
                print('the device preference is not as expected' + str(teacherProfile.device_preference))
                return render_template('feedbackCollection.html',classSecCheckVal=classSecCheck(), subject_id=qsubject_id,classSections = classSections, distinctClasses = distinctClasses, class_val = qclass_val, section = qsection, questionList = questionIDList, questionListSize = questionListSize, resp_session_id = responseSessionID)
            else:
                print('the device preference is external webcame' + str(teacherProfile.device_preference))
                return render_template('feedbackCollectionExternalCam.html',classSecCheckVal=classSecCheck(), responseSessionIDQRCode = responseSessionIDQRCode, resp_session_id = responseSessionID,  subject_id=qsubject_id,classSections = classSections, distinctClasses = distinctClasses,questions=questions , class_val = qclass_val, section = qsection, questionList = questionIDList, questionListSize = questionListSize,qtest_id=qtest_id)

    elif request.method == 'POST':
        allCoveredTopics = request.form.getlist('topicCheck')
        class_val = request.form['class_val']
        section = request.form['section']
        subject_id = request.form['subject_id']
        teacher= TeacherProfile.query.filter_by(user_id=current_user.id).first()  
        #sidebar queries
        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).all()
        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val order by class_val")).fetchall()
        # end of sidebarm

        curr_class_sec_id=""

        for eachRow in classSections:
            if str(eachRow.section).strip()==str(section).strip():
                if str(eachRow.class_val).strip()==str(class_val).strip():                    
                    curr_class_sec_id=eachRow.class_sec_id

        #start of - db update to ark the checked topics as completed        
        #topicTrackerDetails = TopicTracker.query.filter_by(school_id = teacherProfile.school_id).all()
        currCoveredTopics=[]

        for val in allCoveredTopics:
            topicFromTracker = TopicTracker.query.filter_by(school_id = teacherProfile.school_id, topic_id=val).first()
            if topicFromTracker != None:
                if topicFromTracker.is_covered!='Y':
                    topicFromTracker.is_covered='Y'
                    currCoveredTopics.append(val)
                    db.session.commit()
        # end of  - update to mark the checked topics as completed

        questionList = QuestionDetails.query.filter(QuestionDetails.topic_id.in_(currCoveredTopics),QuestionDetails.question_type.like('%MCQ%')).filter_by(archive_status='N').all()
        questionListSize = len(questionList)
        
        responseSessionID = str(dateVal).strip() + str(subject_id).strip() + str(curr_class_sec_id).strip()
        responseSessionIDQRCode = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="+responseSessionID
        #changes for use with PC+ mobile cam combination
        print('Question list size:'+str(questionListSize))
        if questionListSize >0:
            sessionDetailRowInsert=SessionDetail(resp_session_id=responseSessionID,session_status='80',teacher_id= teacherProfile.teacher_id,
                        class_sec_id=curr_class_sec_id)
            db.session.add(sessionDetailRowInsert)
            db.session.commit()
            
            for eachQuestion in questionList:
                respSessionQuestionRowInsert = RespSessionQuestion(question_id = eachQuestion.question_id, question_status='86', resp_session_id=responseSessionID)
                db.session.add(respSessionQuestionRowInsert)
                db.session.commit()
            # topic_id, question_id, question_status, resp_session_id

        if teacherProfile.device_preference==78:        
            return render_template('feedbackCollection.html',classSecCheckVal=classSecCheck(), subject_id=subject_id,classSections = classSections, distinctClasses = distinctClasses, class_val = class_val, section = section, questionList = questionList, questionListSize = questionListSize, resp_session_id = responseSessionID)
        else:
            return render_template('feedbackCollectionExternalCam.html',classSecCheckVal=classSecCheck(), responseSessionIDQRCode = responseSessionIDQRCode, resp_session_id = responseSessionID,  subject_id=subject_id,classSections = classSections, distinctClasses = distinctClasses, class_val = class_val, section = section, questionList = questionList, questionListSize = questionListSize)
    else:
        return redirect(url_for('classCon'))

@app.route('/markSessionComplete')
@login_required
def markSessionComplete():
    resp_session_id = request.args.get('resp_session_id')
    sessionDetailRow = SessionDetail.query.filter_by(resp_session_id=resp_session_id).first()
    if sessionDetailRow!=None:
        sessionDetailRow.session_status='82'
        db.session.commit()
        return jsonify(["0"])
    else:
        return jsonify(["1"])


@app.route('/checkQuestionChange')
@login_required
def checkQuestionChange():
    resp_session_id = request.args.get('resp_session_id')
    sessionDetailRow = SessionDetail.query.filter_by(resp_session_id=resp_session_id).first()
    if str(sessionDetailRow.session_status).strip()=='80':
        if sessionDetailRow.load_new_question=='Y':
            return jsonify(["Y"])
        else:
            return jsonify(["N"])
    elif str(sessionDetailRow.session_status).strip()=='82':
        print ("returning FR")
        return jsonify(["FR"])
    else:
        print("We're in returning sessionDetail row's sessionstatus NA")
        return jsonify([str(sessionDetailRow.session_status)+'NA'])
            

@app.route('/loadQuestionExtCam')
@login_required
def loadQuestionExtCam():
    resp_session_id=request.args.get('resp_session_id')
    totalQCount = request.args.get('total')
    qnum= request.args.get('qnum')
    print("This is the complete response session ID received in load quest ext cam"+resp_session_id)
    sessionDetailRow=SessionDetail.query.filter_by(resp_session_id=resp_session_id).first()
    if sessionDetailRow!=None:
        sessionDetailRow.load_new_question='N'
        db.session.commit()
    current_question_id=sessionDetailRow.current_question
    question = QuestionDetails.query.filter_by(question_id=current_question_id, archive_status='N').first()
    questionOp = QuestionOptions.query.filter_by(question_id=current_question_id).all()
    return render_template('_loadQuestionExtCam.html',question=question, questionOp=questionOp,qnum = qnum,totalQCount = totalQCount)

@app.route('/loadQuestion')
@login_required
def loadQuestion():
    question_id = request.args.get('question_id')
    totalQCount = request.args.get('total')
    qnum= request.args.get('qnum')
    resp_session_id=request.args.get('resp_session_id')
    print('Question Id:'+str(question_id))
    print(resp_session_id)
    question = QuestionDetails.query.filter_by(question_id=question_id, archive_status='N').first()
    questionOp = QuestionOptions.query.filter_by(question_id=question_id).all()
    if resp_session_id!=None:
        respSessionQuestionRow=RespSessionQuestion.query.filter_by(resp_session_id=resp_session_id,question_status='86').first()
        if respSessionQuestionRow!=None:
            respSessionQuestionRow.question_status='87'
            db.session.commit()
        sessionDetRow=SessionDetail.query.filter_by(resp_session_id=str(resp_session_id).strip()).first()        
        sessionDetRow.current_question=question_id
        sessionDetRow.load_new_question='Y'
        db.session.commit()
    #for option in questionOp:
    #    print(option.option_desc)
    return render_template('_question.html',question=question, questionOp=questionOp,qnum = qnum,totalQCount = totalQCount,  )    


# route for fetching next question and updating db for each response from student - tablet assessment process

@app.route('/loadQuestionStud')
def loadQuestionStud():
    question_id = request.args.get('question_id')
    totalQCount = request.args.get('total')
    qnum= request.args.get('qnum')
    print('Question Num:'+str(qnum))
    print('totalQCount:'+str(totalQCount))
    print('question_id:'+str(question_id))
    btn = request.args.get('btn')
    ######################################################
    response_option = request.args.get('response_option')
    resp_session_id = request.args.get('resp_session_id')
    subject_id =  request.args.get('subject_id')
    last_q_id =  request.args.get('last_q_id')
    print('This is the response session id in: ' + str(resp_session_id) )
    if current_user.is_anonymous:        
        studentRow=StudentProfile.query.filter_by(user_id=app.config['ANONYMOUS_USERID']).first()
    else:
        studentRow=StudentProfile.query.filter_by(user_id=current_user.id).first()
    #print('#######this is the current user id'+ str(current_user.id))
    resp_id = str(resp_session_id)
    sessionDetailRow = SessionDetail.query.filter_by(resp_session_id = resp_id).first()
    #print('########### Session details have been fetched')
    #print(sessionDetailRow)
    teacherID = sessionDetailRow.teacher_id
    # If Test is submitted
    if btn=='submit' or btn=='timeout':
        totalMarksQuery = "select sum(marks_scored) as total_marks, count(*) as num_of_questions from response_capture where student_id="+str(studentRow.student_id)+" and resp_session_id='"+str(resp_session_id)+"'"
        print('Total Marks Query:'+totalMarksQuery)
        totalQ = "select count(*) as num_of_questions from test_questions where test_id='"+str(sessionDetailRow.test_id)+"'"
        print('Query:'+str(totalQ))
        totalQ = db.session.execute(text(totalQ)).first()
        
        print('Total questions:'+str(totalQ.num_of_questions))
        totalMarksVal = db.session.execute(text(totalMarksQuery)).first()
        neg_marks = SessionDetail.query.filter_by(resp_session_id=resp_session_id).first()
        # marksScoredQuery =  "select sum(suggested_weightage) as marks_scored, count(*) as correct_ans from question_details where question_id "
        # marksScoredQuery=marksScoredQuery+"in (select distinct question_id from response_capture where is_correct='Y' and "
        # marksScoredQuery=marksScoredQuery+"student_id="+str(studentRow.student_id)+" and resp_session_id='"+str(resp_session_id)+"')"
        incorrect_ques = "select count(*) as incorrect_ques from response_capture rc where is_correct = 'N' and resp_session_id = '"+str(resp_session_id)+"' and (answer_status=239 or answer_status=241)"
        print(' Query for incorrect question:'+str(incorrect_ques))
        incorrect_ques = db.session.execute(text(incorrect_ques)).first()
        marksScoredQuery = "select sum(marks_scored) as marks_scored, count(*) as correct_ans from response_capture where is_correct='Y' and student_id="+str(studentRow.student_id)+" and resp_session_id='"+str(resp_session_id)+"' and (answer_status='239' or answer_status='241')"
        print('Query for scored marks:'+str(marksScoredQuery))
        marksScoredVal = db.session.execute(text(marksScoredQuery)).first()
        print('Marks Scored Query:'+marksScoredQuery)
        print('Marks Scored:'+str(marksScoredVal.marks_scored))
        print('Total Marks:'+str(totalMarksVal.total_marks))
        negative_marks = 0
        marks_scored = 0
        if neg_marks.incorrect_marks>0:
            print('incorrect Ques:'+str(incorrect_ques.incorrect_ques))

            negative_marks = int(neg_marks.incorrect_marks) * int(incorrect_ques.incorrect_ques)
        if marksScoredVal.marks_scored!=None:
            print('inside marksscoredval is not empty')
            marks_scored = int(marksScoredVal.marks_scored)
        if negative_marks>0:
            print('Negative Marks:'+str(negative_marks))
            marks_scored = int(marks_scored) - int(negative_marks)
        else:
            marks_scored = int(marks_scored)
        try:
            if marks_scored>0:
                marksPercentage = (marks_scored/sessionDetailRow.total_marks) *100
            else:
                marksPercentage = 0
        except:
            marksPercentage=0        
        
        print('Marks Percentage:'+str(marksPercentage))
        if studentRow.points!=None and studentRow.points!="":
            studentRow.points = int(studentRow.points) + 1
            db.session.commit()
        return render_template('_feedbackReportIndiv.html',btn=btn,totalQ=totalQ,sessionDetailRow=sessionDetailRow,marksPercentage=marksPercentage,marksScoredVal=marksScoredVal , marks_scored= marks_scored,totalMarksVal =totalMarksVal, student_id=studentRow.student_id, student_name= studentRow.full_name, resp_session_id = resp_session_id )

    # End
    if btn=='next':
        responseStudUpdateQuery=ResponseCapture(school_id=studentRow.school_id,student_id=studentRow.student_id,
            question_id= last_q_id, teacher_id= teacherID,
            class_sec_id=studentRow.class_sec_id, subject_id = subject_id, resp_session_id = resp_session_id, marks_scored= sessionDetailRow.correct_marks,answer_status=242,last_modified_date= date.today())
        
        print(responseStudUpdateQuery)
        db.session.add(responseStudUpdateQuery)
        db.session.commit()
    print('qId:'+str(last_q_id))
    checkResponse = ''
    if last_q_id:
        print('inside if qId not empty')
        checkResponse = ResponseCapture.query.filter_by(resp_session_id = resp_session_id,question_id= last_q_id).first()
        if checkResponse:
            if btn=='submitandnext':
                print('inside submitandnext')
                checkResponse.answer_status = 239
                db.session.commit()
            if btn=='save':
                print('inside savebtn')
                checkResponse.answer_status = 241
                db.session.commit()
    if response_option!='':
        #print('###############Response option is not null###############. This is it' + str(response_option)+ '-')
        optionCheckRow = QuestionOptions.query.filter_by(question_id=last_q_id, option=response_option).first()                    

        #print('this is optionCheckRow'+ str(optionCheckRow))
        ansCheck = ''
        if (optionCheckRow==None):
            ansCheck='N'
        elif (optionCheckRow.is_correct=='Y'):
            ansCheck='Y'
        else:
            ansCheck='N'
             
        print('Class:'+str(studentRow.class_sec_id))
        resp_weightage = SessionDetail.query.filter_by(resp_session_id=resp_session_id).first()
        if checkResponse:
            if checkResponse.response_option==None or checkResponse.response_option:
                checkResponse.response_option = response_option
                checkResponse.is_correct = ansCheck
                
                db.session.commit()
            print('data already exist')
        else:
            print('new data insert in response capture')
            responseStudUpdateQuery=ResponseCapture(school_id=studentRow.school_id,student_id=studentRow.student_id,
            question_id= last_q_id, response_option=response_option, is_correct = ansCheck, teacher_id= teacherID,
            class_sec_id=studentRow.class_sec_id, subject_id = subject_id, resp_session_id = resp_session_id, marks_scored= resp_weightage.correct_marks,answer_status=240,last_modified_date= date.today())
            print(responseStudUpdateQuery)
            db.session.add(responseStudUpdateQuery)
            db.session.commit()
            if btn=='submitandnext':
                print('inside submitandnext')
                response_cap = ResponseCapture.query.filter_by(resp_session_id = resp_session_id,question_id= last_q_id).first()
                response_cap.answer_status = 239
                db.session.commit()
            if btn=='save':
                print('inside savebtn')
                response_cap = ResponseCapture.query.filter_by(resp_session_id = resp_session_id,question_id= last_q_id).first()
                response_cap.answer_status = 241
                db.session.commit()
        
        print('Question numbering')
        
        
        # if btn=='next':
        #     print('inside nextbtn')
        #     response_cap = ResponseCapture.query.filter_by(resp_session_id = resp_session_id,question_id= last_q_id).first()
        #     response_cap.answer_status = 242
        #     db.session.add(response_cap)
        #     db.session.commit()
        
        ######################################################
    # correctOpt = ''
    # question = ''
    # questionOp = ''
    if int(qnum)<= int(totalQCount):
        print('###############q number LESS THAN TOTAL Q COUNT###############')
        question = QuestionDetails.query.filter_by(question_id=question_id, archive_status='N').first()
        questionOp = QuestionOptions.query.filter_by(question_id=question_id).order_by(QuestionOptions.option).all()
        print('this is the last q id#################:'+last_q_id)
        
        answerRes = ResponseCapture.query.filter_by(resp_session_id = resp_session_id).all()
        # session['status'] = []
        answer_list = []
        print('response_session_id:'+str(resp_session_id))
        for row in answerRes:
            answer_pair = []
            answer_pair.append(row.question_id)
            answer_pair.append(row.answer_status)
            answer_list.append(answer_pair)
        # session['status'] = answer_list
        status = 0
        # print(session['status'])
        for row in answer_list:
            print(row[0])
            print(row[1])
        chooseOption = ResponseCapture.query.filter_by(resp_session_id = resp_session_id,question_id=question_id).first()
        correctOpt = ''
        if chooseOption:
            correctOpt = chooseOption.response_option
        return render_template('_questionStud.html',correctOpt = correctOpt,duration=sessionDetailRow.test_time,btn=btn,answer_list=answer_list,question=question, questionOp=questionOp,qnum = int(qnum)+1,totalQCount = totalQCount, last_q_id=question_id)
    # else:
    #     return jsonify(['0'])
    #     print('###############q number MORE THAN TOTAL Q COUNT###############')
    #     # totalMarksQuery = "select sum(suggested_weightage) as total_marks, count(*) as num_of_questions  from question_details where question_id in "
    #     # totalMarksQuery =  totalMarksQuery +"(select distinct question_id from test_questions t1 inner join session_detail t2 on "
    #     # totalMarksQuery =  totalMarksQuery +"t1.test_id=t2.test_id and t2.resp_session_id='"+str(resp_session_id)+"') "

    #     totalMarksQuery = "select sum(marks_scored) as total_marks, count(*) as num_of_questions from response_capture where student_id="+str(studentRow.student_id)+" and resp_session_id='"+str(resp_session_id)+"'"
    #     print('Total Marks Query:'+totalMarksQuery)
    #     totalMarksVal = db.session.execute(text(totalMarksQuery)).first()
    #     neg_marks = SessionDetail.query.filter_by(resp_session_id=resp_session_id).first()
    #     # marksScoredQuery =  "select sum(suggested_weightage) as marks_scored, count(*) as correct_ans from question_details where question_id "
    #     # marksScoredQuery=marksScoredQuery+"in (select distinct question_id from response_capture where is_correct='Y' and "
    #     # marksScoredQuery=marksScoredQuery+"student_id="+str(studentRow.student_id)+" and resp_session_id='"+str(resp_session_id)+"')"
    #     incorrect_ques = "select count(*) as incorrect_ques from response_capture rc where is_correct = 'N' and resp_session_id = '"+str(resp_session_id)+"'"
    #     incorrect_ques = db.session.execute(text(incorrect_ques)).first()
    #     marksScoredQuery = "select sum(marks_scored) as marks_scored, count(*) as correct_ans from response_capture where is_correct='Y' and student_id="+str(studentRow.student_id)+" and resp_session_id='"+str(resp_session_id)+"'"
    #     marksScoredVal = db.session.execute(text(marksScoredQuery)).first()
    #     print('Marks Scored Query:'+marksScoredQuery)
    #     print('Marks Scored:'+str(marksScoredVal.marks_scored))
    #     print('Total Marks:'+str(totalMarksVal.total_marks))
    #     negative_marks = 0
    #     marks_scored = 0
    #     if neg_marks.incorrect_marks>0:
    #         negative_marks = int(neg_marks.incorrect_marks) * int(incorrect_ques.incorrect_ques)
    #     if negative_marks>0:
    #         marks_scored = int(marksScoredVal.marks_scored) - int(negative_marks)
    #     try:
    #         if marks_scored>0:
    #             marksPercentage = (marks_scored/totalMarksVal.total_marks) *100
    #         else:
    #             marksPercentage = 0
    #     except:
    #         marksPercentage=0        
        
    #     print('Marks Percentage:'+str(marksPercentage))
    #     if studentRow.points!=None and studentRow.points!="":
    #         studentRow.points = int(studentRow.points) + 1
    #         db.session.commit()
    #     return render_template('_feedbackReportIndiv.html',marksPercentage=marksPercentage,marksScoredVal=marksScoredVal , marks_scored= marks_scored,totalMarksVal =totalMarksVal, student_id=studentRow.student_id, student_name= studentRow.full_name, resp_session_id = resp_session_id )
    


#@app.route('/responseStudUpdate')
#@login_required
#def responseStudUpdate():        
#    question_id = request.args.get('question_id')
#    response_option = request.args.get('response_option')
#    resp_session_id = request.args.get('resp_session_id')
#    subject_id =  request.args.get('subject_id')
#
#    studentRow=StudentProfile.query.filter_by(user_id=current_user.id).first()
#
#    sessionDetailRow = SessionDetail.query.filter_by(resp_session_id = resp_session_id).first()
#    teacherID = sessionDetailRow.teacher_id
#
#    optionCheckRow = QuestionOptions.query.filter_by(question_id=splitVal[0], option=response_option).first()                    
#
#    #print('this is optionCheckRow'+ str(optionCheckRow))
#    ansCheck = ''
#    if (optionCheckRow==None):
#        ansCheck='N'
#    elif (optionCheckRow.is_correct=='Y'):
#        ansCheck='Y'
#    else:
#        ansCheck='N'
#
#    responseStudUpdateQuery=ResponseCapture(school_id=studentRow.school_id,student_id=studentRow.student_id,
#        question_id= question_id, response_option=response_option, is_correct = ansCheck, teacher_id= teacherID,
#        class_sec_id=studentRow.class_sec_id, subject_id = subject_id, resp_session_id = resp_session_id,last_modified_date= date.today())
#    db.session.add(responseStudUpdateQuery)
#    db.session.commit()
#    return jsonify(['0'])
#

@app.route('/questionAllDetails')
def questionAllDetails():
    question_id = request.args.get('question_id')
    totalQCount = ''
    qnum= ''
    question = QuestionDetails.query.filter_by(question_id=question_id, archive_status='N').first()
    questionOp = QuestionOptions.query.filter_by(question_id=question_id).order_by(QuestionOptions.option_id).all()
    
    return render_template('_question.html',question=question, questionOp=questionOp,qnum = qnum,totalQCount = totalQCount,  )    




@app.route('/decodes', methods=['GET', 'POST'])
def decodeAjax():
    if request.method == 'POST':
        decodedData = barCode.decode(request.form['imgBase64'])
        if decodedData:
            json_data = json.dumps(decodedData)
            print(json_data)
            return jsonify(json_data)
        return jsonify(['NO BarCode Found'])

@app.route('/responseDBUpdate', methods=['POST'])
def responseDBUpdate():   
    print('Inside Response DB Update')     
    responseList=request.json
    responseSessionID=request.args.get('resp_session_id')
    responseArray = {}
    if responseList:
        #print(responseList)        
        for key, value in responseList.items():
            if key =="formdataVal":
                responseArray = value
                for val in responseArray:

                    #print('this is val: ' + str(val))
                    splitVal= re.split('[:]', val)
                    #print('this is splitVal'+ str(splitVal))
                    response = splitVal[1]
                    #print('this is response from SplitVal[1]' + response)
                    responseSplit = re.split('-|@',response)
                    #print('Response split is: '+ str(responseSplit ))
                    
                    teacherIDRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
                    print('Class Section Id in Response DB Update:'+str(responseSplit[0]))
                    studentDetailQuery = "select class_sec_id from student_profile where student_id=" + responseSplit[0]
                    studentDetailRow = db.session.execute(text(studentDetailQuery)).first()

                    #studentDetailQuery = "select class_sec_id from student_profile where student_id=" + responseSplit[0]
                    questionDetailRow = QuestionDetails.query.filter_by(question_id=splitVal[0], archive_status='N').first()
                    
                    dateVal= datetime.today().strftime("%d%m%Y")

                    # responseSessionID =  str(questionDetailRow.subject_id) + str(dateVal) + str(studentDetailRow.class_sec_id)
                    # print('Class section Id in response DB Update:'+str(studentDetailRow.class_sec_id))
                    print('this is the response session id: ' + str(responseSessionID))
                    #the response session id is a combination of today's date, subject id and the class section id

                    optionCheckRow = QuestionOptions.query.filter_by(question_id=splitVal[0], option=responseSplit[3]).first()
                    

                    #print('this is optionCheckRow'+ str(optionCheckRow))
                    ansCheck = ''
                    if (optionCheckRow==None):
                        ansCheck='N'
                    elif (optionCheckRow.is_correct=='Y'):
                        ansCheck='Y'
                    else:
                        ansCheck='N'

                    weightage = SessionDetail.query.filter_by(resp_session_id=responseSessionID).first()

                    responsesForQuest=ResponseCapture(school_id=teacherIDRow.school_id,student_id=responseSplit[0],
                    question_id= splitVal[0], response_option= responseSplit[3], is_correct = ansCheck, teacher_id= teacherIDRow.teacher_id,
                    class_sec_id=studentDetailRow.class_sec_id, subject_id = questionDetailRow.subject_id, resp_session_id = responseSessionID,last_modified_date= datetime.now(),marks_scored=weightage.correct_marks,answer_status=239)
                    db.session.add(responsesForQuest)
                    db.session.commit()
                #flash('Response Entered')
                return jsonify(['Data ready for entry'])
    return jsonify(['No records entered to DB'])
  
@app.route('/feedbackReport')
def feedbackReport():    
    fromClassPerf = request.args.get('fromClassPerf')
    responseSessionID=request.args.get('resp_session_id')
    print('Response Session Id in FeedBack Report route'+str(responseSessionID))
    if fromClassPerf!=None:
    #questionListJson=request.args.get('question_id')
        class_val=request.args.get('class_val')
        subject_id=request.args.get('subject_id')
    ##print('here is the class_val '+ str(class_val))
        section=request.args.get('section')
        section = section.strip()
        dateVal = request.args.get('date')
    print('Class Perf:'+str(fromClassPerf))
    
    #print('here is the section '+ str(section))
    #if (questionListJson != None) and (class_val != None) and (section != None):
    
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()
#
    if fromClassPerf!=None:
#
        classSecRow = ClassSection.query.filter_by(class_val=class_val, section=section, school_id=teacher.school_id).first()       
        print('here is the subject_id: '+ str(subject_id))
    #    #questionDetailRow = QuestionDetails.query.filter_by(question_id=questionListJson[1]).first()
    #    
        if dateVal == None or dateVal=="":
            dateVal= datetime.today().strftime("%d%m%Y")
        else:
            tempDate=dt.datetime.strptime(dateVal,'%Y-%m-%d').date()
            dateVal= tempDate.strftime("%d%m%Y")
            print('Date:'+str(dateVal)+'Subject Id:'+str(subject_id)+'Class Section Id:'+str(classSecRow.class_sec_id))
        responseSessionID = str(dateVal) + str(subject_id) + str(classSecRow.class_sec_id)

    if responseSessionID!=None:
        #
        # print('Class Section Id in feedbackReport:'+str(classSecRow.class_sec_id))
        print('Here is response session id in feedback report: ' + responseSessionID)   
        # responseResultQuery = "with total_marks_cte as ( "
        # responseResultQuery = responseResultQuery + "select sum(suggested_weightage) as total_weightage, count(*) as num_of_questions  from question_details where question_id in "
        # responseResultQuery = responseResultQuery + "(select distinct question_id from test_questions t1 inner join session_detail t2 on "
        # responseResultQuery = responseResultQuery + "t1.test_id=t2.test_id and t2.resp_session_id='"+str(responseSessionID)+"') ) "
        # responseResultQuery = responseResultQuery + "select distinct sp.roll_number, sp.full_name, sp.student_id, "
        # responseResultQuery = responseResultQuery + "SUM(CASE WHEN rc.is_correct='Y' THEN qd.suggested_weightage ELSE 0 end) AS  points_scored , "
        # responseResultQuery = responseResultQuery + "total_marks_cte.total_weightage "
        # responseResultQuery = responseResultQuery + "from response_capture rc inner join student_profile sp on "
        # responseResultQuery = responseResultQuery + "rc.student_id=sp.student_id "
        # responseResultQuery = responseResultQuery + "inner join question_details qd on "
        # responseResultQuery = responseResultQuery + "qd.question_id=rc.question_id "
        # responseResultQuery = responseResultQuery + "and rc.resp_session_id='"+str(responseSessionID)+"', total_marks_cte "
        # responseResultQuery = responseResultQuery + "group by sp.roll_number, sp.full_name, sp.student_id, total_marks_cte.total_weightage "
        responseResultQuery = "select distinct sp.roll_number, sp.full_name, sp.student_id,SUM(CASE WHEN rc.is_correct='Y' and rc.resp_session_id = '"+str(responseSessionID)+"' and (rc.answer_status='239' or answer_status='241') THEN rc.marks_scored ELSE 0 end) as marks_scored from "
        responseResultQuery = responseResultQuery + "student_profile sp inner join response_capture rc on sp.student_id = rc.student_id where "
        responseResultQuery = responseResultQuery + "rc.resp_session_id = '"+str(responseSessionID)+"' "
        responseResultQuery = responseResultQuery + "group by sp.roll_number, sp.full_name, sp.student_id"
        print('Query:'+str(responseResultQuery))
        responseResultRow = db.session.execute(text(responseResultQuery)).fetchall()
        responseResultRowCount = 0
        total = SessionDetail.query.filter_by(resp_session_id=responseSessionID).first()
        incorrect_ques = "select count(*) as incorrect_ques from response_capture rc where is_correct = 'N' and resp_session_id = '"+str(responseSessionID)+"' and (answer_status='239' or answer_status='241')"
        incorrect_ques = db.session.execute(text(incorrect_ques)).first()
        neg_marks = 0
        if total.incorrect_marks>0:
            neg_marks = int(incorrect_ques.incorrect_ques)*int(total.incorrect_marks)
        if responseResultRow:
            totalPointsScored =  0
            totalPointsLimit = 0   
            # print(responseResultRow)
            # print('ResultRow length:'+str(len(responseResultRow)))         
            # for row in responseResultRow:
            #     totalPointsScored = totalPointsScored + row.points_scored
            #     totalPointsLimit = totalPointsLimit + row.total_weightage
            totalPointsLimit = total.total_marks
            for row in responseResultRow:
                totalPointsScored = row.marks_scored
            classAverage = 0
            totalPointsScored = totalPointsScored - neg_marks
            if totalPointsLimit !=0 and totalPointsLimit != None:
                if totalPointsScored>0:
                    classAverage = (totalPointsScored/totalPointsLimit) *100
                else:
                    classAverage = 0
            else:
                classAverage = 0
                print("total Points limit is zero")

            responseResultRowCount = len(responseResultRow)
        #print('Here is the questionListJson: ' + str(questionListJson))
    else:
        print("Error collecting data from ajax request. Some values could be null")

    if responseResultRowCount>0:
        return render_template('_feedbackReport.html',totalPointsLimit=totalPointsLimit,neg_marks=neg_marks,classAverage=classAverage, classSecCheckVal=classSecCheck(),responseResultRow= responseResultRow,  responseResultRowCount = responseResultRowCount, resp_session_id = responseSessionID)
    else:
         return jsonify(['NA'])
         


@app.route('/studentFeedbackReport')
@login_required
def studentFeedbackReport():
    student_id = request.args.get('student_id')  
    student_name = request.args.get('student_name') 
    student_id=student_id.strip()
    resp_session_id = request.args.get('resp_session_id')
    #responseCaptureRow = ResponseCapture.query.filter_by(student_id = student_id, resp_session_id = resp_session_id).all()    
    responseCaptureQuery = "select rc.student_id,qd.question_id, qd.question_description, rc.response_option, qo2.option_desc as option_desc,qo.option_desc as corr_option_desc, "   
    responseCaptureQuery = responseCaptureQuery +"qo.option as correct_option, rc.answer_status, "
    responseCaptureQuery = responseCaptureQuery +"CASE WHEN qo.option= response_option THEN 'Correct' ELSE 'Not Correct' END AS Result "
    responseCaptureQuery = responseCaptureQuery +"from response_capture rc  "
    responseCaptureQuery = responseCaptureQuery +"inner join question_Details qd on rc.question_id = qd.question_id  and qd.archive_status='N' "    
    responseCaptureQuery = responseCaptureQuery +"left join question_options qo on qo.question_id = rc.question_id and qo.is_correct='Y'  "
    responseCaptureQuery = responseCaptureQuery +"inner join question_options qo2 on qo2.question_id = rc.question_id and qo2.option = rc.response_option "
    responseCaptureQuery = responseCaptureQuery +"where student_id='" +  str(student_id) + "' and rc.resp_session_id='"+str(resp_session_id)+ "'"
    print('Response Capture Query:'+str(responseCaptureQuery))
    responseCaptureRow = db.session.execute(text(responseCaptureQuery)).fetchall()

    return render_template('studentFeedbackReport.html',classSecCheckVal=classSecCheck(),student_name=student_name, student_id=student_id, resp_session_id = resp_session_id, responseCaptureRow = responseCaptureRow,disconn=1)

@app.route('/testPerformance')
@login_required
def testPerformance():
    user = User.query.filter_by(username=current_user.username).first_or_404()        
    teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
    
    #setting up testperformance form
    form=testPerformanceForm()    
    test_date = "select distinct m.description as type,p.date as date,m.msg_id as id,c.class_val as class,c.section as section from performance_detail p,message_detail m,class_section c where c.school_id='"+str(teacher.school_id)+"' and p.school_id='"+str(teacher.school_id)+"' and p.test_type=m.msg_id and c.class_sec_id=p.class_sec_id order by date desc fetch next 10 rows only"  
    datelist = db.session.execute(text(test_date)).fetchall()
    for date in datelist:
        print(str(date.date.date())+' '+str(date.type))
    available_class=ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher.school_id).order_by(ClassSection.class_val).all()
    available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher.school_id).all()    
    available_test_type=MessageDetails.query.filter_by(category='Test type').all()

    class_list=[(str(i.class_val), "Class "+str(i.class_val)) for i in available_class]
    section_list=[(i.section,i.section) for i in available_section]    
    test_type_list=[(i.msg_id,i.description) for i in available_test_type]

    #selectfield choices
    form.class_val.choices = class_list
    form.subject_name.choices= ''
    form.section.choices = ''
    # section_list    
    form.test_type.choices=test_type_list

    #setting up studentperformance form
    form1=studentPerformanceForm()
    
    available_class=ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher.school_id).all()
    available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher.school_id).all()    
    available_test_type=MessageDetails.query.filter_by(category='Test type').all()
    available_student_list=StudentProfile.query.filter_by(school_id=teacher.school_id).all()


    class_list=[(str(i.class_val), "Class "+str(i.class_val)) for i in available_class]
    section_list=[(i.section,i.section) for i in available_section]    
    test_type_list=[(i.msg_id,i.description) for i in available_test_type]
    student_list=[(i.student_id,i.full_name) for i in available_student_list]
    resultSet = db.session.execute(text("Select * from fn_overall_performance_summary('"+str(teacher.school_id)+"') where class='All' and section='All'")).fetchall()
    avg_scores = []
    resultSetCount = 0
    # print('Length of Result Set:'+len(resultSet))
    for resultNum in resultSet:
        resultSetCount+=1
        print('#######################first  Resultset:'+str(resultSetCount))

    #for resultNum in resultSet:
    #    #resultSetCount+=1
    #    print('#######################second  Resultset:'+str(resultSetCount))

    #selectfield choices
    form1.class_val1.choices = class_list
    form1.section1.choices= ''
    # section_list    
    form1.test_type1.choices=test_type_list
    form1.student_name1.choices = ''
    findStudentData = "select p.full_name as full_name,p.student_id as student_id,c.class_val as class  from student_profile as p,class_section as c where p.school_id='"+str(teacher.school_id)+"' and c.school_id='"+str(teacher.school_id)+"' and p.class_sec_id=c.class_sec_id"
    print('Query:'+str(findStudentData))
    students = db.session.execute(text(findStudentData))
    print(students)
    print('Inside Test Performance')
    return render_template('testPerformance.html',classSecCheckVal=classSecCheck(),form=form,form1=form1,resultSetCount=resultSetCount,resultSet=resultSet,datelist=datelist,students=students)


@app.route('/testPerformanceGraph')
@login_required
def testPerformanceGraph():  
    print('Inside testPerformanceGraph')  
    class_val=request.args.get('class_val')
    section=request.args.get('section')
    section = section.strip()    
    test_type=request.args.get('test_type')
    print('class:'+class_val+'section:'+section+'test_type:'+test_type)
    #print('here is the class_val '+ str(class_val))
    dateVal = request.args.get('date')
    print('Date:'+dateVal)
    if dateVal ==None or dateVal=="":
        dateVal= datetime.today()

    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    classSectionRows=ClassSection.query.filter_by(class_val=int(class_val),section=section, school_id=teacher.school_id).first()
        
    testPerformanceQuery = "select sp.full_name, pd.student_score, md.description "
    testPerformanceQuery = testPerformanceQuery + "from performance_detail pd "
    testPerformanceQuery = testPerformanceQuery + "inner join student_profile sp on "
    testPerformanceQuery = testPerformanceQuery + "sp.student_id=pd.student_id inner join "
    testPerformanceQuery = testPerformanceQuery + "message_detail md on md.msg_id=pd.subject_id "
    testPerformanceQuery = testPerformanceQuery + "where "
    testPerformanceQuery = testPerformanceQuery + "pd.class_sec_id='"+str(classSectionRows.class_sec_id) +"' "
    testPerformanceQuery = testPerformanceQuery + "and "
    testPerformanceQuery = testPerformanceQuery + "pd.date='"+ str(dateVal) +"' "
    testPerformanceQuery = testPerformanceQuery + "and test_type='"+ str(test_type)+ "'"  

    testPerformanceRecords = db.session.execute(text(testPerformanceQuery)).fetchall()
        
    if len(testPerformanceRecords) !=0:

        df = pd.DataFrame( [[ij for ij in i] for i in testPerformanceRecords])
        df.rename(columns={0: 'full_name', 1: 'student_score', 2: 'subject'}, inplace=True)

        student_names= list(df['full_name'])
        student_scores= list(df['student_score'])
        subject= list(df['subject'])    

        distinct_subjects= df['subject'].unique()
        
        subLevelData=[]
        i=0
        for subVal in distinct_subjects:
            filtered_df=df[df.subject==subVal]
            filtered_df_student = list(filtered_df['full_name'])
            filtered_df_student_scored = list(filtered_df['student_score'])            
            tempDict = dict(y=filtered_df_student,x=filtered_df_student_scored,type='bar',name=subVal,orientation='h')
            subLevelData.append(tempDict)
        print(str(subLevelData))

        graphData=[dict()]

        graphJSON = json.dumps(subLevelData, cls=plotly.utils.PlotlyJSONEncoder)        
        return render_template('_testPerformanceGraph.html',graphJSON=graphJSON)
    else:
        return jsonify(['No records found for the selected date'])
    

@app.route('/studentPerformanceGraph')
@login_required
def studentPerformanceGraph(): 
    print('Inside Student performance graph')
      
    class_val=request.args.get('class_val')
    section=request.args.get('section')
    fromPractice = request.args.get('fromPractice')
    print('##### this is the value of fromPractice: '+ str(fromPractice))
    if section!=None:
        section = section.strip()    
    test_type=request.args.get('test_type')
    student_id=request.args.get('student_id')      
    print("Student id is: "+str(student_id))  
    dateVal = request.args.get('date')
    
    if dateVal ==None or dateVal=="":
        dateVal= datetime.today()
    
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    fromTestPerformance=0
    
    if fromPractice=='1':
        print('######using newer query')
        studPerformanceQuery = "select test_date as date, CAST(perf_percentage AS INTEGER) as student_score, subject as description"
        studPerformanceQuery = studPerformanceQuery + " from fn_student_performance_response_capture("+str(student_id)+") "
    else:
        print('#######using older query')
        studPerformanceQuery = "select pd.date, CAST(pd.student_score AS INTEGER) as student_score,md.description "
        studPerformanceQuery = studPerformanceQuery + "from performance_detail pd "
        studPerformanceQuery = studPerformanceQuery + "inner join "
        studPerformanceQuery = studPerformanceQuery + "message_detail md on md.msg_id=pd.subject_id "
        studPerformanceQuery = studPerformanceQuery + "and "
        studPerformanceQuery = studPerformanceQuery + "pd.student_id='"+ str(student_id) +"' order by date"            
    

    studPerformanceRecords = db.session.execute(text(studPerformanceQuery)).fetchall()
        
    if len(studPerformanceRecords) !=0:
        df = pd.DataFrame( [[ij for ij in i] for i in studPerformanceRecords])
        df.rename(columns={0: 'date', 1: 'student_score', 2: 'subject'}, inplace=True)

        dateRange= list(df['date'])
        student_scores= list(df['student_score'])
        subject= list(df['subject'])

        distinct_subjects= df['subject'].unique()
        subLevelData=[]
        i=0
        for subVal in distinct_subjects:
            filtered_df=df[df.subject==subVal]
            filtered_df_date = list(filtered_df['date'])
            filtered_df_student_scored = list(filtered_df['student_score'])
            tempDict = dict(y=filtered_df_student_scored,x=filtered_df_date,mode= 'lines+markers',type='scatter',name=subVal,line_shape="spline", smoothing= '1.5')
            subLevelData.append(tempDict)
        print(str(subLevelData))

        graphData=[dict()]

        graphJSON = json.dumps(subLevelData, cls=plotly.utils.PlotlyJSONEncoder)        
        return render_template('_studentPerformanceGraph.html',graphJSON=graphJSON)
    else:
        return jsonify(['No performance data found'])
  


@app.route('/classPerformance')
@login_required
def classPerformance():
    form=feedbackReportForm()

    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()

    available_class=ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).order_by(ClassSection.class_val).all()
    available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher_id.school_id).all()    
    available_subject=MessageDetails.query.filter_by(category='Subject').all()


    class_list=[(str(i.class_val), "Class "+str(i.class_val)) for i in available_class]
    section_list=[(i.section,i.section) for i in available_section]    
    subject_name_list=[(i.msg_id,i.description) for i in available_subject]

    #selectfield choices
    form.class_val.choices = class_list
    form.section.choices= ''
    # section_list    
    form.subject_name.choices= ''
    # subject_name_list

    testDetailQuery = "select distinct t1.resp_session_id, t1.last_modified_Date as test_date, t5.teacher_name as conducted_by,t4.class_val, t4.section, "
    testDetailQuery = testDetailQuery+ "t3.description as subject "
    testDetailQuery = testDetailQuery+ " from session_detail t1 "
    testDetailQuery = testDetailQuery+ " inner join test_details t2 on t2.test_id=t1.test_id "
    testDetailQuery = testDetailQuery+ " inner join message_detail t3 on t2.subject_id=t3.msg_id "
    testDetailQuery = testDetailQuery+ " inner join class_section t4 on t1.class_Sec_id=t4.class_sec_id "
    testDetailQuery = testDetailQuery+ " inner join teacher_profile t5 on t5.teacher_id=t1.teacher_id  and t5.school_id='"+str(teacher_id.school_id)+"' order by test_date desc "
    testDetailRows= db.session.execute(text(testDetailQuery)).fetchall()
    return render_template('classPerformance.html',classSecCheckVal=classSecCheck(),form=form, school_id=teacher_id.school_id, testDetailRows=testDetailRows,user_type_val=str(current_user.user_type))



@app.route('/resultUpload',methods=['POST','GET'])
@login_required
def resultUpload():
    #selectfield choices list
    qclass_val = request.args.get('class_val')
    qsection=request.args.get('section')
    print('Section:'+str(qsection))

    user = User.query.filter_by(username=current_user.username).first_or_404()    
    teacher= TeacherProfile.query.filter_by(user_id=user.id).first()     
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id=SchoolProfile.query.with_entities(SchoolProfile.board_id).filter_by(school_id=teacher_id.school_id).first()
    distinctClasses = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacher.school_id)+" GROUP BY class_val order by s")).fetchall()        
    classSections=ClassSection.query.filter_by(school_id=teacher.school_id).all()

    count = 0
    #this section is to load the page for the first class section if no query value has been provided
    if qclass_val==None:
        for section in classSections:                
            if count==0:
                getClassVal = section.class_val
                getSection = section.section          
                print('set class and section values for first load')      
        #if no value has been passed for class and section in query string then use the values fetched from db
                qclass_val = getClassVal
                qsection=getSection
                count+=1
            
    test_type = MessageDetails.query.filter_by(category='Test type').all()
    test_details = "select test_id,date_of_creation,description as subject_name from test_details td inner join message_detail md on md.msg_id=td.subject_id where class_val='"+str(qclass_val)+"' and school_id='"+str(teacher_id.school_id)+"'"
    test_details = db.session.execute(test_details).fetchall()
    for section in classSections:
            print("Class Section:"+section.section)
    subject_name = []
    if current_user.is_authenticated:
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        print('Class value:'+str(qclass_val))
        print('school_id:'+str(teacher_id.school_id))
        class_sec_id=ClassSection.query.filter_by(class_val=str(qclass_val),school_id=teacher_id.school_id,section=qsection).all()
        
        print(teacher_id.school_id)
        class_value = str(qclass_val)
        print('Class Value:'+str(class_value))
        for section in class_sec_id:
            print('Section Id:'+str(section.class_sec_id))
        student_list = []
        for section in class_sec_id:
            student_list = StudentProfile.query.filter_by(class_sec_id=section.class_sec_id,school_id=teacher_id.school_id).all()
        queryForSubjectName = "select description,msg_id from message_detail where msg_id in (select distinct subject_id from topic_detail where class_val='"+ str(class_value) +"' and board_id='"+ str(board_id[0]) +"')"
        subject_name = db.session.execute(queryForSubjectName).fetchall()
        print('No of Subjects:'+str(len(subject_name)))
        for subjects in subject_name:
            print('Subjects Name:'+subjects[0])        
        return render_template('resultUpload.html',classSecCheckVal=classSecCheck(),test_details=test_details,test_type=test_type,qclass_val=qclass_val,subject_name=subject_name,qsection=qsection, distinctClasses=distinctClasses, classsections=classSections,student_list=student_list,user_type_val=str(current_user.user_type))
        

@app.route('/resultUpload/<class_val>')
def section(class_val):
    if class_val!='All':

        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        sections = ClassSection.query.distinct().filter_by(class_val=class_val,school_id=teacher_id.school_id).all()
        sectionArray = []

        for section in sections:
            sectionObj = {}
            sectionObj['section_id'] = section.class_sec_id
            sectionObj['section_val'] = section.section
            sectionArray.append(sectionObj)
        return jsonify({'sections' : sectionArray})
    else:
        return "return"



@app.route('/fetchStudentsName')
def fetchStudentsName():
    print('Inside fetchStudentsName')
    class_val = request.args.get('class_val')
    section = request.args.get('section')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first() 
    print('class_val:'+class_val)
    query = "select p.full_name as name,p.student_id as id  from student_profile as p,class_section as c where p.school_id='"+str(teacher_id.school_id)+"' and c.school_id='"+str(teacher_id.school_id)+"' and p.class_sec_id="
    if class_val!='All' and section=='All': 
        query =query + "(select class_sec_id from class_section where school_id='"+str(teacher_id.school_id)+"' and class_val='"+str(class_val)+"')"
    if section!='All' and class_val=='All':
        query = query +"(select class_sec_id from class_section where school_id='"+str(teacher_id.school_id)+"' and section='"+str(section)+"')"
    if class_val=='All' and section=='All':
        query = query + "c.class_sec_id"
    if class_val!='All' and section!='All':
        query = query + "(select class_sec_id from class_section where school_id='"+str(teacher_id.school_id)+"' and class_val='"+str(class_val)+"' and section='"+str(section)+"')"
    print('Fetch Student Query:'+query)
    studentList = db.session.execute(text(query))
    
    studentArray = []
    for student in studentList:
        studentObject = {}
        studentObject['student_name'] = str(student[0])
        studentObject['student_id'] = str(student[1])
        studentArray.append(studentObject)
    return jsonify({'studentData':studentArray})




@app.route('/fetchTestDates')
def fetchTestDates():
    print('Inside fetchTestDates')
    class_val = request.args.get('class_val')
    section = request.args.get('section')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first() 
    query = "select distinct m.description as type,p.date as date,m.msg_id as id,c.class_val as class,c.section as section from performance_detail p,message_detail m,class_section c where c.school_id='"+str(teacher_id.school_id)+"' and p.school_id='"+str(teacher_id.school_id)+"'" 
    print(class_val+' '+section)
    if(class_val!='All'):
        query = query + "and c.class_val='"+str(class_val)+"'"
    if(section!='All'): 
        query = query + "and c.section='"+str(section)+"'" 
    query = query + "and p.test_type=m.msg_id and c.class_sec_id=p.class_sec_id order by date desc fetch next 10 rows only"
    print(query)
    dateData = db.session.execute(text(query))
    dateArray = []    
    for data in dateData:
        print('Inside for')
        dateObject = {}
        dateObject['type'] = str(data[0])
        dateObject['date'] = str(data[1].date())
        dateObject['id'] = str(data[2])
        dateObject['class'] = str(data[3])
        dateObject['section'] = str(data[4])
        print(str(data[0])+' '+str(data[1].date())+' '+str(data[2])+' '+str(data[3])+' '+str(data[4]))
        dateArray.append(dateObject)
    return jsonify({'dateData':dateArray})


@app.route('/scoreGraph')
def scoreGraph():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_value = request.args.get('class_val')
    section = request.args.get('section')
    query = "select *from fn_overall_attendance_summary('"+str(teacher_id.school_id)+"') where class='"+str(class_value)+"' and section='"+str(section)+"'"
    attendance = db.session.execute(text(query))
    resultArray = []

    for result in attendance:
        Array = {}
        Array['present'] = str(result.no_of_student_present)
        Array['absent'] = str(result.no_of_student_absent)
        resultArray.append(Array)
    return jsonify({'result':resultArray})

@app.route('/linkWithImpact/<int:impactSchoolID>', methods=["GET","POST"])
@login_required
def linkWithImpact(impactSchoolID):
    teacherProfileData = TeacherProfile.query.filter_by(user_id = current_user.id).first()
    if teacherProfileData!=None:
        schoolProfileData = SchoolProfile.query.filter_by(school_id=teacherProfileData.school_id).first()
        if schoolProfileData!=None:
            schoolProfileData.impact_school_id=impactSchoolID
            db.session.commit()
            status = 0
        else:
            status = 1
    else:
        status = 1
    urlForImpact = app.config['IMPACT_HOST']
    return render_template('linkWithImpact.html',urlForImpact=urlForImpact,status=status,schoolId=schoolProfileData.school_id, impactSchoolID = impactSchoolID)


@app.route('/api/schoolRegistration/<int:impactSchoolID>',methods=["GET","POST"])
def apiSchoolRegistration(impactSchoolID,):
    #Firstly register the school using the data from impact form
    #When inserting a record in schoolProfile ensure that you add the impactSchoolID to it
    ###Use this section to insert into school registration, class section, address and update user as admin
    #
    #
    #
    #
    # if the insert is successful, set status =1
    ###status =1
    ###message = "School registered successfully"
    ###else
    ###status = 0
    ###message = "Error registering school"

    #Secondly return the school_id that has newly been created back to the impact system
    #schoolData = SchoolProfile.query.filter_by(impact_school_id = request.form('impact_school_id')).first()
    #

    #postData= {
    #    "status" : status,
    #    "message" : message
    #    "perf_eval_school_id" : schoolData.school_id
    #}
    return {'result' : postData}    

@app.route('/api/userRegistration',methods=["POST"])
def apiUserRegistration():
    if request.form['internalKey'] == app.config['ALLLEARN_INTERNAL_KEY']:
        userData = User.query.filter_by(email = request.form['email']).first()
        if userData==None:
            user = User(username=request.form['email'], email=request.form['email'], user_type='140', access_status='144', phone=request.form['phone'],
                    first_name = request.form['firstName'],last_name= request.form['lastName'],password_hash=request.form['key'])        
            db.session.add(user)
            db.session.commit()
            print("########## no existing user of the same email")
            return {'result' : 'User Registered successfully', 'value':'0'}  
        else:
            print(str(userData))
            print(str(userData.email))
            print('######### user already present')
            return {'result' : 'User already present','value':'err1'}  
    else:
        return {'result' : 'Key mismatch','value':'err2'}


   


@app.route('/api/performanceSummary/<int:schoolID>')
def apiPerformanceSummary(schoolID):
    query = "Select * from fn_overall_performance_summary("+str(schoolID)+") where class='All'and section='All' and subject='All'"
    
    resultSet = db.session.execute(text(query))
    
    resultArray = []

    for result in resultSet:
        Array = {}
        Array['avg_score'] = str(round(result.avg_score,2))
        Array['highest_mark'] = str(result.highest_mark)
        Array['lowest_mark'] = str(result.lowest_mark)
        Array['no_of_students_above_90'] = str(result.no_of_students_above_90)
        Array['no_of_students_80_90'] = str(result.no_of_students_80_90)
        Array['no_of_students_70_80'] = str(result.no_of_students_70_80)
        Array['no_of_students_50_70'] = str(result.no_of_students_50_70)
        Array['no_of_students_below_50'] = str(result.no_of_students_below_50)
        Array['no_of_students_cross_50'] = str(result.no_of_students_cross_50)
        resultArray.append(Array)
    return {'result' : resultArray}    


@app.route('/testDateSearch/<class_val>')
def testDate(class_val):
    print('Inside TestDate Search')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id=ClassSection.query.filter_by(class_val=int(class_val),school_id=teacher_id.school_id).first()
    testdates = ResultUpload.query.with_entities(ResultUpload.exam_date).distinct().filter_by(class_sec_id=class_sec_id.class_sec_id,school_id=teacher_id.school_id).all()
    print('class value:'+str(class_val)+"School Id:"+str(teacher_id.school_id)+"Teacher_id:"+str(teacher_id.teacher_id)+"userId:"+str(current_user.id))
    
    dates = []
    for test in testdates:
        print("Test Dates:"+str(test.exam_date))
        test = test.exam_date.date().strftime("%d-%B-%Y")
        print('Dates:'+str(test))
        dates.append(test)
    testdateArray = []
    print(dates)
    for testdate in dates:
        testdateObj = {}
        testdateObj['date'] = testdate
        testdateArray.append(testdateObj)
    return jsonify({'testdates' : testdateArray})

@app.route('/resultUploadHistory')
def resultUploadHistory():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()

    uploadHistoryQuery = "select distinct upload_id, cs.class_val, cs.section, "
    uploadHistoryQuery = uploadHistoryQuery + "md.description as test_type, md2.description as subject, date(ru.last_modified_date) as upload_date, date(ru.exam_date) as exam_date "
    uploadHistoryQuery = uploadHistoryQuery +"from result_upload ru inner join  class_section cs on  cs.class_sec_id=ru.class_sec_id and cs.school_id='"+str(teacher_id.school_id)+"' "
    uploadHistoryQuery = uploadHistoryQuery +"inner join message_detail md on md.msg_id=ru.test_type inner join message_detail md2 on md2.msg_id=ru.subject_id order by exam_date desc"
    
    uploadHistoryRecords = db.session.execute(text(uploadHistoryQuery)).fetchall()
    return render_template('resultUploadHistory.html',uploadHistoryRecords=uploadHistoryRecords,user_type_val=str(current_user.user_type))


@app.route('/uploadHistoryDetail',methods=['POST','GET'])
def uploadHistoryDetail():
    upload_id=request.args.get('upload_id')
    resultDetailQuery = "select distinct sp.full_name, sp.profile_picture, ru.total_marks, ru.marks_scored as marks_scored, md.description as test_type, ru.exam_date,cs.class_val, cs.section, ru.question_paper_ref "
    resultDetailQuery = resultDetailQuery + "from result_upload ru inner join student_profile sp on sp.student_id=ru.student_id "
    resultDetailQuery = resultDetailQuery + "inner join message_detail md on md.msg_id=ru.test_type "
    resultDetailQuery = resultDetailQuery + "and ru.upload_id='"+ str(upload_id) +"' inner join class_section cs on cs.class_sec_id=ru.class_sec_id order by marks_scored desc" 
    resultUploadRows = db.session.execute(text(resultDetailQuery)).fetchall()
    # paper = TestDetails.query.filter_by(test).first()
    runcount=0
    class_val_record = ""    
    section_record=""
    test_type_record=""
    exam_date_record=""
    question_paper_ref = ""
    for value in resultUploadRows:
        if runcount==0:        
            class_val_record = value.class_val
            section_record = value.section
            test_type_record=value.test_type
            exam_date_record= value.exam_date
            question_paper_ref = value.question_paper_ref
        runcount+1
    print('Upload Id:'+str(upload_id))
    print('Question Paper link:'+str(question_paper_ref))
    return render_template('_uploadHistoryDetail.html',resultUploadRows=resultUploadRows, class_val_record=class_val_record,section_record=section_record, test_type_record=test_type_record,exam_date_record=exam_date_record,question_paper_ref=question_paper_ref)

@app.route('/studentList/<class_val>/<section>/')
def studentList(class_val,section):
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    classSecRow = ClassSection.query.filter_by(class_val=class_val, section=section,school_id=teacher_id.school_id).first()
    students = StudentProfile.query.distinct().filter_by(class_sec_id=classSecRow.class_sec_id).all()
    studentArray = []

    

    for student in students:
        print('Student Name:'+str(student.full_name))
        studentObj = {}
        studentObj['student_id'] = student.student_id
        studentObj['student_name'] = student.full_name
        studentObj['class_value'] = classSecRow.class_val
        studentArray.append(studentObj)

    print(str(studentArray))
    return jsonify({'students' : studentArray})

@app.route('/questionBuilder',methods=['POST','GET'])
@login_required
def questionBuilder():
    form=QuestionBuilderQueryForm()
    print("Inside Question Builder")
    if request.method=='POST':
        if form.submit.data:
            question=QuestionDetails(class_val=str(request.form['class_val']),subject_id=int(request.form['subject_name']),question_description=request.form['question_desc'],
            reference_link=request.form['reference'],topic_id=int(request.form['topics']),question_type=form.question_type.data,suggested_weightage=int(request.form['weightage']),archive_status=str('N'))
            print(question)
            db.session.add(question)
            if form.question_type.data=='Subjective':
                question_id=db.session.query(QuestionDetails).filter_by(class_val=str(request.form['class_val']),topic_id=int(request.form['topics']),question_description=request.form['question_desc']).first()
                options=QuestionOptions(question_id=question_id.question_id,weightage=request.form['weightage'])
                print('Options Desc:'+str(options))
                db.session.add(options)
                db.session.commit()
                flash('Success')
                return render_template('questionBuilder.html',user_type_val=str(current_user.user_type))
            else:
                option_list=request.form.getlist('option_desc')
                question_id=db.session.query(QuestionDetails).filter_by(class_val=str(request.form['class_val']),topic_id=int(request.form['topics']),question_description=request.form['question_desc']).first()
                if request.form['correct']=='':
                    flash('Correct option not seleted !')
                    return render_template('questionBuilder.html',user_type_val=str(current_user.user_type))
                for i in range(len(option_list)):
                    if int(request.form['option'])==i+1:
                        correct='Y'
                        weightage=int(request.form['weightage'])
                    else:
                        weightage=0
                        correct='N'
                    if i+1==1:
                        option='A'
                    elif i+1==2:
                        option='B'
                    elif i+1==3:
                        option='C'
                    else:
                        option='D'
                        
                    options=QuestionOptions(option_desc=option_list[i],question_id=question.question_id,is_correct=correct,weightage=weightage,option=option)
                    print("Options in question Builder:"+str(options))
                    db.session.add(options)
                db.session.commit()
                flash('Success')
                return render_template('questionBuilder.html',user_type_val=str(current_user.user_type))
        else:
            csv_file=request.files['file-input']
            df1=pd.read_csv(csv_file)
            for index ,row in df1.iterrows():
                if row['Question Type']=='MCQ1':
                    print("Inside MCQ")
                    question=QuestionDetails(class_val=str(request.form['class_val']),subject_id=int(request.form['subject_name']),question_description=row['Question Description'],
                    topic_id=row['Topic Id'],question_type='MCQ1',reference_link=request.form['reference-url'+str(index+1)],archive_status=str('N'),suggested_weightage=row['Suggested Weightage'])
                    db.session.add(question)
                    question_id=db.session.query(QuestionDetails).filter_by(class_val=str(request.form['class_val']),topic_id=row['Topic Id'],question_description=row['Question Description']).first()
                    for i in range(1,5):
                        option_no=str(i)
                        option_name='Option'+option_no

                        print(row[option_name])
                        if row['CorrectAnswer']=='Option'+option_no:
                            correct='Y'
                            weightage=row['Suggested Weightage']
                        else:
                            correct='N'
                            weightage='0'
                        if i==1:
                                option_val='A'
                        elif i==2:
                                option_val='B'
                        elif i==3:
                                option_val='C'
                        else:
                            option_val='D'
                        print(row[option_name])
                        print(question_id.question_id)
                        print(correct)
                        print(option_val)
                        options=QuestionOptions(option_desc=row[option_name],question_id=question_id.question_id,is_correct=correct,option=option_val,weightage=int(weightage))
                        print(options)
                        db.session.add(options)
                else:
                    print("Inside Subjective")
                    question=QuestionDetails(class_val=str(request.form['class_val']),subject_id=int(request.form['subject_name']),question_description=row['Question Description'],
                    topic_id=row['Topic Id'],question_type='Subjective',reference_link=request.form['reference-url'+str(index+1)],archive_status=str('N'),suggested_weightage=row['Suggested Weightage'])
                    db.session.add(question)
            db.session.commit()
            flash('Successfully Uploaded !')
            return render_template('questionBuilder.html',user_type_val=str(current_user.user_type))
    return render_template('questionBuilder.html',user_type_val=str(current_user.user_type))



@app.route('/questionUpload',methods=['GET'])
def questionUpload():
    flag = False
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form=QuestionBuilderQueryForm()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).order_by(ClassSection.class_val).all()]
    form.subject_name.choices= ''
    # [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.topics.choices= ''
    # [(str(i['topic_id']), str(i['topic_name'])) for i in topics(1,54)]
    if request.method=='POST':
        print('Inside if question Upload')
        topic_list=Topic.query.filter_by(class_val=str(form.class_val.data),subject_id=str(form.subject_name.data),chapter_num=str(form.chapter_num.data)).all()
        return render_template('questionUpload.html',form=form, flag=flag,topic_list=topic_list)
    else:
        return render_template('questionUpload.html',form=form,flag=flag)

@app.route('/uploadMarks',methods=['GET'])
def uploadMarks():
    user = User.query.filter_by(username=current_user.username).first_or_404()    
    teacher= TeacherProfile.query.filter_by(user_id=user.id).first()     
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id=SchoolProfile.query.with_entities(SchoolProfile.board_id).filter_by(school_id=teacher_id.school_id).first()
    classValue = request.args.get('class_val')
    class_section = request.args.get('class_section')
    class_sec_id=ClassSection.query.filter_by(class_val=int(classValue),school_id=teacher_id.school_id,section=class_section).first()
    student_list=StudentProfile.query.filter_by(class_sec_id=class_sec_id.class_sec_id,school_id=teacher_id.school_id).all()
    paperUrl = request.args.get('paperUrl')
    subject_id = request.args.get('subject_id')
    marks = request.args.get('marks')
    testdate = request.args.get('testdate')
    Tmarks = request.args.get('Tmarks')
    testId = request.args.get('testId')
    test_type = request.args.get('test_type')
    marks = marks.split(",")
    count = 0
    now = datetime.now()
 
    print("now =", now)

    dt_string = now.strftime("%d/%m/%Y/%H:%M:%S")
    num = 1
    list_id = []
    for student_id in student_list:
        list_id.append(student_id.student_id)
    paper = ''
    print('Coming Paper Url :'+str(paperUrl))
    if testId!='':
        paper = TestDetails.query.filter_by(test_id=testId).first()
        print('Paper:'+str(paper.test_paper_link))
    else:
        testType = MessageDetails.query.filter_by(msg_id=test_type).first()
        testPaper = TestDetails(test_type=testType.description,total_marks=Tmarks,
        last_modified_date=datetime.today(),board_id=board_id.board_id,subject_id=subject_id,class_val=classValue,date_of_creation=datetime.today(),school_id=teacher_id.school_id,teacher_id=teacher_id.teacher_id,test_paper_link=paperUrl)
        db.session.add(testPaper)
    for marksSubjectWise in marks:
        if marksSubjectWise=='-1':
            marksSubjectWise=0
            is_present=MessageDetails.query.filter_by(description='Not Present').first()
        else:
            is_present=MessageDetails.query.filter_by(description='Present').first()
        #print('Marks:'+marksSubjectWise)
        upload_id=str(teacher_id.school_id)+str(class_sec_id.class_sec_id)+str(subject_id) + str(test_type) + dt_string
        upload_id=upload_id.replace('-','')
        print('Test Id:'+testId)
        
        if testId=='':
            print('If test id is null')
            print('Test Date:'+str(testdate))
            print('upload Date:'+str(datetime.today()))
            Marks=ResultUpload(school_id=teacher_id.school_id,student_id=list_id[count],
            exam_date=testdate,marks_scored=marksSubjectWise,class_sec_id=class_sec_id.class_sec_id,
            test_type=test_type,subject_id=subject_id,is_present=is_present.msg_id,total_marks=Tmarks,
            uploaded_by=teacher_id.teacher_id, upload_id=upload_id,last_modified_date=datetime.today(),question_paper_ref=paperUrl
            )
        else:
            print('If test id not null')
            print('Test Date:'+str(testdate))
            print('upload Date:'+str(datetime.today()))
            
            Marks=ResultUpload(school_id=teacher_id.school_id,student_id=list_id[count],
            exam_date=testdate,marks_scored=marksSubjectWise,class_sec_id=class_sec_id.class_sec_id,
            test_type=test_type,subject_id=subject_id,is_present=is_present.msg_id,total_marks=Tmarks,test_id=testId,
            uploaded_by=teacher_id.teacher_id, upload_id=upload_id,last_modified_date=datetime.today(),question_paper_ref=str(paper.test_paper_link)
            )
        
        db.session.add(Marks)
        count = count + 1
    db.session.execute(text('call sp_performance_detail_load()'))
    db.session.commit()
    flash('Login required !')
    print('Class_val:'+str(classValue)+'subject_id:'+str(subject_id)+'classSection:'+class_section+"testdate:"+testdate+"Total marks:"+Tmarks+"TestId:"+testId+"Test type:"+test_type)
    

    flash('Marks successfully uploaded')
    return render_template('resultUpload.html')


@app.route('/questionFile',methods=['GET']) 
def questionFile():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form=QuestionBuilderQueryForm()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().order_by(ClassSection.class_val).filter_by(school_id=teacher_id.school_id).all()]
    form.subject_name.choices= ''
    # [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.chapter_num.choices= ''
    form.topics.choices= ''
    # [(str(i['topic_id']), str(i['topic_name'])) for i in topics(1,54)]
    return render_template('questionFile.html',form=form)

@app.route('/addChapterTopics',methods=['GET','POST'])
def addChapterTopics():
    class_val = request.args.get('class_val')
    subject_id = request.args.get('subject_id')
    if current_user.is_anonymous:
        studentData = StudentProfile.query.filter_by(user_id=app.config['ANONYMOUS_USERID']).first()
        school_id = studentData.school_id
    else:
        if current_user.user_type==134 or current_user.user_type==234:
            studentData = StudentProfile.query.filter_by(user_id=current_user.id).first()
            school_id = studentData.school_id            
        else:
            teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
            school_id = teacherData.school_id

    query = "select distinct bd.book_name ,topic_name, chapter_name, td.topic_id, td.chapter_num from topic_tracker tt "
    query = query + "inner join topic_detail td on td.topic_id = tt.topic_id "
    query = query + "inner join book_details bd on td.book_id = bd.book_id "
    query = query + "where td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id)+"' and tt.school_id='"+str(school_id)+"' order by td.chapter_num "
    chapters = db.session.execute(text(query)).fetchall()
    chaptersArray = []
    i=1
    for chapter in chapters:
        if len(chapters)>1:
            book = chapter.book_name
            ch = chapter.topic_id
            if i==1:
                ch = str(ch)+"/"
            elif i==len(chapters):
                book = "/"+str(book)
            else:
                book = "/"+str(book)
                ch = str(ch)+"/"
            i=i+1
        chaptersArray.append(str(book)+"@"+str(chapter.topic_name)+"@"+str(chapter.chapter_name)+"@"+str(ch))
    
    if chaptersArray:
        return jsonify([chaptersArray])
    else:
        return ""


@app.route('/addClass',methods=['GET','POST'])
def addClass():
    class_val = request.args.get('class_val')

    ##########
    if current_user.is_anonymous:
        studentData = StudentProfile.query.filter_by(user_id=app.config['ANONYMOUS_USERID']).first()
        school_id = studentData.school_id
    else:
        if current_user.user_type==134 or current_user.user_type==234:
            studentData = StudentProfile.query.filter_by(user_id=current_user.id).first()
            school_id = studentData.school_id            
        else:
            teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
            school_id = teacherData.school_id
    ##########
    #teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #board_id = SchoolProfile.query.filter_by(school_id=school_id).first()
    subjects = BoardClassSubject.query.filter_by(class_val=str(class_val),school_id=school_id).all()
    subjectArray = []
    for subject in subjects:
        subject_name = "select description as subject_name from message_detail where msg_id='"+str(subject.subject_id)+"'"
        subject_name = db.session.execute(text(subject_name)).first()
        subjectArray.append(str(subject.subject_id)+":"+str(subject_name.subject_name))

    if subjectArray:
        return jsonify([subjectArray])
    else:
        return ""

@app.route('/topperList')
def topperList():
    classValue = request.args.get('class_val')
    # subject_id = request.args.get('subject_id')
    #test_type = request.args.get('test_type')
    # section_val = request.args.get('section_val')
    #test_date = request.args.get('test_date')
    #print('Class Value:'+classValue+"Subject Value:"+subject_id+"Test Type:"+test_type+"Section value:"+section_val+"Test date:"+test_date)
    user = User.query.filter_by(username=current_user.username).first_or_404()
    teacher= TeacherProfile.query.filter_by(user_id=user.id).first() 
    query = "select  * from fn_performance_leaderboard_detail('"+ str(teacher.school_id) +"') where class='"+classValue+"' order by marks desc"
    #print('Query topperList:'+query)
    leaderBoardData = db.session.execute(text(query)).fetchall()
    return render_template('_leaderBoardTable.html',leaderBoardData=leaderBoardData)

@app.route('/topperListForAll')
def topperListBySubject():
    classValue = request.args.get('class_val')
    subjectValue = request.args.get('subject_id')
    test_type = request.args.get('test_type')
    section_val = request.args.get('section_val')
    user = User.query.filter_by(username=current_user.username).first_or_404()
    teacher= TeacherProfile.query.filter_by(user_id=user.id).first() 
    subjectName = ''
    print('Subject id:'+subjectValue)
    if subjectValue!='All':
        subjectName = MessageDetails.query.filter_by(msg_id=subjectValue).first()
    query = "select *from public.fn_performance_leaderboard('"+ str(teacher.school_id) +"') where "
    print('Subject Value:'+subjectValue)
    if subjectValue=='All':
        sub = 'All'
    else:
        sub = subjectName.description
    if classValue!='':
        query = query + "class='"+classValue+"' and subjects='"+sub+"' and section='"+section_val+"' order by marks desc"
    else:
        query = query + "subjects='"+sub+"' and section='"+section_val+"' order by marks desc"
    print('Query topperList:'+query)
    leaderBoardData = db.session.execute(text(query)).fetchall()
    return render_template('_leaderBoardTable.html',leaderBoardData=leaderBoardData)

@app.route('/questionBuilder/<class_val>')
def subject_list(class_val):
    if class_val!='All':
        user_type_val = current_user.user_type
        teacher_id = ''
        if user_type_val==134:
            teacher_id = StudentProfile.query.filter_by(user_id=current_user.id).first()
        else:
            teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        board_id=SchoolProfile.query.with_entities(SchoolProfile.board_id).filter_by(school_id=teacher_id.school_id).first()
        subject_id=BoardClassSubject.query.with_entities(BoardClassSubject.subject_id).distinct().filter_by(class_val=str(class_val),board_id=board_id).all()
        subject_name_list=[]

        for id in subject_id:

            subject_name=MessageDetails.query.filter_by(msg_id=id).first()
            if subject_name in subject_name_list:
                continue
            subject_name_list.append(subject_name)
        subjectArray = []

        for subject in subject_name_list:
            subjectObj = {}
            subjectObj['subject_id'] = subject.msg_id
            subjectObj['subject_name'] = subject.description
            subjectArray.append(subjectObj)

        return jsonify({'subjects' : subjectArray})
    else:
        return "return"

# topic list generation dynamically
@app.route('/questionBuilder/<class_val>/<subject_id>')
def topic_list(class_val,subject_id):
    topic_list=Topic.query.filter_by(class_val=class_val,subject_id=subject_id).all()

    topicArray=[]

    for topic in topic_list:
        topicObj={}
        topicObj['topic_id']=topic.topic_id
        topicObj['topic_name']=topic.topic_name
        topicArray.append(topicObj)
    
    return jsonify({'topics':topicArray})

@app.route('/questionTopicPicker')
def questionTopicPicker():
    print('Inside topic picker')
    class_val = request.args.get('class_val')
    subject_id = request.args.get('subject_id')
    topic_list=Topic.query.filter_by(class_val=class_val,subject_id=subject_id).order_by(Topic.chapter_num).all()
    for topic in topic_list:
        print(topic.topic_id)
        print(topic.topic_name)
        print(topic.chapter_num)
    
    return render_template('_topics.html',topic_list=topic_list)

# @app.route('/coveredTopic',methods=['GET','POST'])
# def coveredTopic():
#     print('covered Topics')
#     class_v = request.args.get('class_val')
#     section = request.args.get('section')
#     query = "select *from topic_details where "
#     return render_template('_topicCovered.html')

@app.route('/questionChapterpicker/<class_val>/<subject_id>')
def chapter_list(class_val,subject_id):
    chapter_num = "select distinct chapter_num,chapter_name from topic_detail where class_val='"+class_val+"' and subject_id='"+subject_id+"' order by chapter_num"
    print(chapter_num)
    print('Inside chapterPicker')
    
    chapter_num_list = db.session.execute(text(chapter_num))
    chapter_num_array=[]
    for chapterno in chapter_num_list:
        chapterNo = {}
        chapterNo['chapter_num']=chapterno.chapter_num
        chapterNo['chapter_name']=chapterno.chapter_name
        chapter_num_array.append(chapterNo)
    return jsonify({'chapterNum':chapter_num_array})

@app.route('/addEvent', methods = ["GET","POST"])
@login_required
def addEvent():        
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form = addEventForm()
    if form.validate_on_submit():
        dataForEntry = EventDetail(event_name=form.eventName.data, event_duration=form.duration.data,event_date=form.eventDate.data,event_start=form.startDate.data,event_end=form.endDate.data,event_category=form.category.data,school_id=teacher_id.school_id, last_modified_date=datetime.today())                
        db.session.add(dataForEntry)
        db.session.commit()
        flash('Event Added!')
    return render_template('addEvent.html', form=form)

@app.route('/studentProfileOld')
@login_required
def studentProfileOld():
    return render_template('studentProfile.html')


@app.route('/allocateStudentToSponsor')
def allocateStudentToSponsor():
    student_id = request.args.get('student_id')
    sponsor_id = request.args.get('sponsor_id')
    sponsor_name = request.args.get('sponsor_name')
    amount = request.args.get('amount')

    studentData = StudentProfile.query.filter_by(student_id=student_id).first()
    studentData.sponsor_id = sponsor_id
    studentData.sponsor_name = sponsor_name
    studentData.sponsored_amount = amount
    studentData.sponsored_on = datetime.today()
    studentData.sponsored_status='Y'
    studentData.last_modified_date = datetime.today()
    db.session.commit()
    
    return jsonify(['0'])

@app.route('/indivStudentProfile')
@login_required
def indivStudentProfile():    
    student_id=request.args.get('student_id')
    flag = request.args.get('flag')
    #spnsor data check
    sponsor_id = request.args.get('sponsor_id')
    sponsor_name = request.args.get('sponsor_name')
    amount = request.args.get('amount')
    
    #New updated query
    studentProfileQuery = "select full_name, email, sponsored_status,sponsored_on,sponsor_name,phone,sp.school_id as school_id, dob, md.description as gender,class_val, section, "
    studentProfileQuery = studentProfileQuery + "roll_number,school_adm_number,profile_picture,student_id from student_profile sp inner join "
    studentProfileQuery = studentProfileQuery + "class_section cs on sp.class_sec_id= cs.class_sec_id and sp.student_id='"+str(student_id)+"'" 
    studentProfileQuery = studentProfileQuery + "inner join message_detail md on md.msg_id =sp.gender "
    studentProfileQuery = studentProfileQuery + "left join address_detail ad on ad.address_id=sp.address_id"

    studentProfileRow = db.session.execute(text(studentProfileQuery)).first()  
    
    #performanceData
    performanceQuery = "SELECT * from vw_leaderboard WHERE student_id = '"+str(student_id)+ "'"    

    perfRows = db.session.execute(text(performanceQuery)).fetchall()
    
    testCountQuery = "select count(*) as testcountval from result_upload where student_id='"+str(student_id)+ "'"

    testCount = db.session.execute(text(testCountQuery)).first()

    testResultQuery = "select exam_date, t2.description as test_type, test_id, t3.description as subject, marks_scored, total_marks "
    testResultQuery = testResultQuery+ "from result_upload t1 inner join message_detail t2 on t1.test_type=t2.msg_id "
    testResultQuery = testResultQuery + "inner join message_detail t3 on t3.msg_id=t1.subject_id "
    testResultQuery = testResultQuery + " where student_id=%s order by exam_date desc" % student_id
    #print(testResultQuery)
    testResultRows = db.session.execute(text(testResultQuery)).fetchall()
    
    #Remarks info
    studentRemarksQuery = "select student_id, tp.teacher_id, teacher_name, profile_picture, remark_desc, sr.last_modified_date as last_modified_date"
    studentRemarksQuery= studentRemarksQuery+ " from student_remarks sr inner join teacher_profile tp on sr.teacher_id=tp.teacher_id and student_id="+str(student_id) + " "
    studentRemarkRows = db.session.execute(text(studentRemarksQuery)).fetchall()
    #studentRemarkRows = StudentRemarks.query.filter_by(student_id=student_id).order_by(StudentRemarks.last_modified_date.desc()).limit(5).all()

    #Sponsor allocation
    urlForAllocationComplete = str(app.config['IMPACT_HOST']) + '/responseStudentAllocate'
    overallSum = 0
    overallPerfValue = 0

    for rows in perfRows:
        overallSum = overallSum + int(rows.student_score)
        #print(overallSum)
    try:
        overallPerfValue = round(overallSum/(len(perfRows)),2)    
    except:
        overallPerfValue=0    
    guardianRows = GuardianProfile.query.filter_by(student_id=student_id).all()
    qrRows = studentQROptions.query.filter_by(student_id=student_id).all()
    qrAPIURL = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="    
    qrArray=[]
    x = range(4)    

    #section for fetching surveys
    try:
        surveyRows = SurveyDetail.query.filter_by(school_id=studentProfileRow.school_id,is_archived='N').all()
    except:
        surveyRows=[]
        print('survey error')

    for n in x:               
        if studentProfileRow!=None and studentProfileRow!="":
            optionURL = qrAPIURL+str(student_id)+ '-'+str(studentProfileRow.roll_number)+'-'+ studentProfileRow.full_name.replace(" ", "%20")+'@'+string.ascii_uppercase[n]
        else:
            optionURL=""
        qrArray.append(optionURL)
        #print(optionURL)
    return render_template('_indivStudentProfile.html',surveyRows=surveyRows, studentRemarkRows=studentRemarkRows, urlForAllocationComplete=urlForAllocationComplete, studentProfileRow=studentProfileRow,guardianRows=guardianRows, 
        qrArray=qrArray,perfRows=perfRows,overallPerfValue=overallPerfValue,student_id=student_id,testCount=testCount,
        testResultRows = testResultRows,disconn=1, sponsor_name=sponsor_name, sponsor_id=sponsor_id,amount=amount,flag=flag)


@app.route('/addStudentRemarks',methods = ["GET","POST"])
def addStudentRemarks():
    remark_desc=request.form.get('remark')
    student_id = request.form.get('student_id')
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()        
    try:
        studentRemarkAdd = StudentRemarks(student_id=student_id, remark_desc=remark_desc, teacher_id=teacherDataRow.teacher_id,
            is_archived = 'N', last_modified_date = datetime.today())
        db.session.add(studentRemarkAdd)
        db.session.commit()
        return jsonify(['0'])
    except:
        return jsonify(['1'])

def classChecker(available_class):
    class_list = []
    for k in available_class:
        if k.class_val == '99':
            class_list.append((str('LKG')+"-"+str(k.section),str('LKG')+"-"+str(k.section)))
            print('inside available classes')
        elif k.class_val == '100':
            class_list.append((str('UKG')+"-"+str(k.section),str('UKG')+"-"+str(k.section)))
        else:
            class_list.append((str(k.class_val)+"-"+str(k.section),str(k.class_val)+"-"+str(k.section)))
    return class_list

@app.route('/studentProfile') 
@login_required
def studentProfile():    
    qstudent_id=request.args.get('student_id')
    #####Section for sponsor data fetch
    qsponsor_name = request.args.get('sponsor_name')
    qsponsor_id = request.args.get('sponsor_id')
    qamount = request.args.get('amount')
    studentDetails = StudentProfile.query.filter_by(user_id = current_user.id).first()

    if qstudent_id==None or qstudent_id=='':
        form=studentDirectoryForm()
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    

        available_class=ClassSection.query.with_entities(ClassSection.class_val,ClassSection.section).distinct().order_by(ClassSection.class_val).filter_by(school_id=teacher.school_id).all()
        available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher.school_id).all()    
        available_test_type=MessageDetails.query.filter_by(category='Test type').all()
        # available_student_list=StudentProfile.query.filter_by(school_id=teacher.school_id).all()
        available_student_list = "select student_id,full_name,profile_picture,class_val, section from student_profile sp inner join class_section cs on sp.class_sec_id = cs.class_sec_id where cs.school_id ='"+str(teacher.school_id)+"'"
        available_student_list = db.session.execute(available_student_list).fetchall()
        
        class_list = classChecker(available_class)
        
        section_list=[(i.section,i.section) for i in available_section]    
        test_type_list=[(i.msg_id,i.description) for i in available_test_type]
        # student_list=[(i.student_id,i.full_name) for i in available_student_list]

        #selectfield choices
        print(class_list)
        form.class_section.choices = class_list
        # form.section1.choices= ''
        # section_list    
        # form.test_type1.choices=test_type_list
        form.student_name.choices = ''
        flag = 1

        return render_template('studentProfileNew.html',form=form, sponsor_name=qsponsor_name, sponsor_id = qsponsor_id, amount = qamount,available_student_list=available_student_list,flag=flag,user_type_val=str(current_user.user_type),studentDetails=studentDetails)
    else:
        value=0
        flag = 0
        if current_user.user_type==72:
            value=1
        #print(qstudent_id)
        return render_template('studentProfileNew.html',qstudent_id=qstudent_id,disconn=value, sponsor_name=qsponsor_name, sponsor_id = qsponsor_id, amount = qamount,flag=flag,user_type_val=str(current_user.user_type),studentDetails=studentDetails)
        flag = 0       
        #print(qstudent_id)
        return render_template('studentProfileNew.html',qstudent_id=qstudent_id,disconn=disconn, sponsor_name=qsponsor_name, sponsor_id = qsponsor_id, amount = qamount,flag=flag, user_type_val=str(current_user.user_type),studentDetails=studentDetails)

#Addition of new section to conduct student surveys
@app.route('/studentSurveys')
def studentSurveys():
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    surveyDetailQuery = "select sd.survey_id, survey_name, question_count, count(ssr.student_id ) as student_responses, question_count, sd.last_modified_date "
    surveyDetailQuery = surveyDetailQuery+ "from survey_detail sd left join student_survey_response ssr on ssr.survey_id =sd.survey_id "
    surveyDetailQuery = surveyDetailQuery+" where sd.school_id ="+str(teacherRow.school_id)+ " and sd.is_archived='N' group by sd.survey_id,survey_name, question_count,question_count, sd.last_modified_date"
    surveyDetailRow = db.session.execute(surveyDetailQuery).fetchall()
    #surveyDetailRow = SurveyDetail.query.filter_by(school_id=teacherRow.school_id).all()
    
    return render_template('studentSurveys.html', surveyDetailRow=surveyDetailRow,user_type_val=str(current_user.user_type))

@app.route('/indivSurveyDetail/')
def indivSurveyDetail():
    survey_id = request.args.get('survey_id')
    survey_id = survey_id.split('_')[1]
    student_id = request.args.get('student_id')    
    studSurveyData = " select sq.sq_id as sq_id, question,sq.survey_id,survey_response_id , sp.student_id, answer from student_survey_response ssr "
    studSurveyData = studSurveyData  + " right join survey_questions sq on "
    studSurveyData = studSurveyData  +  " sq.survey_id =ssr.survey_id and "
    studSurveyData = studSurveyData  +  " sq.sq_id =ssr.sq_id and ssr.student_id ="+ str(student_id)
    studSurveyData = studSurveyData  +  " left join student_profile sp "
    studSurveyData = studSurveyData  +  " on sp.student_id =ssr.student_id "
    studSurveyData = studSurveyData  +  " where sq.survey_id =" + str(survey_id)
    surveyQuestions = db.session.execute(text(studSurveyData)).fetchall()
    return render_template('_indivSurveyDetail.html',surveyQuestions=surveyQuestions,student_id=student_id,survey_id=survey_id)

@app.route('/updateSurveyAnswer',methods=["GET","POST"])
def updateSurveyAnswer():
    sq_id_list = request.form.getlist('sq_id')
    survey_response_id_list = request.form.getlist('survey_response_id')
    answer_list = request.form.getlist('answer')
    survey_id = request.form.get('survey_id')
    student_id = request.form.get('student_id')
    for i in range(len(sq_id_list)):
        if survey_response_id_list[i]!='None':
            studentSurveyAnsUpdate = StudentSurveyResponse.query.filter_by(sq_id=sq_id_list[i], survey_response_id=survey_response_id_list[i]).first()
            studentSurveyAnsUpdate.answer = answer_list[i]
            surveyDetailRow = SurveyDetail.query.filter_by(survey_id=survey_id).first()            
        else:
            addNewSurveyResponse = StudentSurveyResponse(survey_id=survey_id, sq_id=sq_id_list[i], 
                student_id=student_id, answer=answer_list[i], last_modified_date=datetime.today())
            db.session.add(addNewSurveyResponse)
    db.session.commit()
    return jsonify(['0'])

@app.route('/addNewSurvey',methods=["GET","POST"])
def addNewSurvey():    
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    questions = request.form.getlist('questionInput')
    questionCount = len(questions)
    newSurveyRow = SurveyDetail(survey_name=request.form.get('surveyName'),teacher_id= teacherRow.teacher_id, 
        school_id=teacherRow.school_id, question_count = questionCount, is_archived='N',last_modified_date=datetime.today())
    db.session.add(newSurveyRow)
    db.session.commit()
    currentSurvey = SurveyDetail.query.filter_by(teacher_id=teacherRow.teacher_id).order_by(SurveyDetail.last_modified_date.desc()).first()
    for i in range(questionCount):
        newSurveyQuestion= SurveyQuestions(survey_id=currentSurvey.survey_id, question=questions[i], is_archived='N',last_modified_date=datetime.today())
        db.session.add(newSurveyQuestion)
    db.session.commit()
    return jsonify(['0'])


@app.route('/archiveSurvey')
def archiveSurvey():
    survey_id = request.args.get('survey_id')
    surveyData = SurveyDetail.query.filter_by(survey_id=survey_id).first()
    surveyData.is_archived='Y'
    db.session.commit()
    return jsonify(['0'])
#End of student survey section


#Start of inventory pages
@app.route('/inventoryManagement')
def inventoryManagement():
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print('#####################'+str(teacherRow))
    inventoryDetailRow = InventoryDetail.query.filter_by(school_id = teacherRow.school_id, is_archived='N').all()
    
    class_list=ClassSection.query.distinct().order_by(ClassSection.class_val).filter_by(school_id=teacherRow.school_id).all()    
    return render_template('inventoryManagement.html',inventoryDetailRow=inventoryDetailRow,class_list=class_list)

@app.route('/addInventoryItem', methods=["GET","POST"])
def addInventoryItem():
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    inventoryName = request.form.get('inventoryName')    
    newInventoryRow = InventoryDetail(inv_name=request.form.get('invName'),teacher_id= teacherRow.teacher_id, 
        inv_description = request.form.get('invDescription'), inv_category = 225, total_stock = request.form.get('totalStock'),
        item_rate = request.form.get('itemRate'), total_cost = request.form.get('totalCost'), stock_out=0, 
        school_id=teacherRow.school_id, is_archived='N',last_modified_date=datetime.today())
    db.session.add(newInventoryRow)
    db.session.commit()        
    addedInventory = InventoryDetail.query.filter_by(teacher_id = teacherRow.teacher_id, is_archived='N').order_by(InventoryDetail.last_modified_date.desc()).first()
    return jsonify([addedInventory.inv_id])


@app.route('/archiveInventory')
def archiveInventory():
    inv_id = request.args.get('inv_id')
    InventoryData = InventoryDetail.query.filter_by(inv_id=inv_id).first()
    InventoryData.is_archived='Y'
    db.session.commit()
    return jsonify(['0'])



@app.route('/studentInventoryAlloc')
def studentInventoryAlloc():
    class_sec_id = request.args.get('class_sec_id')
    inv_id = request.args.get('inv_id')
    inv_id = inv_id.split('_')[1]
    #studentInventoryQuery = "select sp.student_id , sp.full_name from student_profile sp  where sp.class_Sec_id="+ str(class_sec_id)    
    #studentInventoryData = db.session.execute(studentInventoryQuery).fetchall()    
    studentInventoryData = StudentProfile.query.filter_by(class_sec_id = str(class_sec_id)).all()
    return render_template('_studentInventoryAlloc.html',studentInventoryData=studentInventoryData)


@app.route('/updateInventoryAllocation')
def updateInventoryAllocation():
    ##last bit of changes required here to save inventory allocation
    return jsonify(['0'])
#End of inventory pages



@app.route('/performance')
def performance():
    df = pd.read_csv('data.csv').drop('Open', axis=1)
    chart_data = df.to_dict(orient='records')
    chart_data = json.dumps(chart_data, indent=2)
    data = {'chart_data': chart_data}
    return render_template("_performance.html", data=data)

@app.route('/help')
@login_required
def help():
    return render_template('help.html',user_type_val=str(current_user.user_type))


@app.route('/search')
def search():
    if not g.search_form.validate():
        return redirect(url_for('explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               app.config['POSTS_PER_PAGE'])
    next_url = url_for('search', q=g.search_form.q.data, page=page + 1) \
        if total > page * app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template(
        'search.html',
        title='Search',
        posts=posts,
        next_url=next_url,
        prev_url=prev_url)



@app.route('/checkout')
@login_required
def checkout():
    MERCHANT_KEY = "jS0QCS0O"
    key = ""
    SALT = "m4UzSP4umv"
    PAYU_BASE_URL = "https://sandboxsecure.payu.in/_payment"
    action = ''
    posted={}
    # Merchant Key and Salt provided y the PayU.
    for i in request.form:
    	posted[i]=request.form[i]
    hash_object = hashlib.sha256(b'randint(0,20)')
    txnid=hash_object.hexdigest()[0:20]
    hashh = ''
    posted['txnid']=txnid
    hashSequence = "key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10"
    posted['key']=key
    hash_string=''
    hashVarsSeq=hashSequence.split('|')
    for i in hashVarsSeq:
    	try:
    		hash_string+=str(posted[i])
    	except Exception:
    		hash_string+=''
    	hash_string+='|'
    hash_string+=SALT
    hash_string=hash_string.encode('utf-8')
    hashh=hashlib.sha512(hash_string).hexdigest().lower()
    action =PAYU_BASE_URL
    if(posted.get("key")!=None and posted.get("txnid")!=None and posted.get("productinfo")!=None and posted.get("firstname")!=None and posted.get("email")!=None):
    	return render_template('checkout.html',posted=posted,hashh=hashh,MERCHANT_KEY=MERCHANT_KEY,txnid=txnid,hash_string=hash_string,action='https://test.payu.in/_payment')
    else:
    	return render_template('checkout.html',posted=posted,hashh=hashh,MERCHANT_KEY=MERCHANT_KEY,txnid=txnid,hash_string=hash_string,action='.')   


@app.route('/paymentSuccess')
@login_required
def paymentSuccess():
    return render_template('paymentSuccess.html')

@app.route('/paymentFailure')
@login_required
def paymentFailure():
    return render_template('paymentFailure.html')


@app.route('/createSubscription',methods = ["GET","POST"])
@login_required
def createSubscription():
    form = createSubscriptionForm()
    if form.validate_on_submit():
        subcription_data=SubscriptionDetail(sub_name=form.sub_name.data,
            monthly_charge=form.monthly_charge.data,start_date=form.start_date.data,end_date=form.end_date.data,
            student_limit=form.student_limit.data,teacher_limit=form.teacher_limit.data,test_limit=form.test_limit.data, 
            sub_desc= form.sub_desc.data, last_modified_date= datetime.now(), archive_status='N', sub_duration_months=form.sub_duration.data)
        db.session.add(subcription_data)
        db.session.commit()
        flash('New subscription plan created.')
    return render_template('createSubscription.html',form=form)


# Routes for New Task

@app.route('/studentHomeWork')
@login_required
def studentHomeWork():
    user_type = current_user.user_type
    if user_type==134:
        user_id = User.query.filter_by(id=current_user.id).first()
        student_id = StudentProfile.query.filter_by(user_id=user_id.id).first()
        print('class_sec_id:'+str(student_id.class_sec_id))
        homeworkDetailQuery = "select sd.homework_id, homework_name, question_count, sd.last_modified_date,count(ssr.answer) as ans_count "
        homeworkDetailQuery = homeworkDetailQuery+ "from homework_detail sd left join student_homework_response ssr on ssr.homework_id =sd.homework_id "
        homeworkDetailQuery = homeworkDetailQuery+" where sd.school_id ="+str(student_id.school_id)+ " and sd.is_archived='N' and sd.class_sec_id='"+str(student_id.class_sec_id)+"' group by sd.homework_id,homework_name,question_count, sd.last_modified_date"
        homeworkDetailQuery = homeworkDetailQuery+" order by sd.last_modified_date desc"
        print(homeworkDetailQuery)
        homeworkData = db.session.execute(homeworkDetailQuery).fetchall()
        print('student_id:'+str(student_id.student_id))
        studentDetails = StudentProfile.query.filter_by(user_id=current_user.id).first()  
    return render_template('studentHomeWork.html',student_id=student_id.student_id,homeworkData=homeworkData,user_type_val=str(current_user.user_type), studentDetails=studentDetails)

@app.route('/HomeWork')
@login_required
def HomeWork():
    qclass_val = request.args.get('class_val')
    qsection=request.args.get('section')
    teacherRow = ''
    if current_user.user_type==134:
        teacherRow = StudentProfile.query.filter_by(user_id=current_user.id).first()        
    else:
        teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    classSections=ClassSection.query.filter_by(school_id=teacherRow.school_id).all()
    count = 0
    for section in classSections:
        print("Class Section:"+section.section)
            #this section is to load the page for the first class section if no query value has been provided
        if count==0:
            getClassVal = section.class_val
            getSection = section.section
            count+=1
    if qclass_val is None:
        qclass_val = getClassVal
        qsection = getSection
    
    class_sec_id = ClassSection.query.filter_by(school_id=teacherRow.school_id,class_val=qclass_val,section=qsection).first()
    homeworkDetailQuery = "select sd.homework_id, homework_name, question_count, count(ssr.student_id ) as student_responses, question_count, sd.last_modified_date "
    homeworkDetailQuery = homeworkDetailQuery+ "from homework_detail sd left join student_homework_response ssr on ssr.homework_id =sd.homework_id "
    homeworkDetailQuery = homeworkDetailQuery+" where sd.school_id ="+str(teacherRow.school_id)+ " and sd.is_archived='N' and sd.class_sec_id='"+str(class_sec_id.class_sec_id)+"' group by sd.homework_id,homework_name, question_count,question_count, sd.last_modified_date"
    homeworkDetailQuery = homeworkDetailQuery+" order by sd.last_modified_date desc"
    print(homeworkDetailQuery)
    homeworkDetailRow = db.session.execute(homeworkDetailQuery).fetchall()
    #surveyDetailRow = SurveyDetail.query.filter_by(school_id=teacherRow.school_id).all()
    distinctClasses = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacherRow.school_id)+" GROUP BY class_val order by s")).fetchall() 
    classSections=ClassSection.query.filter_by(school_id=teacherRow.school_id).all()
    return render_template('HomeWork.html', homeworkDetailRow=homeworkDetailRow,distinctClasses=distinctClasses,classSections=classSections,qclass_val=qclass_val,qsection=qsection,user_type_val=str(current_user.user_type))

@app.route('/homeworkReview')
@login_required
def homeworkReview():
    homework_id = request.args.get('homework_id')
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #homeworkRevData = "select *from fn_student_homework_status("+str(teacherRow.school_id)+","+str(homework_id)+")"
    homeworkRevData = "select sp.full_name as student_name, sp.student_id ,count(answer) as ans_count,hd.question_count as qcount,hd.homework_id from student_homework_response shr inner join student_profile sp "
    homeworkRevData = homeworkRevData + "on sp.student_id = shr.student_id inner join homework_detail hd on hd.homework_id = shr.homework_id "
    homeworkRevData = homeworkRevData + "where sp.school_id = '"+str(teacherRow.school_id)+"' and shr.homework_id='"+str(homework_id)+"' group by student_name , qcount, sp.student_id, hd.homework_id"
    homeworkRevData = db.session.execute(text(homeworkRevData)).fetchall()    
    homework_name = HomeWorkDetail.query.filter_by(homework_id=homework_id).first()
    classSections=ClassSection.query.filter_by(school_id=teacherRow.school_id,class_sec_id=homework_name.class_sec_id ).first()
    return render_template('homeworkReview.html',homeworkRevData=homeworkRevData,class_val=classSections.class_val,section=classSections.section,homework_name=homework_name.homework_name,homework_id=homework_id)

@app.route('/indivHomeworkReview',methods=['GET','POST'])
@login_required
def indivHomeworkReview():
    homework_id = request.args.get('homework_id') 
    student_id = request.args.get('student_id')
    #homework_id = HomeWorkDetail.query.filter_by(homework_id=homework_id).first()
    #reviewData = "select  hq.sq_id as sq_id, hq.question,hq.ref_type,hq.ref_url,shr.answer,shr.teacher_remark as teacher_remark from homework_questions hq left join student_homework_response shr "
    #reviewData = reviewData + "on hq.homework_id = shr.homework_id and hq.sq_id =shr.sq_id where hq.homework_id = '"+str(homework_id.homework_id)+"'"
    reviewData = "select  hq.sq_id as sq_id, hq.question,hq.ref_type,hq.ref_url,shr.answer,shr.teacher_remark as teacher_remark "
    #from homework_questions hq left join student_homework_response shr "
    #reviewData = reviewData + "on hq.homework_id = shr.homework_id and hq.sq_id =shr.sq_id where hq.homework_id = '"+str(homework_id.homework_id)+"'"
    reviewData = reviewData + " from homework_detail hd inner join homework_questions hq on "
    reviewData = reviewData + " hd.homework_id = hq.homework_id and hd.homework_id =" + str(homework_id)
    reviewData = reviewData + " left join student_homework_response shr on "
    reviewData = reviewData + " hq.sq_id =shr.sq_id and shr.student_id = " + str(student_id)
    reviewData = reviewData + " and shr.homework_response_id in (select min(homework_response_id )from student_homework_response shr "
    reviewData = reviewData + " where student_id ="+ str(student_id) +" and homework_id ="+ str(homework_id) +" group by sq_id ) "
    #print(reviewData)
    reviewData = db.session.execute(text(reviewData)).fetchall()    
    return render_template('_indivHomeWorkReview.html',reviewData=reviewData,student_id=student_id)

@app.route('/indivHomeworkDetail',methods=['GET','POST'])
@login_required
def indivHomeWorkDetail():
    homework_id = request.args.get('homework_id') 
    user_id = User.query.filter_by(id=current_user.id).first()
    student_id = StudentProfile.query.filter_by(user_id=user_id.id).first()
    homework_name = HomeWorkDetail.query.filter_by(homework_id=homework_id).first()
    #homeworkQuestions = HomeWorkQuestions.query.filter_by(homework_id=homework_id).all()

    #homeworkDataQQuery = " select distinct hq.sq_id as sq_id, question,hq.homework_id ,ref_type, ref_url, homework_response_id , sp.student_id, answer,teacher_remark from student_homework_response shr "
    #homeworkDataQQuery = homeworkDataQQuery + "right join homework_questions hq on "
    #homeworkDataQQuery = homeworkDataQQuery +  "hq.homework_id =shr.homework_id and "
    #homeworkDataQQuery = homeworkDataQQuery +  "hq.sq_id =shr.sq_id and shr.student_id = "+ str(student_id.student_id)
    #homeworkDataQQuery = homeworkDataQQuery +  " left join student_profile sp "
    #homeworkDataQQuery = homeworkDataQQuery +  "on sp.student_id =shr.student_id where hq.homework_id ="+ str(homework_id)
    #homeworkDataQQuery = homeworkDataQQuery +  " and homework_response_id in "
    #homeworkDataQQuery = homeworkDataQQuery +  " (select min(homework_response_id )from student_homework_response shr "
    #homeworkDataQQuery = homeworkDataQQuery +  " where student_id ="+ str(student_id.student_id) + " and homework_id ="+ str(homework_id) +" group by sq_id ) "
    homeworkDataQQuery = "select distinct hq.sq_id as sq_id, question,hq.homework_id ,ref_type, ref_url, homework_response_id , shr.student_id, answer,teacher_remark "
    homeworkDataQQuery = homeworkDataQQuery +  " from homework_detail hd inner join homework_questions hq "
    homeworkDataQQuery = homeworkDataQQuery +  " on hd.homework_id = hq.homework_id and hd.homework_id =" + str(homework_id)
    homeworkDataQQuery = homeworkDataQQuery +  " left join student_homework_response shr on "
    homeworkDataQQuery = homeworkDataQQuery +  " hq.sq_id =shr.sq_id and shr.student_id =" + str(student_id.student_id)
    homeworkDataQQuery = homeworkDataQQuery +  " and shr.homework_response_id in (select min(homework_response_id )from student_homework_response shr "
    homeworkDataQQuery = homeworkDataQQuery +  " where student_id ="+ str(student_id.student_id) +" and homework_id ="+ str(homework_id) +" group by sq_id )"

    print(homeworkDataQQuery)
    homeworkDataRows = db.session.execute(text(homeworkDataQQuery)).fetchall()
    homeworkAttach = db.session.execute(text("select attachment from homework_detail where homework_id='"+str(homework_id)+"'")).first()
    return render_template('_indivHomeWorkDetail.html',homeworkDataRows=homeworkDataRows,homework_name=homework_name,homework_id=homework_id,student_id=student_id,homeworkAttach=homeworkAttach)

@app.route('/addAnswerRemark',methods=["GET","POST"])
def addAnswerRemark():
    remark = request.form.getlist('remark')
    student_id = request.args.get('student_id')
    sq_id_list = request.form.getlist('sq_id')
    print('######'+str(len(sq_id_list) ))
    for i in range(len(sq_id_list)):
        remarkData = StudentHomeWorkResponse.query.filter_by(student_id=student_id,sq_id= sq_id_list[i]).first()  

        print('################################e   entered remark section')
        print(str(StudentHomeWorkResponse.query.filter_by(student_id=student_id,sq_id= sq_id_list[i])))
        if remarkData!=None:            
            remarkData.teacher_remark = remark[i]
    db.session.commit()
    return jsonify(['0'])

checkValue = ''
@app.route('/addHomeworkAnswer',methods=["GET","POST"])
def addHomeworkAnswer():
    sq_id_list = request.form.getlist('sq_id')
    answer_list = request.form.getlist('answer')
    homework_id = request.form.get('homework_id')
    print('add homework answer')
    user_id = User.query.filter_by(id=current_user.id).first()
    student_id = StudentProfile.query.filter_by(user_id=user_id.id).first()
    for i in range(len(sq_id_list)):
        checkStudentReponse = StudentHomeWorkResponse.query.filter_by(student_id=student_id.student_id,sq_id=sq_id_list[i]).first()
        if checkStudentReponse==None or checkStudentReponse=="":
            addNewHomeWorkResponse = StudentHomeWorkResponse(homework_id=homework_id, sq_id=sq_id_list[i], 
                student_id=student_id.student_id, answer=answer_list[i], last_modified_date=datetime.today())
            db.session.add(addNewHomeWorkResponse)
            print("Not present")
        else:
            return jsonify(['1'])
        #    checkStudentReponse.answer=answer_list[i]
        #    print("Already present")
    db.session.commit()
    return jsonify(['0'])


def get_yt_video_id(url):
    """Returns Video_ID extracting from the given url of Youtube
    
    Examples of URLs:
      Valid:
        'http://youtu.be/_lOT2p_FCvA',
        'www.youtube.com/watch?v=_lOT2p_FCvA&feature=feedu',
        'http://www.youtube.com/embed/_lOT2p_FCvA',
        'http://www.youtube.com/v/_lOT2p_FCvA?version=3&amp;hl=en_US',
        'https://www.youtube.com/watch?v=rTHlyTphWP0&index=6&list=PLjeDyYvG6-40qawYNR4juzvSOg-ezZ2a6',
        'youtube.com/watch?v=_lOT2p_FCvA',
      
      Invalid:
        'youtu.be/watch?v=_lOT2p_FCvA',
    """
    

    if url.startswith(('youtu', 'www')):
        url = 'http://' + url
    embeddingURL = "https://www.youtube.com/embed/"
    query = urlparse(url)
    
    if 'youtube' in query.hostname:
        if query.path == '/watch':
            return "96", embeddingURL + parse_qs(query.query)['v'][0]
        elif query.path.startswith(('/embed/', '/v/')):
            return "96",embeddingURL + query.path.split('/')[2]
    elif 'youtu.be' in query.hostname:
        return "96",embeddingURL + query.path[1:]
    else:
        return "97",url


def checkContentType(contentName):
    with urlopen(contentName) as response:
        info = response.info()
        contentTypeVal = info.get_content_type()
        splittedContentType = contentTypeVal.split('/')
        if splittedContentType[1]=='pdf' or splittedContentType[1]=='msword':
            return "99"
        elif splittedContentType[0]=='audio':
            return "97"
        elif splittedContentType[1]=='image':
            return "98"
        else:
            return "227"


@app.route('/addNewHomeWork',methods=["GET","POST"])
def addNewHomeWork():     
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    questions = request.form.getlist('questionInput')
    #contentType = request.form.getlist('contentType')
    contentName = request.form.getlist('contentName')
    homeworkContent = request.form.get('homeworkContent')
    print('inside addNew Homework')
    print(homeworkContent)
    for i in range(len(contentName)):
        print(contentName[i])
    #for i in range(len(contentType)):
    #    print('content type:'+str(contentType[i]))
    questionCount = len(questions)
    class_val = request.form.get('class')
    section = request.form.get('section')
    class_sec_id = ClassSection.query.filter_by(school_id=teacherRow.school_id,class_val=class_val,section=section).first()
    newHomeWorkRow = HomeWorkDetail(homework_name=request.form.get('homeworkName'),teacher_id= teacherRow.teacher_id, 
        school_id=teacherRow.school_id, question_count = questionCount, is_archived='N',class_sec_id=class_sec_id.class_sec_id,last_modified_date=datetime.today(),attachment=homeworkContent)
    db.session.add(newHomeWorkRow)
    db.session.commit()
    currentHomeWork = HomeWorkDetail.query.filter_by(teacher_id=teacherRow.teacher_id).order_by(HomeWorkDetail.last_modified_date.desc()).first()
        
    for i in range(questionCount):           
        if contentName[i] !='':               
            refType ,contentName[i] = get_yt_video_id(contentName[i])
            if refType!=96:
                refType= checkContentType(contentName[i])                
        else:
            refType=226
        newHomeWorkQuestion= HomeWorkQuestions(homework_id=currentHomeWork.homework_id, question=questions[i], is_archived='N',last_modified_date=datetime.today(),ref_type=int(refType),ref_url=contentName[i])
        db.session.add(newHomeWorkQuestion)
    db.session.commit()
    return jsonify(['0:'+ str(currentHomeWork.homework_id)])






@app.route('/archiveHomeWork')
def archiveHomeWork():
    homework_id = request.args.get('homework_id')
    homeworkData = HomeWorkDetail.query.filter_by(homework_id=homework_id).first()
    homeworkData.is_archived='Y'
    db.session.commit()
    return jsonify(['0'])


# End

# start
def conversion(num):
    strings = []
    for integ in num:
        strings.append(str(integ))
    a_string = "".join(strings)
    an_integer = int(a_string)
    return(an_integer)
      
def convList(left):
    res = [int(x) for x in str(left)]
    return res
def cal(num): 
    digit = len(num) 
    print(digit)
    powTen = pow(10, digit - 1) 
    res = []

    
    an_integer = conversion(num)
    res.append(num)
    for i in range(digit - 1):
        firstDigit = an_integer // powTen
        left = (an_integer * 10 + firstDigit - (firstDigit * powTen * 10))
        an_integer = left
        out = convList(an_integer)
        res.append(out)
    return res 

# Route for Schedule or Time Table
@app.route('/updateSchedule',methods=['POST','GET'])
def updateSchedule():
    slots = request.form.get('slots')
    class_value = request.args.get('class_val')
    print('No of slots:'+str(slots))
    print('Class_val:'+str(class_value))
    # start = request.form.getlist('start')
    # end = request.form.getlist('end')
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    sections = ClassSection.query.filter_by(school_id=teacher.school_id,class_val=class_value).all()
    batches = len(sections)
    slotTime = []
    # for (s,e) in itertools.zip_longest(start,end):
    #     slotTime.append(s+'-'+e)
    print('inside schedule')
    # nDays = request.form.get('nDays')
    noTeachers = request.form.get('noTeachers')
    nameTeacher = request.form.getlist('nameTeacher')
    nameSubject = request.form.getlist('nameSubject')
    subject = request.form.getlist('subject')
    time = request.form.getlist('time')
    day = request.form.getlist('day')
        # batches = request.form.get('batches')
    print('No of Days:'+str(len(day)))
    nDays = len(day)
    totalTime = 0
    for ti in time:
            # print('Time:'+str(ti))
        if ti:
            totalTime = totalTime + int(ti)
    totalSlots = int(nDays)*int(slots)
        # print('Total slots:'+str(totalSlots))
        # print('Total Time:'+str(totalTime))
    perSlots = []
    for s in range(int(slots)):
                
        perSlots.append(s+1)
    slotsoutput = cal(perSlots)

        # for slot in range(len(slotsoutput)):
            # print('slot'+str(slot))
            # print(slotsoutput[slot])
    finalSlot = []
    indexSlot = []
        # print('outside while loop')
    p=0
        # print('length of slots output')
        # print(len(slotsoutput))
    while p<len(slotsoutput):
            # print('inside while loop')
        r = randint(0,len(slotsoutput)-1)
        if r not in indexSlot:
            p=p+1
            indexSlot.append(r)
        # print(indexSlot)
    for index in indexSlot:
        finalSlot.append(slotsoutput[index])
        # print(finalSlot)
        

        # print('slot output print')
        # print(slotsoutput)
    t=1
    z=0
    class_sec_ids = ClassSection.query.filter_by(class_val = class_value, school_id = teacher.school_id).all() 
    for class_sec_id in class_sec_ids:
        updateTable = "update schedule_detail set is_archived = 'Y' where class_sec_id='"+str(class_sec_id.class_sec_id)+"' and school_id='"+str(teacher.school_id)+"'"
        updateTable = db.session.execute(text(updateTable))
    for l in subject:
            # print(l)
        if(l):
            z=z+1
        # print('No of Subjects:'+str(z))
    if totalSlots>=totalTime:

        for arr1 in finalSlot:
            if t<=int(batches):    
                            
                    
                for i in range(0,z):

                    for j in range(0,int(time[i])):
                            
                        class_sec_id = "select class_sec_id from class_section where class_val='"+str(class_value)+"' and section='"+chr(ord('@')+t)+"' and school_id='"+str(teacher.school_id)+"'"
                            
                        class_sec_id = db.session.execute(text(class_sec_id)).first()
                        subject_id = "select msg_id from message_detail where description='"+str(subject[i])+"'"
                        subject_id = db.session.execute(text(subject_id)).first()
                        teacher_id = TeacherSubjectClass.query.filter_by(class_sec_id=class_sec_id.class_sec_id,subject_id=subject_id.msg_id,school_id=teacher.school_id,is_archived='N').first()
                           
                        if teacher_id:
                            insertData = ScheduleDetail(class_sec_id=class_sec_id.class_sec_id ,school_id=teacher.school_id, days_name=day[j] ,subject_id=subject_id.msg_id , teacher_id=teacher_id.teacher_id ,slot_no=arr1[i] , last_modified_date=dt.datetime.now(), is_archived= 'N')
                        else:
                            insertData = ScheduleDetail(class_sec_id=class_sec_id.class_sec_id ,school_id=teacher.school_id, days_name=day[j] ,subject_id=subject_id.msg_id  ,slot_no=arr1[i] , last_modified_date=dt.datetime.now(), is_archived= 'N')
                        db.session.add(insertData)
            t=t+1
    else:
        return jsonify(['1'])
    db.session.commit()
    print('Data is Submitted') 
    return jsonify(['0'])

@app.route('/schedule')
def schedule():
    # slots = request.form.get('slots')
    # print('inside schedule function')
    # print(slots)
    qclass_val = request.args.get("class_val")
    qsection = request.args.get("section")
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    classSections=ClassSection.query.filter_by(school_id=teacher.school_id).all()
    available_class_section = "select distinct class_val,section from class_section where school_id='"+str(teacher.school_id)+"'"
    available_class_section = db.session.execute(text(available_class_section)).fetchall()
    distinctClasses = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacher.school_id)+" GROUP BY class_val order by s")).fetchall()  
    if qclass_val==None and qsection == None:
        qclass_val = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacher.school_id)+" GROUP BY class_val order by s")).first()  
        qclass_val = qclass_val.class_val
        qsection = ClassSection.query.filter_by(school_id=teacher.school_id).first()
        qsection = qsection.section
    return render_template('schedule.html',classsections=classSections,distinctClasses=distinctClasses,available_class_section=available_class_section,qclass_val=qclass_val,qsection=qsection)
    
@app.route('/fetchTimeTable',methods=['GET','POST'])
def fetchTimeTable():
    class_val = request.args.get('class_value')
    section = request.args.get('section')
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print(class_val)
    print(section)
    print(teacher.school_id)
    class_section = ClassSection.query.filter_by(class_val=str(class_val),section = section, school_id= teacher.school_id).first()

    query = "select *from fn_time_table("+str(teacher.school_id)+","+str(class_section.class_sec_id)+")"
    print(query)
    timeTableData = db.session.execute(text(query)).fetchall()
    print(timeTableData)
    for data in timeTableData:
        print(data)
    fetchTeacher = "select *from fn_teacher_allocation("+str(teacher.school_id)+","+str(class_section.class_sec_id)+")"
    print(fetchTeacher)
    fetchTeacher = db.session.execute(text(fetchTeacher)).fetchall()
    print(fetchTeacher)
    return render_template('_timeTable.html',timeTableData=timeTableData,fetchTeacher=fetchTeacher)

@app.route('/downloadTimeTable',methods=['GET','POST'])
def downloadTimeTable():
    print('inside download time table')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    # fetchTeacher = "select *from fn_teacher_allocation("+str(teacher_id.school_id)+","+str(class_section.class_sec_id)+")"
    # print(fetchTeacher)
    # fetchTeacher = db.session.execute(text(fetchTeacher)).fetchall()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    class_sec_ids = ClassSection.query.filter_by(school_id=teacher_id.school_id).all()
    filepath = 'static/images/'+str(teacher_id.school_id)+str(dt.datetime.now())+'TimeTable.csv'
    with open(filepath, 'w', newline='') as file:
        
        print('file')
        
        file.write('Introduction \n')
        writer = csv.writer(file)
        for class_sec_id in class_sec_ids:
            fetchTeacher = "select *from fn_teacher_allocation("+str(teacher_id.school_id)+","+str(class_sec_id.class_sec_id)+")"
            print(fetchTeacher)
            
            fetchTeacher = db.session.execute(text(fetchTeacher)).fetchall()
            writer.writerow(["Subject Name", "Teacher Name"])
            # writer.writerow(["", "Name", "Contribution"])
            for teacher in fetchTeacher:
                print(teacher.subject_name)
                print(teacher.teacher_name)
                writer.writerow([teacher.subject_name,teacher.teacher_name])
                # os.remove(filepath)
                print('File path')
                print(filepath)
            query = "select *from fn_time_table("+str(teacher_id.school_id)+","+str(class_sec_id.class_sec_id)+")"
            print(query)
            timeTableData = db.session.execute(text(query)).fetchall()
            writer.writerow(["Periods", "Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"])
            
            for table in timeTableData:
                writer.writerow([table.period_no,table.monday,table.tuesday,table.wednesday,table.thursday,table.friday,table.saturday])
            writer.writerow(["","","","","","",""])
    return jsonify([filepath])

@app.route('/allSubjects',methods=['GET','POST'])
def allSubjects():
    print('inside all Subjects')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    school_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    class_val = request.args.get('class_value') 
    print(class_val)
    print(teacher_id.school_id)
    subjects = BoardClassSubject.query.filter_by(class_val = str(class_val),school_id=teacher_id.school_id,is_archived='N').all()
    subjectList = []
    for subject in subjects:
        subject_name = "select description from message_detail where msg_id='"+str(subject.subject_id)+"'"
        subject_name = db.session.execute(text(subject_name)).first()
        
        subjectList.append(str(subject_name.description))
    return jsonify([subjectList])

#End
#Start

@app.route('/addTeacherClassSubject',methods=['GET','POST'])
def addTeacherClassSubject():
    subjectNames = request.get_json()
    print('Inside add Teacher class Subject')
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = request.args.get('class_sec_id')
    teacher_id = request.args.get('teacher_id')
    remdata = "update teacher_subject_class set is_archived = 'Y' where class_sec_id='"+str(class_sec_id)+"' and school_id = '"+str(teacher.school_id)+"'  and teacher_id = '"+str(teacher_id)+"'"
    remdata = db.session.execute(text(remdata))
    for subjects in subjectNames:
        print('inside for')
        print(subjects)
        subject_id = "select msg_id from message_detail where description='"+str(subjects)+"'"
        subject_id = db.session.execute(text(subject_id)).first()
        
        
        addTeacherClass = TeacherSubjectClass(teacher_id=teacher_id,class_sec_id=class_sec_id,subject_id=subject_id.msg_id,is_archived='N',school_id=teacher.school_id,last_modified_date=dt.datetime.now())
        db.session.add(addTeacherClass)
        db.session.commit()
    return ""

@app.route('/loadSubject',methods=['GET','POST'])
def loadSubject():
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    teacher_id = request.args.get('teacher_id')
    class_sec_id = request.args.get('class_sec_id')
    class_val = ClassSection.query.filter_by(class_sec_id=class_sec_id,school_id=teacher.school_id).first()
    allSubjects = "select distinct subject_id from board_class_subject bcs where school_id = '"+str(teacher.school_id)+"' and class_val = '"+str(class_val.class_val)+"' and is_archived = 'N' and subject_id "
    allSubjects = allSubjects + "not in (select distinct subject_id from teacher_subject_class where school_id= '"+str(teacher.school_id)+"' and is_archived = 'N' and class_sec_id = '"+str(class_sec_id)+"' and teacher_id='"+str(teacher_id)+"')"
    allSubjects = db.session.execute(text(allSubjects)).fetchall()

    selSubjects = "select distinct subject_id from teacher_subject_class where school_id= '"+str(teacher.school_id)+"' and is_archived = 'N' and class_sec_id = '"+str(class_sec_id)+"' and teacher_id='"+str(teacher_id)+"'"
    selSubjects = db.session.execute(text(selSubjects)).fetchall()
    selArray = []
    for subjects in allSubjects:
        subject_name = "select description from message_detail where msg_id='"+str(subjects.subject_id)+"'"
        subject_name = db.session.execute(text(subject_name)).first()
        selArray.append(str(subject_name.description)+':'+str('false'))
    for sub in selSubjects:
        subject_name = "select description from message_detail where msg_id='"+str(sub.subject_id)+"'"
        subject_name = db.session.execute(text(subject_name)).first()
        selArray.append(str(subject_name.description)+':'+str('true'))
    if selArray:
        return jsonify([selArray])
    else:
        return ""

@app.route('/loadClasses',methods=['GET','POST'])
def loadClasses():
    teacher_id = request.args.get('teacher_id')
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_val = ClassSection.query.filter_by(school_id=teacher.school_id).all()
    classes = []
    print(teacher.school_id)
    for clas in class_val: 
        teacher = TeacherSubjectClass.query.filter_by(teacher_id=teacher_id,class_sec_id=clas.class_sec_id).first()
        if teacher:
            classes.append(str(clas.class_val)+':'+str(clas.class_sec_id)+':'+str(clas.section)+':'+str('true'))
        else:
            classes.append(str(clas.class_val)+':'+str(clas.class_sec_id)+':'+str(clas.section)+':'+str('false'))
        
    return jsonify([classes])

@app.route('/teacherAllocation',methods=['GET','POST'])
def teacherAllocation():
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_ids = ClassSection.query.filter_by(school_id=teacher_id.school_id).all()
    fetchTeacherNameQuery = "select distinct tp.teacher_name,tp.teacher_id from teacher_profile tp "
    fetchTeacherNameQuery = fetchTeacherNameQuery + "left join teacher_subject_class tsc on tsc.teacher_id=tp.teacher_id "
    fetchTeacherNameQuery = fetchTeacherNameQuery + "where tp.school_id='"+str(teacher_id.school_id)+"'"
    print(fetchTeacherNameQuery)
    teacherNames = db.session.execute(text(fetchTeacherNameQuery)).fetchall()
    print('Inside teacher class subject allocation')
    return render_template('_teacherAllocation.html',teacherNames=teacherNames,class_sec_ids=class_sec_ids)

#End

# Code for course 
@app.route('/')
# End


@app.route('/subscriptionPlans')
def subscriptionPlans():
    subscriptionRow = SubscriptionDetail.query.filter_by(archive_status='N').order_by(SubscriptionDetail.sub_duration_months).all()    
    distinctSubsQuery = db.session.execute(text("select distinct group_name, sub_desc, student_limit, teacher_limit, test_limit from subscription_detail where archive_status='N' order by student_limit ")).fetchall()
    return render_template('/subscriptionPlans.html', subscriptionRow=subscriptionRow, distinctSubsQuery=distinctSubsQuery)

def format_currency(value):
    return "₹{:,.2f}".format(value)

if __name__=="__main__":
    app.debug=True  
    #app.use_reloader=False  
    app.jinja_env.filters['zip'] = zip
    #app.run(host=os.getenv('IP', '127.0.0.1'), 
    #        port=int(os.getenv('PORT', 8000)))
    app.run(host=os.getenv('IP', '0.0.0.0'),         
        port=int(os.getenv('PORT', 8000))
        # ssl_context='adhoc'
        )
    #app.run()
