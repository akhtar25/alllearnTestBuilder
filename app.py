from flask import Flask, Markup, render_template, request, flash, redirect, url_for, Response,session,jsonify
from send_email import welcome_email, send_password_reset_email, user_access_request_email,user_school_access_request_email, access_granted_email, new_school_reg_email, performance_report_email,test_report_email,notificationEmail
from send_email import new_teacher_invitation,new_applicant_for_job, application_processed, job_posted_email, send_notification_email
from applicationDB import *
#from qrReader import *
from threading import Thread
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
#import barCode
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
import requests as rq
import urllib
#import matplotlib.pyplot as plt
from flask_talisman import Talisman, ALLOW_FROM
from flask_api import FlaskAPI, status, exceptions
from calendar import monthrange
import calendar
from urllib.parse import quote,urlparse, parse_qs
from google.oauth2 import id_token
from google.auth.transport import requests
from algoliasearch.search_client import SearchClient
import base64
import hmac
import hashlib
import json
# from moviepy.editor import *


app=FlaskAPI(__name__)

talisman = Talisman(app, content_security_policy=None)


client = SearchClient.create('RVHAVJXK1B', '58e63c83b4126c21f2e994f1d4e89439')
index = client.init_index('prd_course')

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
            user = User(username=idinfo["email"], email=idinfo["email"], user_type='253', access_status='145', 
                first_name = idinfo["given_name"],last_name= idinfo["family_name"], last_modified_date = datetime.today(),
                user_avatar = idinfo["picture"],school_id=1, login_type=244)
            #user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            #flash('Congratulations! You\'re now a registered user!')
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
    #print('#######this is teacher profile val '+ str(teacherProfile.teacher_id))
    #print('#######this is current user '+ str(current_user.id))
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

@app.route('/inReviewSchool')
def inReviewSchool():
    print('In review school:'+str(current_user.user_type))
    return render_template('inReviewSchool.html', disconn = 1)

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
    indic='DashBoard'
    return render_template('schoolProfile.html',indic=indic,title='School Profile', teacherRow=teacherRow, registeredStudentCount=registeredStudentCount, registeredTeacherCount=registeredTeacherCount,allTeachers=allTeachers,classSectionRows=classSectionRows, schoolProfileRow=schoolProfileRow,addressRow=addressRow,subscriptionRow=subscriptionRow,disconn=value,user_type_val=str(current_user.user_type),studentDetails=studentDetails)




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

        school=SchoolProfile(school_name=form.schoolName.data,board_id=board_id.msg_id,address_id=address_id.address_id,registered_date=dt.datetime.now(), last_modified_date = dt.datetime.now(), sub_id=selected_sub_id,how_to_reach=form.how_to_reach.data,is_verified='N')
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
        schoolData = SchoolProfile.query.filter_by(school_admin=newTeacherRow.teacher_id).first()
        print('current user id:'+str(current_user.id))
        print('schoolData:'+str(schoolData))
        print('schoolData.is_verified'+str(schoolData.is_verified))
        if schoolData:
            print('if schoolData exist')
            if schoolData.is_verified == 'N':
                print('if schoolData.is_verified is N')
                userTableDetails = User.query.filter_by(id=current_user.id).first()
                adminEmail=db.session.execute(text("select t2.email,t2.teacher_name,t1.school_name,t3.username from school_profile t1 inner join teacher_profile t2 on t1.school_admin=t2.teacher_id inner join public.user t3 on t2.email=t3.email where t1.school_id='"+str(schoolData.school_id)+"'")).first()
                user_school_access_request_email(adminEmail.email,adminEmail.teacher_name, adminEmail.school_name, userTableDetails.first_name+ ''+userTableDetails.last_name, adminEmail.username, userTableDetails.user_type)
                return redirect(url_for('inReviewSchool'))
        
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
        indic='DashBoard'
        return render_template('promoteStudent.html',indic=indic,title='Promote Student',form=form,studentList=studentList,user_type_val=str(current_user.user_type))
    else:
        indic='DashBoard'
        return render_template('promoteStudent.html',indic=indic,title='Promote Student',form=form,studentList=studentList,user_type_val=str(current_user.user_type))
      
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
        indic='DashBoard'         
        return render_template('teacherDirectory.html',indic=indic,form=form, payrollReportData=payrollReportData,allTeachers=allTeachers,user_type_val=str(current_user.user_type))

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
    feeStatusDataQuery = "select sp.student_id as student_id, sp.profile_picture as profile_picture, sp.full_name as student_name,sp.roll_number, fd.fee_amount as fee_amount,fd.fee_paid_amount as paid_amount, fd.outstanding_amount as rem_amount, fd.paid_status as paid_status,fd.delay_reason"
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
                indic='DashBoard'
                return render_template('studentRegistration.html',indic=indic,title='Student Registration',studentId=student_id,user_type_val=str(current_user.user_type))


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
                class_val=str(form.class_val.data), section=form.section.data, is_current='Y',last_modified_date=datetime.today()) 
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
                indic='DashBoard'
                return render_template('studentRegistration.html',indic=indic,title='Student Registration',user_type_val=str(current_user.user_type))

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
            indic='DashBoard'
            return render_template('studentRegistration.html',indic=indic,user_type_val=str(current_user.user_type))
    if studId!='':
        print('inside if Student Id:'+str(studId))
        indic='DashBoard'
        return render_template('studentRegistration.html',indic=indic,studentId=studId,user_type_val=str(current_user.user_type))
    indic='DashBoard'
    return render_template('studentRegistration.html',indic=indic,user_type_val=str(current_user.user_type))


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

@app.route('/',methods=["GET","POST"])
@app.route('/index')
@app.route('/dashboard')
@login_required 
def index():
    #print('Inside index')
    #print("########This is the request url: "+str(request.url))
    print('current_user.id:'+str(current_user.id))
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    schoolData = ''
    if teacherData:
        schoolData = SchoolProfile.query.filter_by(school_admin=teacherData.teacher_id).first()
    if schoolData:
        if schoolData.is_verified == 'N':
            return redirect(url_for('inReviewSchool'))
    checkUser = User.query.filter_by(id=current_user.id).first()
    if checkUser:
        if checkUser.access_status == 143:
            return redirect(url_for('disconnectedAccount'))
    user = User.query.filter_by(username=current_user.username).first_or_404()        
    school_name_val = schoolNameVal()
    #print('User Type Value:'+str(user.user_type))
    teacher_id = TeacherProfile.query.filter_by(user_id=user.id).first() 
    
    school_id = SchoolProfile.query.filter_by(school_name=school_name_val).first()
    print('school_name_val:',school_name_val)
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
            return render_template('syllabus.html',title='Syllabus',generalBoard=generalBoard,boardRowsId = boardRows.msg_id , boardRows=boardRows.description,subjectValues=subjectValues,school_name=school_id.school_name,classValues=classValues,classValuesGeneral=classValuesGeneral,bookName=bookName,chapterNum=chapterNum,topicId=topicId,fromSchoolRegistration=fromSchoolRegistration)
    #if user.user_type==135:
    #    return redirect(url_for('admin'))
    if user.user_type==234:
    #or ("prep.alllearn" in str(request.url)) or ("alllearnprep" in str(request.url))
        return redirect(url_for('practiceTest'))
    if user.user_type==253:
        return redirect(url_for('courseHome'))
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
        return redirect(url_for('studentDashboard'))
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
    indic='DashBoard'
    return render_template('postJob.html',indic=indic,title='Post Job',form=form,classSecCheckVal=classSecCheck())


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

# start live class section

@app.route('/liveClass', methods=['GET','POST'])
@login_required
def liveClass():    
    form = AddLiveClassForm()
    user_id = request.args.get('user_id')
    student = ''
    studentDetails = ''
    print('inside live class route')
    if user_id:
        student = StudentProfile.query.filter_by(user_id=user_id).first()
        allLiveClassQuery = "(select t1.class_sec_id, t2.class_val, t2.section "
        allLiveClassQuery = allLiveClassQuery + ", t1.subject_id, t3.description as subject, t1.topic_id, t4.topic_name, start_time,end_time, status, teacher_name, "
        allLiveClassQuery = allLiveClassQuery + " conf_link, t1.school_id "
        allLiveClassQuery = allLiveClassQuery + " from live_class t1 "
        allLiveClassQuery = allLiveClassQuery+ " inner join class_section t2 on t1.class_sec_id = t2.class_sec_id "
        allLiveClassQuery= allLiveClassQuery + " inner join message_detail t3 on t1.subject_id = t3.msg_id "
        allLiveClassQuery= allLiveClassQuery + " inner join topic_detail t4 on t1.topic_id = t4.topic_id where t1.school_id= " +str(student.school_id) + " and t1.class_sec_id= "+str(student.class_sec_id) 
        allLiveClassQuery= allLiveClassQuery + " and end_time > now() order by end_time desc)"  
        allLiveClassQuery= allLiveClassQuery + " union "
        allLiveClassQuery = allLiveClassQuery + "(select t1.class_sec_id, t2.class_val, t2.section "
        allLiveClassQuery = allLiveClassQuery + ", t1.subject_id, t3.description as subject, t1.topic_id, t4.topic_name, start_time,end_time, status, teacher_name, "
        allLiveClassQuery = allLiveClassQuery + " conf_link, t1.school_id "
        allLiveClassQuery = allLiveClassQuery + " from live_class t1 "
        allLiveClassQuery = allLiveClassQuery+ " inner join class_section t2 on t1.class_sec_id = t2.class_sec_id "
        allLiveClassQuery= allLiveClassQuery + " inner join message_detail t3 on t1.subject_id = t3.msg_id "
        allLiveClassQuery= allLiveClassQuery + " inner join topic_detail t4 on t1.topic_id = t4.topic_id where t1.is_private= 'N' and t1.school_id<> " +str(student.school_id) + " and t1.class_sec_id= "+str(student.class_sec_id) 
        allLiveClassQuery= allLiveClassQuery + " and end_time > now() order by end_time desc)"
        print('Query for live class:'+str(allLiveClassQuery))
        try:
            allLiveClasses = db.session.execute(text(allLiveClassQuery)).fetchall()
            print('##########Data:'+str(allLiveClasses))
        except:
            allLiveClasses = "" 
        indic='DashBoard'   
        return render_template('liveClass.html',indic=indic,title='Live Classes',allLiveClasses=allLiveClasses,form=form,current_time=datetime.now(),studentDetails=studentDetails)      
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
    allLiveClassQuery= allLiveClassQuery + " union "
    allLiveClassQuery = "select t1.class_sec_id, t2.class_val, t2.section "
    allLiveClassQuery = allLiveClassQuery + ", t1.subject_id, t3.description as subject, t1.topic_id, t4.topic_name, start_time,end_time, status, teacher_name, "
    allLiveClassQuery = allLiveClassQuery + " conf_link, t1.school_id "
    allLiveClassQuery = allLiveClassQuery + " from live_class t1 "
    allLiveClassQuery = allLiveClassQuery+ " inner join class_section t2 on t1.class_sec_id = t2.class_sec_id "
    allLiveClassQuery= allLiveClassQuery + " inner join message_detail t3 on t1.subject_id = t3.msg_id "
    allLiveClassQuery= allLiveClassQuery + " inner join topic_detail t4 on t1.topic_id = t4.topic_id where t1.school_id<> " +str(school_id)+" and is_private='N'" 
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
    indic='DashBoard'              
    return render_template('liveClass.html',indic=indic,title='Live Classes',allLiveClasses=allLiveClasses,form=form,user_type_val=str(current_user.user_type),current_time=datetime.now(),studentDetails=studentDetails)    

#end of live class section


#####New section for open class modules
@app.route('/updateSearchIndex/<task>')
@login_required
def updateSearchIndex(task, fromPage="default"):
    #queryTest = "select *from topic_detail where topic_name is not null fetch first 100 rows only"
    indexQuery = "select cd.course_id as \"objectID\", cd.course_id, cd.course_name, cd.description,average_rating , cd.image_url, "
    indexQuery = indexQuery + " tp.teacher_name,ideal_for, string_agg(topic_name::text, ', ') as topics, text(cd.last_modified_date) as last_modified_date"
    indexQuery = indexQuery + " from course_detail cd "
    indexQuery = indexQuery + " inner join course_topics ct"
    indexQuery = indexQuery + " on ct.course_id =cd.course_id "
    indexQuery = indexQuery + " inner join topic_detail td"
    indexQuery = indexQuery + " on td.topic_id =ct.topic_id "
    indexQuery = indexQuery + " inner join teacher_profile tp "
    indexQuery = indexQuery + " on tp.teacher_id =cd.teacher_id "
    indexQuery = indexQuery + " group by "
    indexQuery = indexQuery + " cd.course_id, cd.course_name, cd.description , cd.image_url, tp.teacher_name "
    indexQuery = indexQuery + " having course_status=251"
    queryResult = db.session.execute(indexQuery).fetchall()
    queryKeys = db.session.execute(indexQuery).keys()
    items = [dict((queryKeys[i], value) \
               for i, value in enumerate(row)) for row in queryResult]
    #print(json.dumps(items))
    if task == "view":
        return json.dumps(items, indent=3)
    elif task=="send":        
        try:
            #index = client.init_index('staging_COURSE')
            index = client.init_index('prd_course')
            #batch = json.load(open('contacts.json'))            
            index.set_settings({"customRanking": ["desc(last_modified_date)"]})            	
            index.set_settings({"searchableAttributes": ["topic_name", "course_name", "teacher_name"]})
            index.save_objects(items, {'autoGenerateObjectIDIfNotExist': True})
            if fromPage=="default":
                return json.dumps({"The following data was sent to algolia index successfully":items})
            else:
                print("############# Course Indexed")
                return True
        except:
            print('########## Throwing exception')
            return "Error Sending index data to algolia"

    elif task=="deleteAll":
        filter_val = request.args.get('filter_val')
        
        #index = client.init_index('staging_COURSE')
        index = client.init_index('prd_course')         
        index.delete_by({'filters': 'board_id:1001'})
        #batch = json.load(open('contacts.json'))            
        #index.set_settings({"customRanking": ["asc(last_modified_date)"]})            	
        #index.set_settings({"searchableAttributes": ["topic_name", "course_name", "teacher_name"]})
        #index.save_objects(items, {'autoGenerateObjectIDIfNotExist': True})
        return json.dumps({"All indexes have been deleted from algolia under: ": filter_val})
        #except:
        #    return "Error Sending index data to algolia"



@app.route('/courseHome')
def courseHome():    
    if ("school.alllearn" in str(request.url)):
        print('#######this is the request url: '+ str(request.url))
        return redirect(url_for('index')) 
    #print(str(current_user.is_anonymous))
    upcomingClassData = ""
    
    #if current_user.is_anonymous==False:
        #upcomingClassQuery = "select * from vw_course_reminder_everyday where email=" + str(current_user.email)
        #upcomingClassData = db.session.execute(upcomingClassQuery).fetchall()
    enrolledCourses = "select ce.COURSE_ID, MAX(ce.LAST_MODIFIED_DATE), cd.course_name, cd.average_rating , cd.description ,cd.image_url, cd.is_archived,cd.course_status, tp.teacher_name,tp.teacher_id from course_enrollment ce "
    enrolledCourses = enrolledCourses + "inner join course_detail cd on cd.course_id =ce.course_id "
    enrolledCourses = enrolledCourses + "inner join teacher_profile tp on tp.teacher_id =cd.teacher_id "
    enrolledCourses = enrolledCourses + "group by ce.course_id,cd.course_name,cd.average_rating , cd.description , cd.image_url,cd.course_status, cd.is_archived, cd.teacher_id, tp.teacher_name, tp.teacher_id "
    enrolledCourses = enrolledCourses + "having cd.course_status =276 and cd.is_archived ='N' order by max(ce.last_modified_date ) desc limit 8"
    enrolledCourses = db.session.execute(text(enrolledCourses)).fetchall()
    recentlyAccessed = "select cd.COURSE_ID, MAX(cd.LAST_MODIFIED_DATE), cd.course_name, cd.average_rating , cd.description ,cd.image_url, cd.is_archived,cd.course_status, tp.teacher_name,cd.teacher_id from course_detail cd "
    recentlyAccessed = recentlyAccessed + "inner join teacher_profile tp on tp.teacher_id =cd.teacher_id "
    recentlyAccessed = recentlyAccessed + "group by cd.course_id,cd.course_name,cd.average_rating , cd.description , cd.image_url,cd.course_status, cd.is_archived, cd.teacher_id, tp.teacher_name having cd.course_status =276 and cd.is_archived ='N' order by max(cd.last_modified_date ) desc limit 8"
    recentlyAccessed = db.session.execute(text(recentlyAccessed)).fetchall() 

    for rate in enrolledCourses:
        print('Rating:'+str(rate.average_rating))
        if rate.average_rating:
            print('rate:'+str(rate.average_rating))

    idealFor = CourseDetail.query.distinct(CourseDetail.ideal_for).all()
    idealList = []
    for ideal in idealFor:
        print('ideal for:'+str(ideal.ideal_for))
        if ideal.ideal_for:
            data = ideal.ideal_for.split(',')
            for d in data:
                if d not in idealList:
                    idealList.append(d)
    print('List:'+str(idealList))
    indic='DashBoard'
    return render_template('courseHome.html',indic=indic,idealList=idealList,recentlyAccessed=recentlyAccessed,enrolledCourses=enrolledCourses,home=1, upcomingClassData=upcomingClassData)

@app.route('/openLiveClass')
def openLiveClass():
    print('inside openlive class')
    #live_class_id = request.args.get('live_class_id')
    topic_id = request.args.get('topic_id')
    batch_id = request.args.get('batch_id')
    course_id = request.args.get('course_id')
    print('topicID:'+str(topic_id))
    print('batch_id'+str(batch_id))
    print('course_id:'+str(course_id))

    videoExist = CourseTopics.query.filter_by(course_id=course_id,topic_id=topic_id).first()
    #topicName = Topic.query.filter_by(topic_id=topic_id).first()
    #courseId = CourseTopics.query.filter_by(topic_id=topic_id).first()
    #courseName = CourseDetail.query.filter_by(course_id=courseId.course_id).first()
    topicDataQuery = "select td.topic_id,ct.video_class_url, cd.course_id,ct.test_id,cd.course_name, td.topic_name, tp.teacher_id, tp.teacher_name, tp.user_id,tp.room_id "
    topicDataQuery = topicDataQuery + " from topic_detail td inner join course_topics ct on  "
    topicDataQuery = topicDataQuery + " ct.topic_id  = td.topic_id inner join course_detail cd on  "
    topicDataQuery = topicDataQuery + " cd.course_id  = ct.course_id  inner join teacher_profile tp on  "
    topicDataQuery = topicDataQuery + " tp.teacher_id  = cd.teacher_id where td.topic_id  =" + str(topic_id)
    topicDataQuery = topicDataQuery + " and cd.course_id=" + str(course_id)
    topicData = db.session.execute(topicDataQuery).first()

    if topicData== None:
        flash('No relevant course and topic found!')
        return redirect(url_for('courseDetail',course_id=course_id))
    
    #batchTestData = BatchTest.query.filter_by(batch_id=batch_id, is_archived='N', is_curren)

    notesList = TopicNotes.query.filter_by(topic_id=topic_id).all()
    comments = "select u.username,c.comment,c.last_modified_date from comments c inner join public.user u on u.id=c.user_id where c.topic_id = '"+str(topic_id)+"' and comment<>' ' and comment is not null  "
    comments = db.session.execute(text(comments)).fetchall()
    lenComm = 0
    if comments:
        lenComm = len(comments)
    #print('comment length:'+str(lenComm))
    #print('courseID:'+str(courseId.course_id))
    rating = CourseDetail.query.filter_by(course_id=topicData.course_id,is_archived='N').first()
    #if rating:
    #    print('Star rating:'+str(rating.average_rating))
    listTopics = "select td.topic_name,td.topic_id from topic_detail td inner join course_topics ct on td.topic_id=ct.topic_id where ct.course_id='"+str(topicData.course_id)+"' and ct.is_archived='N' and ct.topic_id <> '"+str(topic_id)+"' "
    listTopics = db.session.execute(text(listTopics)).fetchall()

    #updating table to say ongoing class
    enrolled=''
    ongoing='N'
    if batch_id!="" and batch_id!=None:
        courseBatchData = CourseBatch.query.filter_by(batch_id = batch_id,is_archived='N').first()
        courseBatchData.is_ongoing = 'Y'
        courseBatchData.ongoing_topic_id = topicData.topic_id
        courseBatchData.last_modified_date = datetime.today()
        db.session.commit()        
    else:
        #checking if a student is seeing the page and then seeing the batch id they're allocated to
        if current_user.is_anonymous==False:
            courseEnrollmentData = CourseEnrollment.query.filter_by(is_archived='N',course_id=topicData.course_id, student_user_id=current_user.id).first()        
            if courseEnrollmentData!=None and courseEnrollmentData!="":
                enrolled='Y'
                batch_id=courseEnrollmentData.batch_id
                courseBatchStudData = CourseBatch.query.filter_by(batch_id = batch_id,is_archived='N',is_ongoing='Y').first()
                if courseBatchStudData!=None and courseBatchStudData!="":
                    ongoing='Y'
        else:
            enrolled='N'
            batch_id=""

    pageTitle = str(topicData.topic_name)+' '+str(topicData.course_name)
    print('$#$$$$$$$$$$$$$'+str(batch_id))
    return render_template('openLiveClass.html',listTopics=listTopics,rating=rating,topicData=topicData
        ,lenComm=lenComm,ongoing=ongoing,title=pageTitle,meta_val=pageTitle,classVideo=videoExist.video_class_url,comments=comments,notesList=notesList,batch_id=batch_id,enrolled=enrolled)

@app.route('/courseDetail')
def courseDetail():
    live_class_id = request.args.get('live_class_id')
    course_id = request.args.get('course_id')
    courseDet = CourseDetail.query.filter_by(course_id=course_id).first()
    teacher = TeacherProfile.query.filter_by(teacher_id=courseDet.teacher_id).first()
    teacherUser = User.query.filter_by(id=teacher.user_id).first()

    upcomingDate = "SELECT * FROM course_batch WHERE batch_start_date > NOW() and course_id='"+str(course_id)+"' ORDER BY batch_start_date LIMIT 1"
    upcomingDate = db.session.execute(text(upcomingDate)).first()
    checkEnrollment = ''
    if upcomingDate and current_user.is_authenticated :
        checkEnrollment = CourseEnrollment.query.filter_by(is_archived='N',course_id=course_id,student_user_id=current_user.id).first()

    idealFor = courseDet.ideal_for.split(",")
    
    levelId = courseDet.difficulty_level
    level = MessageDetails.query.filter_by(msg_id=levelId,category='Difficulty Level').first()
    #rating = CourseDetail.query.filter_by(course_id=course_id,is_archived='N').first()
    #if rating:
    #    print('Star rating:'+str(rating.average_rating))
    comments = "select u.username,cr.comment,cr.last_modified_date from course_review cr inner join public.user u on u.id=cr.user_id where cr.course_id = '"+str(course_id)+ "' and cr.comment <> ' '"
    #print(comments)
    comments = db.session.execute(text(comments)).fetchall()
    lenComment = len(comments)
    #print(comments)
    otherCourses = "select *from course_detail cd where cd.course_id <> '"+str(course_id)+"' and cd.teacher_id='"+str(teacher.teacher_id)+"' and cd.course_status =276"
    otherCourses = db.session.execute(text(otherCourses)).fetchall()


    pageTitle = courseDet.course_name
    return render_template('courseDetail.html',
        lenComment=lenComment,comments=comments,otherCourses=otherCourses,level=level,
        idealFor=idealFor,upcomingDate=upcomingDate,
        courseDet=courseDet,meta_val=pageTitle,title=pageTitle,teacherUser=teacherUser,checkEnrollment=checkEnrollment,course_id=course_id,teacher=teacher)


@app.route('/courseTopicDetail')
def courseTopicDetail():
    course_id = request.args.get('course_id')
    topicDet = "select case when count(tq.question_id) >0 then count(tq.question_id )"
    topicDet = topicDet + " else 0 end as no_of_questions , topic_name,ct.video_class_url, ct.topic_id, course_id from course_topics ct "
    topicDet = topicDet + " inner join topic_detail td on td.topic_id =ct.topic_id and ct.course_id =" + str(course_id)
    topicDet = topicDet + " left join test_questions tq on tq.test_id =ct.test_id "    
    topicDet = topicDet + " where ct.is_archived ='N' group by  topic_name, ct.topic_id, course_id,ct.video_class_url"
    topicDet = topicDet + " order by topic_id asc "
    #print(topicDet)
    topicDet = db.session.execute(text(topicDet)).fetchall()
    return render_template('_courseTopicDetail.html', topicDet=topicDet,course_id=course_id)

@app.route('/fetchClassVideo',methods=['GET','POST'])
def fetchClassVideo():
    topic_id = request.args.get('topic_id')
    class_video = CourseTopics.query.filter_by(topic_id=topic_id).first()
    return jsonify(class_video.video_class_url)


@app.route('/courseBatchDetail')
def courseBatchDetail():
    course_id = request.args.get('course_id')
    teacher_user_id = request.args.get('teacher_user_id')
    #teacher = TeacherProfile.query.filter_by(teacher_id=courseDet.teacher_id).first()
    teacherUser = User.query.filter_by(id=teacher_user_id).first()
    courseBatchData = " select cb.batch_id ,cb.batch_end_date ,cb.batch_start_date ,cb.days_of_week ,cb.student_limit, cb.students_enrolled , "
    courseBatchData = courseBatchData + " cb.course_batch_fee,ce.student_user_id from course_batch cb left join course_enrollment ce on ce.batch_id = cb.batch_id "
    courseBatchData = courseBatchData + " and cb.course_id=ce.course_id "
    if current_user.is_anonymous==False:
        courseBatchData = courseBatchData + " and ce.student_user_id="+str(current_user.id) 
    courseBatchData = courseBatchData + " where cb.course_id = '"+str(course_id)+"' and cb.is_archived='N' "    
    courseBatchData = courseBatchData + " and cb.batch_end_date > NOW() "
    courseBatchData = courseBatchData + " order by cb.batch_start_date desc"
    print('Query:'+str(courseBatchData))
    courseBatchData = db.session.execute(text(courseBatchData)).fetchall()
    return render_template('_courseBatchDetail.html', courseBatchData=courseBatchData,teacherUser=teacherUser
        ,course_id=course_id)

@app.route('/studTakeQuiz', methods=['GET','POST'])
def studTakeQuiz():
    #course_id={{topicData.course_id}}&batch_id={{batch_id}}&topic_id={{topicData.topic_id}}",
    course_id = request.args.get('course_id')
    batch_id = request.args.get('batch_id')
    topic_id = request.args.get('topic_id')
    batchTestData = BatchTest.query.filter_by(batch_id=batch_id, topic_id=topic_id, is_current='Y').first()
    if batchTestData:
        return jsonify([batchTestData.resp_session_id])
    else:
        return jsonify(['1'])


@app.route('/addComments',methods=['GET','POST'])
def addComments():
    topicId = request.form.get('topicId')
    remark = request.form.get('remark')
    if remark:
        addComment = Comments(comment=remark,topic_id=topicId,user_id=current_user.id,is_archived='N',last_modified_date=datetime.now())
        db.session.add(addComment)
        db.session.commit()
    fetchComments = "select u.username,c.comment,c.last_modified_date from comments c inner join public.user u on u.id=c.user_id where c.topic_id = '"+str(topicId)+"'"
    fetchComments = db.session.execute(text(fetchComments)).fetchall()
    lenComm = len(fetchComments)
    print('length:'+str(lenComm))
    commentList = []
    for comment in fetchComments:
        commentList.append(str(comment.username)+":"+str(comment.comment)+":"+str(comment.last_modified_date.strftime('%d %B %Y'))+":"+str(lenComm))
    return jsonify(commentList)

@app.route('/addTopicReview',methods=['GET','POST'])
def addTopicReview():
    course_id = request.args.get('course_id')
    revComment = request.args.get('revComment')
    print('courseId:'+str(course_id))
    reviewRate = CourseReview.query.filter_by(course_id=course_id,is_archived='N',user_id=current_user.id).first()
    reviewRate.comment = revComment
    db.session.commit()
    return jsonify("1")

@app.route('/addReviewComment',methods=['GET','POST'])
def addReviewComment():
    course_id = request.args.get('course_id')
    revComment = request.args.get('revComment')
    starRating = request.args.get('starRating')
    
    print('courseId:'+str(course_id))
    reviewRate = CourseReview.query.filter_by(course_id=str(course_id),is_archived='N',user_id=current_user.id).first()
    if reviewRate==None or revComment=="":
        reviewDataAdd = CourseReview(course_id=str(course_id), star_rating = starRating, comment = str(revComment),
            is_archived = 'N', last_modified_date=datetime.today(), user_id=current_user.id)
        db.session.add(reviewDataAdd )
    else:
        reviewRate.comment = revComment
    db.session.commit()
    fetchReview = "select u.username,cr.comment,cr.last_modified_date from course_review cr inner join public.user u on u.id=cr.user_id where cr.course_id = '"+str(course_id)+"' and cr.comment <> ' '"
    fetchReview = db.session.execute(text(fetchReview)).fetchall()
    lenComm = len(fetchReview)
    print('length:'+str(lenComm))
    reviewList = []
    for review in fetchReview:
        reviewList.append(str(review.username)+":"+str(review.comment)+":"+str(review.last_modified_date.strftime('%d %B %Y'))+":"+str(lenComm))
    return jsonify(reviewList)

@app.route('/addRatingReview',methods=['GET','POST'])
def addRatingReview():
    course_id = request.args.get('course_id')
    rating = request.args.get('rating')
    dataExist = CourseReview.query.filter_by(course_id=course_id,is_archived='N',user_id=current_user.id).first()
    if dataExist:
        dataExist.star_rating = rating
        dataExist.comment = ' '
        db.session.commit()
        courseRevDet = CourseReview.query.filter_by(course_id=course_id,is_archived='N').all()
        aveRat = 0
        for rate in courseRevDet:
            aveRat = aveRat + rate.star_rating
        aveRat = aveRat / len(courseRevDet)
        print('course_id:'+str(course_id))
        print('Average rating:'+str(aveRat))
        courseData = CourseDetail.query.filter_by(course_id=course_id).first()
        courseData.average_rating = aveRat
        db.session.commit()
        return jsonify("1")
    print('Rating:'+str(rating))
    courseRev = CourseReview(course_id=course_id,star_rating=rating,comment=' ',is_archived='N',last_modified_date=datetime.now(),user_id=current_user.id)
    db.session.add(courseRev)
    db.session.commit()
    courseRevDet = CourseReview.query.filter_by(course_id=course_id,is_archived='N').all()
    aveRat = 0
    for rate in courseRevDet:
        aveRat = aveRat + rate.star_rating
    aveRat = aveRat / len(courseRevDet)
    print('Average rating:'+str(aveRat))
    courseData = CourseDetail.query.filter_by(course_id=course_id).first()
    courseData.average_rating = aveRat
    db.session.commit()
    return jsonify("1")

@app.route('/addReview',methods=['GET','POST'])
def addReview():
    course_id = request.args.get('course_id')
    rating = request.args.get('rating')
    dataExist = CourseReview.query.filter_by(course_id=course_id,is_archived='N',user_id=current_user.id).first()
    if dataExist:
        dataExist.star_rating = rating
        dataExist.comment = ' '
        db.session.commit()
        courseRevDet = CourseReview.query.filter_by(course_id=course_id,is_archived='N').all()
        aveRat = 0
        for rate in courseRevDet:
            aveRat = aveRat + rate.star_rating
        aveRat = aveRat / len(courseRevDet)
        print('course_id:'+str(course_id))
        print('Average rating:'+str(aveRat))
        courseData = CourseDetail.query.filter_by(course_id=course_id).first()
        courseData.average_rating = aveRat
        db.session.commit()
        fetchReview = "select u.username,cr.comment,cr.last_modified_date from course_review cr inner join public.user u on u.id=cr.user_id where cr.course_id = '"+str(course_id)+"' and cr.comment <> ' '"
        fetchReview = db.session.execute(text(fetchReview)).fetchall()
        lenComm = len(fetchReview)
        print('length:'+str(lenComm))
        reviewList = []
        for review in fetchReview:
            reviewList.append(str(review.username)+":"+str(review.comment)+":"+str(review.last_modified_date.strftime('%d %B %Y'))+":"+str(lenComm))
        return jsonify(reviewList)
    print('Rating:'+str(rating))
    courseRev = CourseReview(course_id=course_id,star_rating=rating,comment=' ',is_archived='N',last_modified_date=datetime.now(),user_id=current_user.id)
    db.session.add(courseRev)
    db.session.commit()
    courseRevDet = CourseReview.query.filter_by(course_id=course_id,is_archived='N').all()
    aveRat = 0
    for rate in courseRevDet:
        aveRat = aveRat + rate.star_rating
    aveRat = aveRat / len(courseRevDet)
    print('Average rating:'+str(aveRat))
    courseData = CourseDetail.query.filter_by(course_id=course_id).first()
    courseData.average_rating = aveRat
    db.session.commit()
    fetchReview = "select u.username,cr.comment,cr.last_modified_date from course_review cr inner join public.user u on u.id=cr.user_id where cr.course_id = '"+str(course_id)+"' and cr.comment <> ' '"
    fetchReview = db.session.execute(text(fetchReview)).fetchall()
    lenComm = len(fetchReview)
    print('length:'+str(lenComm))
    reviewList = []
    for review in fetchReview:
        reviewList.append(str(review.username)+":"+str(review.comment)+":"+str(review.last_modified_date.strftime('%d %B %Y'))+":"+str(lenComm))
    return jsonify(reviewList)

@app.route('/batchTopicList',methods=['GET','POST'])
def batchTopicList():
    batch_id = request.args.get('batch_id')
    courseId = CourseBatch.query.filter_by(batch_id=batch_id).first()
    topicIds = CourseTopics.query.filter_by(course_id=courseId.course_id,is_archived='N').all()
    topics = []
    for topicId in topicIds:
        topicName = Topic.query.filter_by(topic_id=topicId.topic_id).first()
        topics.append(str(topicName.topic_name)+':'+str(topicName.topic_id))
    if topics:
        return jsonify(topics)
    else:
        return ""

@app.route('/tutorDashboard',methods=['GET','POST'])
def tutorDashboard():
    tutor_id = request.args.get('tutor_id')
    user_id = request.args.get('user_id')
    if user_id:
        TeacherId = TeacherProfile.query.filter_by(user_id=user_id).first()
        
    else:
        TeacherId = TeacherProfile.query.filter_by(teacher_id=tutor_id).first()
    
    if TeacherId==None:
        return redirect(url_for('courseHome'))
    else:
        tutor_id=TeacherId.teacher_id
    user = User.query.filter_by(id=TeacherId.user_id).first()
    # courseDet = CourseDetail.query.filter_by(teacher_id=TeacherId.teacher_id).all()
    courseDet = "select count(*) as no_of_topic,cd.course_name,md.description as desc,cd.description,cd.image_url,cd.course_id from course_detail cd left join course_topics ct on ct.course_id=cd.course_id inner join message_detail md on md.msg_id = cd.course_status where cd.teacher_id='"+str(tutor_id)+"' and cd.is_archived='N' group by course_name,md.description,cd.description,cd.image_url,cd.course_id order by cd.course_id desc"
    
    courseDet = db.session.execute(text(courseDet)).fetchall()
    print(courseDet)
    feeType = MessageDetails.query.filter_by(category='Fee Type').all()
    return render_template('tutorDashboard.html',user=user,tutor_id=tutor_id,feeType=feeType,courseDet=courseDet,teacher_name = user.first_name+' '+user.last_name,profile_pic = user.user_avatar,email = user.email,students_taught=TeacherId.students_taught,courses_created=TeacherId.courses_created)

@app.route('/fetchBatch',methods=['GET','POST'])
def fetchBatch():
    print('inside fetch Batch')
    courseId = request.args.get('courseId')
    courseName = CourseDetail.query.filter_by(course_id=courseId).first()
    fetchBatch = "select cb.batch_start_date,cb.batch_end_date,cb.batch_start_time,cb.batch_end_time,cb.days_of_week,cb.student_limit,cb.students_enrolled,cb.course_batch_fee,cb.total_fee_received,cb.fee_type,md.description "
    fetchBatch = fetchBatch + "from course_batch cb inner join message_detail md on cb.fee_type=md.msg_id where cb.course_id='"+str(courseId)+"' and cb.is_archived='N' order by batch_start_date desc"
    print('Query:'+str(fetchBatch))
    fetchBatch = db.session.execute(text(fetchBatch)).fetchall()
    return render_template('_batchDetail.html',fetchBatch=fetchBatch,courseName=courseName)

@app.route('/createBatch',methods=['GET','POST'])
def createBatch():
    startDate = request.form.get('startDate')
    EndDate = request.form.get('EndDate')
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    days = request.form.getlist('Days')
    studentLimit = request.form.get('studentLimit')
    batchFee = request.form.get('batchFee')
    coId = request.form.get('coId')
    print('New courseId:'+str(coId))
    if batchFee==None:
        batchFee=0
    enrolledStudents = request.form.get('enrolledStudents')
    feeReceived = request.form.get('feeReceived')
    courseId = request.args.get('courseId')
    print('previous courseID:'+str(courseId))
    selectType = request.form.get('selectType')
    print('startDate:'+str(startDate))
    print('selectType:'+str(selectType))
    print('EndDate:'+str(EndDate))
    print('startTime:'+str(startTime))
    print('endTime:'+str(endTime))
    print('days:'+str(days))
    print('studentLimit:'+str(studentLimit))
    print('batchFee:'+str(batchFee))
    print('enrolledStudents:'+str(enrolledStudents))
    print('feeReceived:'+str(feeReceived))
    print('courseId:'+str(courseId))
    dayString = ''
    i=1
    for day in days:
        print('Day:'+str(day))
        dayS =  str(day)
        if i==len(days):
            dayString = dayString + dayS
        else:
            dayString = dayString + dayS + ','
        i=i+1
    print('StringDays:'+str(dayString))
    if startDate and EndDate and startTime and endTime and days and studentLimit and enrolledStudents and selectType:
        createBatch = CourseBatch(course_id=courseId,batch_start_date=startDate,
        batch_end_date=EndDate,batch_start_time=startTime,batch_end_time=endTime,
        days_of_week=dayString,student_limit=studentLimit,course_batch_fee=float(batchFee),
        students_enrolled=enrolledStudents,total_fee_received=0,fee_type=selectType,
        is_archived='N',last_modified_date=datetime.now())
        db.session.add(createBatch)
        db.session.commit()
        return jsonify("1")
    else:
        return ""

@app.route('/teacherRegistration')
def teacherRegistration():
    print('inside teacher Registration')
    School = "select *from school_profile sp where school_name not like '%_school' order by school_id desc"
    School = db.session.execute(text(School)).fetchall()
    NewSchool = "select *from school_profile order by school_id desc"
    NewSchool = db.session.execute(text(NewSchool)).fetchall()
    reviewStatus = "select *from teacher_profile where user_id='"+str(current_user.id)+"' "
    reviewStatus = db.session.execute(text(reviewStatus)).first()
    teacher_id = request.args.get('teacher_id')
    print(teacher_id)
    teacherDetail = ''
    bankDetail = ''
    if teacher_id:
        teacher = TeacherProfile.query.filter_by(teacher_id = teacher_id).first()
        #for school in School:
        #    print('School name:'+str(school.school_name))
        teacherDetail = User.query.filter_by(id = teacher.user_id).first()
        school_id = SchoolProfile.query.filter_by(school_id=current_user.school_id).first() 
        email = str(current_user.email).lower().replace(' ','_')
        vendorId = str(email)+str('_school_')+str(teacher.school_id)+str('_1')
        print(vendorId)
        bankDetail = BankDetail.query.filter_by(vendor_id=vendorId).first()
        print('details')
        print(bankDetail)
        print(teacherDetail.about_me)
        if reviewStatus:
            return render_template('teacherRegistration.html',School=School,NewSchool=NewSchool,reviewStatus=reviewStatus.review_status,bankDetail=bankDetail,teacherDetail=teacherDetail,teacher_id=teacher_id)
        else:
            return render_template('teacherRegistration.html',School=School,NewSchool=NewSchool,bankDetail=bankDetail,teacherDetail=teacherDetail,teacher_id=teacher_id)
    
    if reviewStatus:
        print('if not registered as teacher')
        return render_template('teacherRegistration.html',School=School,NewSchool=NewSchool,reviewStatus=reviewStatus.review_status,bankDetail=bankDetail,teacherDetail=teacherDetail,teacher_id=teacher_id)
    else:
        print('if not registered as teacher')
        return render_template('teacherRegistration.html',School=School,NewSchool=NewSchool,bankDetail=bankDetail,teacherDetail=teacherDetail,teacher_id=teacher_id)
@app.route('/teacherRegForm',methods=['GET','POST'])
def teacherRegForm():
    bankName =request.form.get('bankName')
    accountHolderName = request.form.get('accountHoldername')
    accountNo = request.form.get('accountNumber')
    IfscCode = request.form.get('ifscCode')
    selectSchool = request.form.get('selectSchool')
    selectedSchool = request.form.get('NewSchool')
    # if selectSchool==None:
    print('select school id')
    print(selectSchool)
    if selectSchool=='None':
        selectSchool = selectedSchool
    user_avatar = request.form.get('imageUrl')
    about_me = request.form.get('about_me')
    schoolName = str(current_user.email)+"_school"
    current_user.about_me = about_me
    teacher_id = request.args.get('teacher_id')
    print('Teacher_id:'+str(teacher_id))
    if teacher_id=='None':
        teacher_id = ''
        print(teacher_id)
    if teacher_id:
        user_id = TeacherProfile.query.filter_by(teacher_id=teacher_id).first()
        schoolIds = user_id.school_id
        user = User.query.filter_by(id=user_id.user_id).first()
        user.user_avatar = user_avatar
        user.about_me = about_me
        db.session.commit()
        school = ''
        if selectSchool:
            school = SchoolProfile.query.filter_by(school_id=selectSchool).first()
        else:
            schoolName = str(current_user.id)+str('_school')
            board  = MessageDetails.query.filter_by(category='Board',description='Other').first()
            school = SchoolProfile(school_name = schoolName,registered_date=datetime.now(),last_modified_date=datetime.now(),board_id=board.msg_id,school_admin=teacher_id,school_type='individual')
            db.session.add(school)
            db.session.commit()
            school = SchoolProfile.query.filter_by(school_name = schoolName).first()
        user_id.school_id = school.school_id
        user_id.review_status = '273'
        db.session.commit()
        print('previous school id:'+str(schoolIds))
        
        vendor = str(current_user.email).lower().replace(' ','_')
        vendorId = str(vendor) +'_school_'+ str(schoolIds) + '_1'
        ven = str(vendor)+'_school_'+str(school.school_id)+'_1'
        
        print('current school id:'+str(school.school_id))
        current_user.school_id = school.school_id
        print(vendorId)
        bankIdExist = BankDetail.query.filter_by(vendor_id=ven).first()
        if bankIdExist:
            bankIdExist.account_num = accountNo
            bankIdExist.ifsc = IfscCode
            bankIdExist.bank_name = bankName
            bankIdExist.account_name = accountHolderName
            db.session.commit()
        else:
            bankDet = BankDetail(account_num=accountNo,ifsc=IfscCode,vendor_id=ven,bank_name=bankName,account_name=accountHolderName,school_id=school.school_id,is_archived='N')
            db.session.add(bankDet)
            db.session.commit()
            school.current_vendor_id = ven
            db.session.commit()
        reviewStatus = "select *from teacher_profile where user_id='"+str(current_user.id)+" '"
        reviewStatus = db.session.execute(text(reviewStatus)).first()
        print('Review status:'+str(reviewStatus.review_status))
        return jsonify(reviewStatus.review_status)
    print('School Id:'+str(selectSchool))
    schoolEx = ''
    if selectSchool:
        schoolEx = SchoolProfile.query.filter_by(school_id=selectSchool).first()
    if user_avatar!=None:
        current_user.user_avatar = user_avatar
    if about_me!=None:
        current_user.about_me = about_me
    board  = MessageDetails.query.filter_by(category='Board',description='Other').first()
    checkTeacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print('Teacher:'+str(checkTeacher))
    if checkTeacher==None:
        ## Adding new school record
        print('if teacher is none')
        schoolAdd = ''
        if selectSchool==None:
            print('if school id is none')
            schoolAdd = SchoolProfile(school_name=schoolName,board_id=board.msg_id,registered_date=datetime.now(),school_type='individual',last_modified_date=datetime.now())
            db.session.add(schoolAdd)
            current_user.school_id = schoolAdd.school_id
            db.session.commit()
            exSchool = SchoolProfile.query.filter_by(school_name=schoolName,school_type='individual',board_id=board.msg_id).first()
            schoolEx = exSchool
        ##Adding new teacher record
        print(schoolEx.school_id)
        teacherAdd = TeacherProfile(teacher_name=str(current_user.first_name)+' '+str(current_user.last_name),school_id=schoolEx.school_id,registration_date=datetime.now(),email=current_user.email,phone=current_user.phone,user_id=current_user.id,device_preference='195',last_modified_date=datetime.now())
        db.session.add(teacherAdd)
        db.session.commit()
        #Updating school admin with the new teacher ID
        #teacherEx = TeacherProfile.query.filter_by(user_id=current_user.id).first()
        checkTeacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
        schoolEx.school_admin = checkTeacher.teacher_id
        #generating vendor id
        vendorId = str(schoolName).lower().replace(' ','_')
        vendorId = str(vendorId) +'_'+ str(schoolEx.school_id) + '_1'
        #schoolAdd.curr_vendor_id = vendorId
        current_user.school_id = schoolEx.school_id
        db.session.commit()
        reviewId = MessageDetails.query.filter_by(description='Inreview',category='Review Status').first()
        reviewInsert = "update teacher_profile set review_status='"+str(reviewId.msg_id)+"' where user_id='"+str(current_user.id)+"' "
        #Send sms to tech team to follow up
        reviewInsert = db.session.execute(text(reviewInsert))
        message = "New tutor has been registered in the database. Please setup contact them on email: "+ current_user.email 
        message = message + " and phone: " + current_user.phone + " for review and pg setup"
        phoneList = "9008500227,9910368828"        
        #calling SMS function        
        smsResponse = sendSMS(message, phoneList)
        print("This is the sms send response: " + smsResponse)

        ##Section to bank details
        print('Bank Details')
        print(accountNo)
        print(IfscCode)
        print(bankName)
        print(accountHolderName)
        print(vendorId)
        bankDetailAdd = BankDetail(account_num = accountNo, ifsc=IfscCode, bank_name=bankName, account_name=accountHolderName, 
            school_id=schoolEx.school_id, vendor_id=vendorId,
            is_archived='N')
        db.session.add(bankDetailAdd)
        db.session.commit()
        schoolEx.curr_vendor_id = vendorId
        db.session.commit()
        ##Section to add vendor with payment gateway


        ## Section to create a roomid  for the teacher
    print("####This is the current room id: " + str(checkTeacher.room_id))
    if checkTeacher.room_id==None:            
        roomResponse = roomCreation()
        roomResponseJson = roomResponse.json()
        print("New room ID created: " +str(roomResponseJson["url"]))
        checkTeacher.room_id = str(roomResponseJson["url"])
        db.session.commit()
    reviewStatus = "select *from teacher_profile where user_id='"+str(current_user.id)+" '"
    reviewStatus = db.session.execute(text(reviewStatus)).first()
    print('Review status:'+str(reviewStatus.review_status))
    return jsonify(reviewStatus.review_status)


@app.route('/getOnlineClassLink',methods=['GET','POST'])
def getOnlineClassLink():
    if request.method == 'POST':
        jsonExamData = request.json 
        # jsonExamData = {"contact":{"phone":"9008262739"},"result":{"data":"1"}}       
        data = json.dumps(jsonExamData)
        response = json.loads(data)
        paramList = []
        conList = []
        print('data:')
        # print(z['result'].class_val)
        # print(z['result'])
        for data in response['contact'].values():
            conList.append(data)
        print('Data Contact')
        # print(conList[2])
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
        if teacher_id.room_id==None:            
            roomResponse = roomCreation()
            roomResponseJson = roomResponse.json()
            print("New room ID created: " +str(roomResponseJson["url"]))
            teacher_id.room_id = str(roomResponseJson["url"])
            db.session.commit()
        OnlineClassLink = str('Online class link:\n')+ str(teacher_id.room_id)
        return jsonify({'onlineClassLink':OnlineClassLink})

##Helper function
def roomCreation():
    dailycourl = "https://api.daily.co/v1/rooms"
    payload = {"properties": {
            "max_participants": 50,
            "enable_screenshare": True,
            "enable_chat": True,
            "start_video_off": True,
            "start_audio_off": True,
            "owner_only_broadcast": True,
            "eject_at_room_exp": True,
            "eject_after_elapsed": 4
        }}
    headers = {
        "content-type": "application/json",
        "authorization": "Bearer 157accd1531abddc376517325567f744168d28be21a18cc1bec3e356695259b4"
    }
    response = rq.request("POST", dailycourl, json=payload, headers=headers)
    #print("##########Room Creation response: "+response.text)
    return response

##Helper function
def sendSMS(message, phoneList):
    apiPath = "http://173.212.233.109/app/smsapisr/index.php?key=35EF8379A04DB8&"
    apiPath = apiPath + "campaign=9967&routeid=6&type=text&"
    apiPath = apiPath + "contacts="+str(phoneList) +"&senderid=GLOBAL&"
    apiPath = apiPath + "msg="+ quote(message)
    print(apiPath)
    ##Sending message here
    try:
        r = requests.post(apiPath)                    
        returnData = str(r.text)
        print(returnData)
        
        if "SMS-SHOOT-ID" in returnData:
            return "SMS sent successfully"
        else:
            return "Error sending sms"
        #    for val in studentPhones:
        #        commTransAdd = CommunicationTransaction(comm_id=commDataAdd.comm_id, student_id=val.student_id,last_modified_date = datetime.today())
        #        db.session.add(commTransAdd)
        #    commDataAdd.status=232
        #    db.session.commit()                                        
        #    return jsonify(['0'])
        #else:
        #    return jsonify(['1'])                    
    except:
        return "Exception in sending sms"

#def vendorAddition():

    #Request {"vendorId" : "VEN343", "name" : "343 Industries", "phone" : 9900034300, "email" : "three43@gmail.com", "commission" : 34.3, "bankAccount" : 30004343400003, "accountHolder" : "TFT", "ifsc" : "HDFC0000343", "address1" : "Diamond District", "address2" : "Indranagar", "city" : "Bengaluru", "state" : "Karnataka", "panNo" : "AAAPL1234C", "aadharNo" : "499118665246", "gstin" : "22AAAAA0000A1Z5", "pincode" : 560071}
    #Response {"status":"SUCCESS", "subCode":"200", "message":"Vendor added successfully"}


@app.route('/addCourse')
def addCourse():
    course_id = request.args.get('course_id')
    if course_id=='':
        courId = CourseDetail(course_name='Untitled Course',course_status=275,is_archived='N',last_modified_date=datetime.now())
        db.session.add(courId)
        db.session.commit()
        course_id = courId.course_id
    return redirect(url_for('editCourse',course_id=course_id))

@app.route('/editCourse')
def editCourse():
    print('inside editCourse')
    course_category = MessageDetails.query.filter_by(category='Course Category').first()
    desc = course_category.description.split(',')
    course_id=request.args.get('course_id')
    teacherIdExist = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print('userID:'+str(current_user.id))
    print('Teacher:'+str(teacherIdExist))
    reviewStatus = "select *from teacher_profile where user_id='"+str(current_user.id)+"'"
    reviewStatus = db.session.execute(text(reviewStatus)).first()
    if reviewStatus:
        print('REview status:'+str(reviewStatus.review_status))
        if reviewStatus.review_status==273:
            print('review status Inreview')
            return redirect(url_for('teacherRegistration'))
    if teacherIdExist==None:
        return redirect(url_for('teacherRegistration'))
    else:
        print('Description:'+str(desc))
        print('course_id:'+str(course_id))
        if course_id:
            courseDet = CourseDetail.query.filter_by(course_id=course_id).first()
            levelId = MessageDetails.query.filter_by(category='Difficulty Level',msg_id=courseDet.difficulty_level).first()
            courseNotes = TopicNotes.query.filter_by(course_id=course_id).first()
            # topicDet = "select count(*) as no_of_questions,td.topic_name,td.topic_id,ct.course_id from course_topics ct "
            # topicDet = topicDet + "inner join topic_detail td on ct.topic_id=td.topic_id "
            # topicDet = topicDet + "left join test_questions tq on ct.test_id = tq.test_id "
            # topicDet = topicDet + "where ct.course_id = '"+str(course_id)+"' and tq.is_archived='N' and ct.is_archived='N' group by td.topic_name,td.topic_id,ct.course_id "
            
            topicL = []
            topicsID = CourseTopics.query.filter_by(course_id=course_id,is_archived='N').all()
            for topicId in topicsID:
                topicList = []
                topic_name = Topic.query.filter_by(topic_id=topicId.topic_id).first()
                quesNo = TestQuestions.query.filter_by(test_id=topicId.test_id,is_archived='N').all()
                questionNo = len(quesNo)
                topicList.append(topic_name.topic_name)
                topicList.append(questionNo)
                topicList.append(topicId.topic_id)
                notes = TopicNotes.query.filter_by(topic_id=topicId.topic_id,is_archived='N').first()
                recording = "select *from course_topics where course_id='"+str(course_id)+"' and topic_id='"+str(topicId.topic_id)+"' and video_class_url<>'' order by topic_id asc"
                recording = db.session.execute(text(recording)).first()
                checkNotes = ''
                checkRec = ''
                if notes:
                    checkNotes = notes.notes_name
                if recording:
                    checkRec = recording.video_class_url
                topicList.append(checkNotes)
                topicList.append(checkRec)
                print(topicList)
                topicL.append(topicList)
            print(topicL)
            for topic in topicL:
                print(topic[0])
                print(topic[1])
                print(topic[2])
            # topicDet = db.session.execute(text(topicDet)).fetchall()
            idealFor = ''
            if courseDet:
                idealFor = courseDet.ideal_for
            levelId = ''
            if levelId:
                levelId = levelId.description
            print('Description:'+str(courseDet.description))
            status = 1
            return render_template('editCourse.html',status=status,levelId=levelId,idealFor=idealFor,desc=desc,courseDet=courseDet,course_id=course_id,topicDet=topicL)
        else:
            levelId = ''
            return render_template('editCourse.html',levelId=levelId,desc=desc,course_id=course_id)
    


#clip = (VideoFileClip("frozen_trailer.mp4")
#        .subclip((1,22.65),(1,23.2))
#        .resize(0.3))
#clip.write_gif("use_your_head.gif")



@app.route('/searchTopic',methods=['GET','POST'])
def searchTopic():
    topic = request.args.get('topic')
    courseId = request.args.get('courseId')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    coursesId = CourseDetail.query.filter_by(teacher_id=teacher_id.teacher_id).all()
    topicArray = []
    for course_id in coursesId:
        if str(course_id.course_id)!=str(courseId):
            TopicIds = "select td.topic_id,td.topic_name from topic_detail td inner join course_topics ct on td.topic_id = ct.topic_id where td.topic_name like '"+str(topic)+"%'  and ct.course_id ='"+str(course_id.course_id)+"' and ct.is_archived='N'"
            TopicIds = db.session.execute(text(TopicIds)).fetchall()
            for top in TopicIds:
                print('Topic:'+str(top))
                topicArray.append(str(top.topic_id)+':'+str(top.topic_name)+':'+str(course_id.course_id))
    if topicArray:
        return jsonify([topicArray])
    else:
        return ""

@app.route('/fetchQues',methods=['GET','POST'])
def fetchQues():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacherData.school_id).first()
    print('inside fetchQues')
    courseId = request.args.get('courseId')
    print('courseId:'+str(courseId))
    topics = CourseTopics.query.filter_by(course_id=courseId,is_archived='N').order_by(CourseTopics.topic_id.desc()).all()
    topicsDet = []
    for topic in topics:
        topicName = Topic.query.filter_by(topic_id=topic.topic_id).first()
        quesIds = TestQuestions.query.filter_by(test_id=topic.test_id,is_archived='N').all()
        quesNo = len(quesIds)
        notes = TopicNotes.query.filter_by(topic_id=topic.topic_id,is_archived='N').first()
        checkNotes = ''
        checkRec = ''
        if notes:
            checkNotes = notes.notes_name
        recording = "select *from course_topics where course_id='"+str(courseId)+"' and topic_id='"+str(topic.topic_id)+"' and video_class_url<>'' order by topic_id"
        recording = db.session.execute(text(recording)).first()
        if recording:
            checkRec = recording.video_class_url
        topic = topicName.topic_name.replace(",","/")
        topicsDet.append(str(topic)+':'+str(quesNo)+':'+str(topicName.topic_id)+':'+str(checkNotes)+':'+str(checkRec))
    if topicsDet:
        return jsonify(topicsDet)
    else:
        return ""

@app.route('/fetchRecording',methods=['GET','POST'])
def fetchRecording():
    print('inside fetchRecording')
    topic_id = request.args.get('topic_id')
    courseId = request.args.get('courseId')
    record = CourseTopics.query.filter_by(course_id=courseId,topic_id=topic_id).first()
    return jsonify(record.video_class_url)

@app.route('/deleteNotes',methods=['GET','POST'])
def deleteNotes():
    notes_id = request.args.get('notes_id')
    notes = TopicNotes.query.filter_by(tn_id=notes_id).first()
    notes.is_archived = 'Y'
    db.session.commit()
    return jsonify(notes.topic_id)


@app.route('/fetchNotes',methods=['GET','POST'])
def fetchNotes():
    print('inside fetchNotes')
    topic_id = request.args.get('topic_id')
    notes = TopicNotes.query.filter_by(topic_id=topic_id,is_archived='N').all()
    notesData = []
    for note in notes:
        NewNotes = note.notes_name.replace(",","/")
        notesData.append(str(NewNotes)+'!'+str(note.notes_url)+'!'+str(note.tn_id))
    print(notesData)
    if notesData:
        return jsonify(notesData)
    else:
        return ""

@app.route('/fetchRemQues',methods=['GET','POST'])
def fetchRemQues():
    quesIdList = request.get_json()
    quesArray = []
    for qId in quesIdList:
        print('Question Id:'+str(qId))
        quesObj = {}    
        quesName = QuestionDetails.query.filter_by(question_id=qId).first()
        quesObj['quesName'] = quesName.question_description
        print('Ques:'+str(quesName.question_description))
        quesOptions = QuestionOptions.query.filter_by(question_id=qId).all()
        i=0
        opt1=''
        opt2=''
        opt3=''
        opt4=''
        for option in quesOptions:
            if i==0:
                opt1 = option.option_desc
            elif i==1:
                opt2 = option.option_desc
            elif i==2:
                opt3 = option.option_desc
            else:
                opt4 = option.option_desc
            i=i+1
            print('quesOptions:'+str(option.option_desc))
        quesArray.append(str(quesName.question_description)+':'+str(opt1)+':'+str(opt2)+':'+str(opt3)+':'+str(opt4)+':'+str(qId))
    print('quesArray:')
    print(quesArray)
    if quesArray:
        return jsonify(quesArray)
    else:
        return ""

@app.route('/topicName',methods=['GET','POST'])
def topicName():
    print('inside topicName')
    topicId = request.args.get('topic_id')
    topicName = Topic.query.filter_by(topic_id=topicId).first()
    topic_name = topicName.topic_name
    print('topic name:'+topic_name)

    return jsonify(topic_name)

@app.route('/fetchTopicQues',methods=['GET','POST'])
def fetchTopicsQues():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacherData.school_id).first()
    print('inside fetchTopics')
    topic_id = request.args.get('topic_id')
    courseId = request.args.get('courseId')
    print('topic_id:'+str(topic_id))
    topics = CourseTopics.query.filter_by(topic_id=topic_id,is_archived='N').first()
    topicName = Topic.query.filter_by(topic_id=topics.topic_id).first()
    print('Topic name:'+str(topicName.topic_name))
    quesIds = TestQuestions.query.filter_by(test_id=topics.test_id,is_archived='N').all()
    # topicNotes = TopicNotes.query.filter_by(topic_id=topics.topic_id).first()
    # NotesName = topicNotes.notes_name
    # NotesUrl = topicNotes.notes_url
    quesArray = []
    NewTopicName = ''
    if len(quesIds)==0:
        NewTopicName = topicName.topic_name.replace(",","/")
        quesArray.append(str('')+':'+str(NewTopicName)+':'+str('')+':'+str('')+':'+str('')+':'+str('')+':'+str('')+':'+str(topicName.topic_id))
    for qId in quesIds:
        quesObj = {}    
        quesName = QuestionDetails.query.filter_by(question_id=qId.question_id).first()
        quesObj['quesName'] = quesName.question_description
        quesObj['topic_name'] = topicName.topic_name
        print('Ques:'+str(quesName.question_description))
        print('topicName:'+str(topicName.topic_name))
        quesOptions = QuestionOptions.query.filter_by(question_id=qId.question_id).all()
        i=0
        opt1=''
        opt2=''
        opt3=''
        opt4=''
        for option in quesOptions:
            if i==0:
                opt1 = option.option_desc
            elif i==1:
                opt2 = option.option_desc
            elif i==2:
                opt3 = option.option_desc
            else:
                opt4 = option.option_desc
            i=i+1
            print('quesOptions:'+str(option.option_desc))
        NewTopicName = topicName.topic_name.replace(",","/")
        quesArray.append(str(quesName.question_description)+':'+str(NewTopicName)+':'+str(opt1)+':'+str(opt2)+':'+str(opt3)+':'+str(opt4)+':'+str(qId.question_id)+':'+str(topicName.topic_id))
    print('quesArray:')
    print(quesArray)
    if quesArray:
        return jsonify(quesArray)
    else:
        return ""

@app.route('/deleteTopic',methods=['GET','POST'])
def deleteTopic():
    print('inside deleteTopic')
    topicId = request.args.get('topicId')
    print('Topic id:'+str(topicId))
    course_id = request.args.get('course_id')
    courseTopic = CourseTopics.query.filter_by(topic_id=topicId,course_id=course_id,is_archived='N').first()
    courseTopic.is_archived = 'Y'
    db.session.commit()
    notes = "update topic_notes set is_archived='Y' where topic_id='"+str(topicId)+"' and is_archived='N'"
    notes = db.session.execute(text(notes))
    db.session.commit()
    return jsonify("1")

@app.route('/updateCourseTopic',methods=['GET','POST'])
def updateCourseTopic():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacherData.school_id).first()
    print('inside updateCourseTopic')
    topicId = request.args.get('topicId')
    courseId = request.args.get('courseId')
    topicName = request.args.get('topicName')
    print('Topic Id:'+str(topicId))
    print('courseId:'+str(courseId))
    quesIds = request.get_json()
    print(quesIds)
    topicDet = Topic.query.filter_by(topic_id=topicId).first()
    topicDet.topic_name = topicName
    db.session.commit()
    testId = CourseTopics.query.filter_by(course_id=courseId,topic_id=topicId).first()
    # totalQId = TestQuestions.query.filter_by(test_id=testId.test_id).all()
    deleteAll = "update test_questions set is_archived='Y' where test_id='"+str(testId.test_id)+"' "
    deleteAll = db.session.execute(text(deleteAll))
    # print('Total Question Ids:'+str(totalQId))
    print('Total not deleted Ques Ids:'+str(quesIds))
    print(quesIds)
    print('Length of Ques Ids:'+str(len(quesIds)))
    total_marks = 10*int(len(quesIds))
    print('Total marks:'+str(total_marks))
    testDet = TestDetails.query.filter_by(test_id=testId.test_id).first()
    # db.session.add(testDet)
    testDet.total_marks = total_marks
    db.session.commit()
        # testId = "select max(test_id) as test_id from test_details"
        # testId = db.session.execute(text(testId)).first()
    # courseTopic = ''
    # if courseId:
    #     courseTopic = CourseTopics(course_id=courseId,topic_id=topicDet.topic_id,test_id=testDet.test_id,is_archived='N',last_modified_date=datetime.now())
    #     db.session.add(courseTopic)
    # else:
    #     courseTopic = CourseTopics(topic_id=topicDet.topic_id,test_id=testDet.test_id,is_archived='N',last_modified_date=datetime.now())
    #     db.session.add(courseTopic)
    # db.session.commit()
    if len(quesIds)!=0:
        for quesId in quesIds:
            print('QuesID:'+str(quesId))
            if quesId!='[' or quesId!=']':
                testQues = TestQuestions(test_id=testDet.test_id,question_id=quesId,is_archived='N',last_modified_date=datetime.now())
                db.session.add(testQues)
                db.session.commit()
            # quesDet = QuestionDetails.query.filter_by(question_id=quesId).first()
            # quesDet.topic_id=topicDet.topic_id
            
    
    return jsonify("1")



@app.route('/addCourseTopic',methods=['GET','POST'])
def addCourseTopic():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacherData.school_id).first()
    print('inside addCourseTopic')
    topicName = request.args.get('topicName')
    courseId = request.args.get('courseId')
    topicId = request.args.get('topicId')
    courId = request.args.get('courId')
    print('My course ID:'+str(courseId))
    print('selected topic id:'+str(topicId))
    print('courseId of selected topic:'+str(courId))
    
    

    if courId:
        quesIds = request.get_json()
        total_marks = 10*len(quesIds)
        print('Total marks:'+str(total_marks))
        testDet = TestDetails(board_id=board.board_id,school_id=teacherData.school_id,test_type='Practice Test',total_marks=total_marks,teacher_id=teacherData.teacher_id,date_of_creation=datetime.now(),last_modified_date=datetime.now())
        db.session.add(testDet)
        db.session.commit()
        testId = "select max(test_id) as test_id from test_details"
        testId = db.session.execute(text(testId)).first()

        if courId:
            myTestId = CourseTopics.query.filter_by(course_id=courseId,topic_id=topicId,is_archived='N').first()
            testID = CourseTopics.query.filter_by(course_id=courId,topic_id=topicId).first()
            questionIds = TestQuestions.query.filter_by(test_id=testID.test_id).all()
            print(questionIds)
            for q in questionIds:
                print('Question ID:'+str(q.question_id))
                print('test id in which question stored:'+str(testId.test_id))
                Questions = TestQuestions(test_id=testId.test_id,question_id=q.question_id,is_archived='N',last_modified_date=datetime.now())
                db.session.add(Questions)
                db.session.commit()
        courseTopic = ''
        if courseId:
            courseTopic = CourseTopics(course_id=courseId,topic_id=topicId,test_id=testId.test_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(courseTopic)
        else:
            courseTopic = CourseTopics(topic_id=topicId,test_id=testId.test_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(courseTopic)
        db.session.commit()
        for quesId in quesIds:
            print('QuesID:'+str(quesId))
            testQues = TestQuestions(test_id=testId.test_id,question_id=quesId,is_archived='N',last_modified_date=datetime.now())
            db.session.add(testQues)
        
            quesDet = QuestionDetails.query.filter_by(question_id=quesId).first()
            quesDet.topic_id=topicId
            db.session.commit()
        return jsonify(topicId)
    else:
        print('Topic name:'+str(topicName))
        print('courseId:'+str(courseId))
        quesIds = request.get_json()
        print(quesIds)
        # courseId = CourseDetail.query.filter_by(course_name=courseName,teacher_id=teacherData.teacher_id,school_id=teacherData.school_id).first()
        
        # for quesId in quesIds:
        #     print(quesId)
        topicDet = Topic(topic_name=topicName,chapter_name=topicName,board_id=board.board_id,teacher_id=teacherData.teacher_id)
        db.session.add(topicDet)
        db.session.commit()
        # topicId = "select max(topic_id) as topic_id from topic_detail"
        # topicId = db.session.execute(text(topicId)).first()
        
        topicTr = TopicTracker(school_id=teacherData.school_id,topic_id=topicDet.topic_id,is_covered='N',reteach_count=0,is_archived='N',last_modified_date=datetime.now())
        db.session.add(topicTr)
        db.session.commit()
        total_marks = 10*len(quesIds)
        print('Total marks:'+str(total_marks))
        testDet = TestDetails(board_id=board.board_id,school_id=teacherData.school_id,test_type='Practice Test',total_marks=total_marks,teacher_id=teacherData.teacher_id,date_of_creation=datetime.now(),last_modified_date=datetime.now())
        db.session.add(testDet)
        db.session.commit()
        # testId = "select max(test_id) as test_id from test_details"
        # testId = db.session.execute(text(testId)).first()
        courseTopic = ''
        if courseId:
            courseTopic = CourseTopics(course_id=courseId,topic_id=topicDet.topic_id,test_id=testDet.test_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(courseTopic)
        else:
            courseTopic = CourseTopics(topic_id=topicDet.topic_id,test_id=testDet.test_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(courseTopic)
        db.session.commit()
        if quesIds:
            for quesId in quesIds:
                testQues = TestQuestions(test_id=testDet.test_id,question_id=quesId,is_archived='N',last_modified_date=datetime.now())
                db.session.add(testQues)
                
                quesDet = QuestionDetails.query.filter_by(question_id=quesId).first()
                quesDet.topic_id=topicDet.topic_id
                db.session.commit()
        return jsonify(topicDet.topic_id)
    
@app.route('/fetchTickCorrect',methods=['GET','POST'])
def fetchTickCorrect():
    print('inside fetchTickCorrect')
    correctOpt = []
    topic_id = request.args.get('topic_id')
    print('TopicId:'+str(topic_id))
    # quesIdsList = TestQuestions.query.filter_by(topic_id=topic_id).all()
    quesList  = request.get_json()
    print('Question List:')
    print(quesList)
    for quesId in quesList:
        print('Question Id:'+str(quesId))
        corr = QuestionOptions.query.filter_by(question_id=quesId,is_correct='Y').first()
        correctOpt.append(str(corr.option_desc)+':'+str(quesId))
    return jsonify(correctOpt)

@app.route('/addRecording',methods=['GET','POST'])
def addRecording():
    topic_id = request.args.get('topic_id')
    course_id = request.args.get('course_id')
    videoRec = CourseTopics.query.filter_by(topic_id=topic_id,course_id=course_id).first()
    recordingURL = request.form.get('recordingURL')
    print('recording Url:'+str(recordingURL))
    videoRecordUrl = request.form.get('videoRecordUrl')
    print('video url:'+str(videoRecordUrl))
    
    print('video recording url:'+str(videoRecordUrl))
    if recordingURL:
        videoRec.video_class_url = recordingURL
    else:
        videoRec.video_class_url = videoRecordUrl
    db.session.commit()
    return jsonify("1")

@app.route('/updateNotes',methods=['GET','POST'])
def updateNotes():
    topicId = request.args.get('topic_id')
    notesName = request.form.getlist('notesName')
    notesURL = request.form.getlist('notesURL')
    videoNotesUrl = request.form.getlist('videoNotesUrl')
    print('topicId:'+str(topicId))
    # print('Notes name:'+str(notesName))  
    existNotes = "update topic_notes set is_archived='Y' where topic_id='"+str(topicId)+"' "
    existNotes = db.session.execute(text(existNotes))
    print('Length of notes url array:'+str(len(notesURL)))
    for i in range(len(notesName)):
        print('inside for loop:'+str(i))
        print('NotesName:'+str(notesName[i]))
        print('notesUrl:'+str(notesURL[i]))
        print('videoNotesUrl:'+str(videoNotesUrl[i]))
        print('index:'+str(i))
        if i!=0:
            if notesURL[i]:
                print('url not null')
                if notesName[i]:
                    print('notes name not null')
                    if notesURL[i]:
                        courseId = CourseTopics.query.filter_by(topic_id=topicId).first()
                        addNotes = TopicNotes(topic_id=topicId,course_id=courseId.course_id,notes_name=notesName[i],notes_url=notesURL[i],notes_type=226,is_archived='N',last_modified_date=datetime.now())
                        db.session.add(addNotes)
                        db.session.commit()
                    else:
                        return ""
                else:
                    return ""
            else:
                if notesName[i]: 
                    if videoNotesUrl[i]:
                        courseId = CourseTopics.query.filter_by(topic_id=topicId).first()
                        addNotes = TopicNotes(topic_id=topicId,course_id=courseId.course_id,notes_name=notesName[i],notes_url=videoNotesUrl[i],notes_type=226,is_archived='N',last_modified_date=datetime.now())
                        db.session.add(addNotes)
                        db.session.commit()
                    else:
                        return ""
                else:
                    return ""
    return jsonify("1")

@app.route('/addNotes',methods=['GET','POST'])
def addNotes():
    topicId = request.args.get('topic_id')
    notesName = request.form.getlist('notesName')
    notesURL = request.form.getlist('notesURL')
    videoNotesUrl = request.form.getlist('videoNotesUrl')
    print('topicId:'+str(topicId))
    print('Notes name:'+str(notesName))
    for i in range(len(notesName)):
        print('inside for loop:'+str(i))
        print('NotesName:'+str(notesName[i]))
        print('notesUrl:'+str(notesURL[i]))
        print('videoNotesUrl:'+str(videoNotesUrl[i]))
        print('index:'+str(i))
        if notesURL[i]:
            print('url not null')
            if notesName[i]:
                print('notes name not null')
                if notesURL[i]:
                    courseId = CourseTopics.query.filter_by(topic_id=topicId).first()
                    addNotes = TopicNotes(topic_id=topicId,course_id=courseId.course_id,notes_name=notesName[i],notes_url=notesURL[i],notes_type=226,is_archived='N',last_modified_date=datetime.now())
                    db.session.add(addNotes)
                    db.session.commit()
                else:
                    return ""
            else:
                return ""
        else:
            if notesName[i]: 
                if videoNotesUrl[i]:
                    print('inside when notes name and file uploaded')
                    courseId = CourseTopics.query.filter_by(topic_id=topicId).first()
                    addNotes = TopicNotes(topic_id=topicId,course_id=courseId.course_id,notes_name=notesName[i],notes_url=videoNotesUrl[i],notes_type=226,is_archived='N',last_modified_date=datetime.now())
                    db.session.add(addNotes)
                    db.session.commit()
                else:
                    return ""
            # return ""
            else:
                return ""
    return jsonify("1")

@app.route('/addNewQuestion',methods=['GET','POST'])
def addNewQuestion():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacherData.school_id).first()
    print('inside add question')
    corr = request.args.get('corr')
    ques = request.args.get('ques')
    opt1 = request.args.get('opt1')
    opt2 = request.args.get('opt2')
    opt3 = request.args.get('opt3')
    opt4 = request.args.get('opt4')
    print('question Desc:'+str(ques))
    print('option 1:'+str(opt1))
    print('option 2:'+str(opt2))
    print('option 3:'+str(opt3))
    print('option 4:'+str(opt4))
    print('correct option:'+str(corr))
    quesCreate = QuestionDetails(board_id=board.board_id,question_description=ques,question_type='MCQ1',suggested_weightage='10',is_private='N',archive_status='N')
    db.session.add(quesCreate)
    db.session.commit()
    for i in range(4):
        op = request.args.get('opt'+str(i+1))
        correctOption = ''
        if str(corr) == str(i+1):
            correctOption = 'Y'
        else:
            correctOption = 'N'
        option = ''
        if i==0:
            option = 'A'
        elif i==1:
            option = 'B'
        elif i==2:
            option = 'C'
        else:
            option = 'D'
        # ques_det = QuestionDetails.query.filter_by(board_id=board.board_id,question_description=ques,question_type='MCQ1',suggested_weightage='10',is_private='N',archive_status='N').first()
        options = QuestionOptions(option=option,is_correct=correctOption,option_desc=op,question_id=quesCreate.question_id,weightage='10',last_modified_date=datetime.now())
        db.session.add(options)
        db.session.commit()
    return jsonify(quesCreate.question_id)
    
@app.route('/fetchQuesList',methods=['GET','POST'])
def fetchQuesList():
    print('inside fetchQuesList')
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    quesList = request.get_json()
    indic = request.args.get('indic')
    print('questionIdList:')
    print(quesList)
    for ques in quesList:
        print('Question_id:')
        print(ques)
    if indic=='1':
        for quesId in quesList:
            quesDesc = QuestionDetails.query.filter_by(question_id=quesId).first()
            print(quesDesc.question_description)
            quesOptions = QuestionOptions.query.filter_by(question_id=quesId).all()
            op1=''
            op2=''
            op3=''
            op4=''
            optionList = []
            quesDetails = []
            corrOption = ''
            for options in quesOptions:
                print('Option Desc:'+str(options.option_desc))
                optionList.append(options.option_desc)
                if options.is_correct=='Y':
                    corrOption = options.option_desc
            for i in range(len(optionList)):
                if i==0:
                    op1=optionList[i]
                elif i==1:
                    op2=optionList[i]
                elif i==2:
                    op3=optionList[i]
                elif i==3:
                    op4=optionList[i]
        print('Question:'+str(quesDesc.question_description)+'op1:'+str(op1)+'op2:'+str(op2)+'op3:'+str(op3)+'op4:'+str(op4))
        quesDetails.append(str(quesDesc.question_description)+':'+str(op1)+':'+str(op2)+':'+str(op3)+':'+str(op4)+':'+str(corrOption))
    return jsonify([quesDetails])

@app.route('/saveAndPublishedCourse',methods=['GET','POST'])
def saveAndPublishedCourse():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #print('inside saveCourse')
    course = request.form.get('course')
    courseId = request.args.get('course_id')
    description = request.form.get('description')
    imageUrl = request.form.get('imageUrl')
    video_url = request.form.get('videoUrl')
    idealfor = request.args.get('idealfor')
    level = request.form.get('level')
    private = request.form.get('private')
    #print('Course name:'+str(course))
    #print('courseId:'+str(courseId))
    #print('description name:'+str(description))
    #print('Image Url:'+str(imageUrl))
    #print('Private:'+str(private))
    course_status = request.args.get('course_status')
    #print('course status:'+str(course_status))
    #
    #print('video_url :'+str(video_url))
    print('Ideal for:'+str(idealfor))
    #print('level:'+str(level))
    updateIndex=False
    levelId = MessageDetails.query.filter_by(description=level,category='Difficulty Level').first()
    courseDet = CourseDetail.query.filter_by(course_id=courseId,description=description,summary_url=video_url,
    teacher_id=teacherData.teacher_id,school_id=teacherData.school_id,ideal_for=idealfor,difficulty_level=levelId.msg_id).first()
    if courseDet:
        course_status_id = MessageDetails.query.filter_by(category='Course Status',description=course_status).first()
        courseDet.course_status=course_status_id.msg_id
        db.session.commit()
        print('returning from first')
        if app.config["MODE"]=="PROD":
            updateIndex = updateSearchIndex("send","saveCourse")
        if updateIndex==True:
            return jsonify("1")
        else:
            return jsonify("2")
    else:
        course_status_id = MessageDetails.query.filter_by(category='Course Status',description=course_status).first()
        courseDet = CourseDetail.query.filter_by(course_id=courseId).first()
        if private:
            print('if course status is private')
            courseDet.description=description
            courseDet.summary_url=video_url
            courseDet.teacher_id=teacherData.teacher_id
            courseDet.school_id=teacherData.school_id
            if idealfor:
                courseDet.ideal_for=idealfor
            courseDet.course_status=course_status_id.msg_id
            courseDet.is_private='Y'
            courseDet.image_url = imageUrl
            courseDet.is_archived = 'N'
            courseDet.difficulty_level=levelId.msg_id
        else:
            print('if course status is public')
            courseDet.description=description
            courseDet.summary_url=video_url
            courseDet.teacher_id=teacherData.teacher_id
            courseDet.school_id=teacherData.school_id
            if idealfor:
                courseDet.ideal_for=idealfor
            courseDet.course_status=course_status_id.msg_id
            courseDet.is_private='N'
            courseDet.image_url = imageUrl
            courseDet.is_archived = 'N'
            courseDet.difficulty_level=levelId.msg_id
        db.session.commit()
        updateIndex = updateSearchIndex("send","saveCourse")
        if updateIndex==True:
            return jsonify("1")
        else:
            return jsonify("2")



@app.route('/saveCourse',methods=['GET','POST'])
def saveCourse():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print('inside saveCourse')
    course = request.form.get('course')
    courseId = request.args.get('course_id')
    description = request.form.get('description')
    # setDate = request.form.get('setDate')
    # startTime = request.form.get('startTime')
    # endTime = request.form.get('endTime')
    # days = request.form.getlist('Days')
    imageUrl = ''
    imgUrl= request.form.get('imageUrl')
    if imgUrl!=None:
        imageUrl = imgUrl
    video_url = request.form.get('videoUrl')
    idealfor = request.args.get('idealfor')
    level = request.form.get('level')
    private = request.form.get('private')
    print('Course name:'+str(course))
    print('courseId:'+str(courseId))
    print('description name:'+str(description))
    print('Private:'+str(private))
    print('course Image:'+str(imageUrl))
    course_status = request.args.get('course_status')
    print('course status:'+str(course_status))
   
    print('video_url :'+str(video_url))
    print('Ideal for:'+str(idealfor))
    print('level:'+str(level))
    levelId = MessageDetails.query.filter_by(description=level,category='Difficulty Level').first()
    course_status_id = MessageDetails.query.filter_by(category='Course Status',description=course_status).first()
    courseDet = CourseDetail.query.filter_by(course_id=courseId).first()
    if private:
        print('if course status is private')
        courseDet.description=description
        courseDet.summary_url=video_url
        courseDet.teacher_id=teacherData.teacher_id
        courseDet.school_id=teacherData.school_id
        if idealfor:
            courseDet.ideal_for=idealfor
        courseDet.course_status=course_status_id.msg_id
        courseDet.is_private='Y'
        courseDet.image_url = imageUrl
        courseDet.is_archived = 'N'
        courseDet.difficulty_level=levelId.msg_id
    else:
        print('if course status is public')
        courseDet.description=description
        courseDet.summary_url=video_url
        courseDet.teacher_id=teacherData.teacher_id
        courseDet.school_id=teacherData.school_id
        if idealfor:
            courseDet.ideal_for=idealfor
        courseDet.course_status=course_status_id.msg_id
        courseDet.is_private='N'
        courseDet.image_url = imageUrl
        courseDet.is_archived = 'N'
        courseDet.difficulty_level=levelId.msg_id
    db.session.commit()
    print('course:'+str(course))
    print('Desc:'+str(description))
    print('url:'+str(video_url))
    print('teacher_id:'+str(teacherData.teacher_id))
    print('school_id:'+str(teacherData.school_id))
    print('idealfor:'+str(idealfor))
    print('course_status:'+str(course_status_id.msg_id))    
    return jsonify("1")

@app.route('/courseEntry',methods=['GET','POST'])
def courseEntry():
    course = request.args.get('course')
    course_id = "select max(course_id) as course_id from course_detail "
    course_id = db.session.execute(text(course_id)).first()
    courseDet = CourseDetail.query.filter_by(course_id=course_id.course_id).first()
    courseDet.course_name = course
    db.session.commit()
    # courseId = "select max(course_id) as course_id from course_detail"
    # courseId = db.session.execute(text(courseId)).first()
    return jsonify(courseDet.course_id)

    # return render_template('editCourse.html')


@app.route('/myCourses')
def myCourses():

    return render_template('myCourses.html')

@app.route('/paymentForm')
def paymentForm():    
    if current_user.is_authenticated:
        #if current_user.country==None:
        #    flash('Please update your profile before donating ')
        #    return jsonify(['2'])

        #qschool_id = request.args.get('school_id')
        amount =  request.args.get('amount') 
        qbatch_id = request.args.get('batch_id')                
        #amount =              #hard coded value
        #qbatch_id = 1               #hard coded value

        if amount=='other':
            amount = 0
        #donation_for = request.args.get('donation_for')
        #if donation_for =='' or donation_for=='undefined':            
        #    donation_for=24
        
        courseBatchData = CourseBatch.query.filter_by(batch_id = qbatch_id).first()
        courseDetailData =CourseDetail.query.filter_by(course_id=courseBatchData.course_id).first()
        schoolData = SchoolProfile.query.filter_by(school_id=courseDetailData.school_id).first() 
        print("this is the batch id: "+str(courseBatchData.batch_id))

        print("this is the course desc: "+str(courseDetailData.description))
        #New section added to handle different vendors     
        #if schoolData.curr_sub_charge_type== 41:
        #    schoolShare = 100-int(schoolData.curr_sub_charge)
        #    selfShare = schoolData.curr_sub_charge             
        #else:

        #every payment amout is to be split in the ratio 97:3 :: Tutor: allLearn
        schoolShare = 97
        selfShare = 3
        vendorData = [
            {
                "vendorId": schoolData.curr_vendor_id,
                "commission": 97 #int(schoolShare)
            }, 
            {
                "vendorId":"SELF",
                "commission":3 #int(selfShare)
            }
        ]

        #vendorData=    [{"vendorId":"VENDOR1","commission":30}, {"vendorId":"VENDOR2","commission":40}]        
        vendorData = json.dumps(vendorData, separators=(',', ':'))
        print(vendorData)
        vendorDataEncoded = base64.b64encode(vendorData.encode('utf-8')).decode('utf-8')
        print(vendorDataEncoded)
        #end of section

        note = "Enrollment transaction"   
        payer_name = current_user.first_name + ' ' + current_user.last_name

        messageData = "" #MessageDetails.query.filter_by(msg_id=payment_for).first()

        #Inserting new order and transaction detail in db

        transactionNewInsert = PaymentTransaction(amount=courseBatchData.course_batch_fee,note=note, 
            payer_user_id=current_user.id, payer_name=str(payer_name),payer_phone=current_user.phone, payer_email=current_user.email,
            school_id=courseDetailData.school_id, teacher_id=courseDetailData.teacher_id,batch_id=qbatch_id, trans_type=254, payment_for= 264, tran_status=256, date=datetime.today()) 
        db.session.add(transactionNewInsert)
        db.session.commit()

        #Fetching all required details for the form and signature creation

        #transactionData = PaymentTransaction.query.filter_by(payer_user_id=current_user.id).order_by(PaymentTransaction.date.desc()).first()
        transactionData  = transactionNewInsert
        orderId= str(transactionData.tran_id).zfill(9)
        print("#######order id: "+str(orderId))
        currency = transactionData.currency
        appId= app.config['ALLLEARN_CASHFREE_APP_ID']
        returnUrl = url_for('paymentResponse',_external=True)
        notifyUrl = url_for('notifyUrl',_external=True)
        return render_template('_paymentForm.html',courseDetailData=courseDetailData,courseBatchData=courseBatchData, vendorDataEncoded=vendorDataEncoded,messageData=messageData,notifyUrl=notifyUrl,returnUrl=returnUrl, schoolData=schoolData, appId=appId, orderId = orderId, amount = amount, orderCurrency = currency, orderNote = note, customerName = payer_name)
    else:
        flash('Please login to enroll')
        return jsonify(['1'])

@app.route('/freeEnrollment')
def freeEnrollment():
    if current_user.is_authenticated:
        batch_id = request.args.get('batch_id')
        courseBatchData = CourseBatch.query.filter_by(batch_id =batch_id , is_archived='N').first()
        courseBatchData.students_enrolled = int(courseBatchData.students_enrolled) + 1
        courseEnrollmentData = CourseEnrollment(course_id= courseBatchData.course_id, 
            batch_id = batch_id, student_user_id=current_user.id, is_archived='N', 
            last_modified_date = datetime.today())   
        db.session.add(courseEnrollmentData)
        db.session.commit()
        flash('Course Enrolled')
        return jsonify(['0'])
    else:
        flash('Please login to enroll')
        return jsonify(['1'])


@app.route('/request', methods=["POST"])
def handlerequest():
    mode = app.config["MODE"] # <-------Change to TEST for test server, PROD for production
    platformSub = request.args.get('platformSub')
    if platformSub=="1":
        postData = {
            "appId" : request.form['appId'], 
            "orderId" : request.form['orderId'], 
            "orderAmount" : request.form['orderAmount'], 
            "orderCurrency" : request.form['orderCurrency'], 
            "orderNote" : request.form['orderNote'], 
            "customerName" : request.form['customerName'], 
            "customerPhone" : request.form['customerPhone'], 
            "customerEmail" : request.form['customerEmail'], 
            "returnUrl" : request.form['returnUrl'], 
            "notifyUrl" : request.form['notifyUrl'],
        }
    else:
        postData = {
            "appId" : request.form['appId'], 
            "orderId" : request.form['orderId'], 
            "orderAmount" : request.form['orderAmount'], 
            "orderCurrency" : request.form['orderCurrency'], 
            "orderNote" : request.form['orderNote'], 
            "customerName" : request.form['customerName'], 
            "customerPhone" : request.form['customerPhone'], 
            "customerEmail" : request.form['customerEmail'], 
            "returnUrl" : request.form['returnUrl'], 
            "notifyUrl" : request.form['notifyUrl'],
            "vendorSplit" : request.form['vendorSplit']
        }
    #vendorSplit = request.form['vendorSplit']
    sortedKeys = sorted(postData)
    signatureData = ""
    for key in sortedKeys:
      signatureData += key+postData[key]
    message = signatureData.encode('utf-8')
    #get secret key from config
    secret = app.config['ALLLEARN_CASHFREE_SECRET_KEY'].encode('utf-8')
    signature = base64.b64encode(hmac.new(secret,message,digestmod=hashlib.sha256).digest()).decode("utf-8")   
            
    transactionData = PaymentTransaction.query.filter_by(payer_user_id=current_user.id).order_by(PaymentTransaction.date.desc()).first()
    transactionData.order_id=postData["orderId"]
    #transactionData.anonymous_donor = anonymous_donor
    #transactionData.anonymous_amount = hide_amount
    transactionData.tran_status = 257 
    transactionData.request_sign_hash = signature
    transactionData.amount = postData["orderAmount"]

    #updating user phone number
    if current_user.phone==None or current_user.phone=="":
        userDataUpdate = User.query.filter_by(id=current_user.id).first()
        userDataUpdate.phone = request.form['customerPhone']
    db.session.commit()

    if mode == 'PROD': 
      url = "https://www.cashfree.com/checkout/post/submit"
    else: 
      url = "https://test.cashfree.com/billpay/checkout/post/submit"
    return render_template('request.html', postData = postData,signature = signature,url = url, platformSub=platformSub)


#this is the page after response from payment gateway
@app.route('/paymentResponse', methods=["POST"])
def paymentResponse():
    payment = request.args.get('payment')

    postData = {
    "orderId" : request.form['orderId'], 
    "orderAmount" : request.form['orderAmount'], 
    "referenceId" : request.form['referenceId'], 
    "txStatus" : request.form['txStatus'], 
    "paymentMode" : request.form['paymentMode'], 
    "txMsg" : request.form['txMsg'], 
    "signature" : request.form['signature'], 
    "txTime" : request.form['txTime']
    }

    signatureData = ""
    signatureData = postData['orderId'] + postData['orderAmount'] + postData['referenceId'] + postData['txStatus'] + postData['paymentMode'] + postData['txMsg'] + postData['txTime']

    message = signatureData.encode('utf-8')
    # get secret key from your config
    secret = app.config['ALLLEARN_CASHFREE_SECRET_KEY'].encode('utf-8')
    computedsignature = base64.b64encode(hmac.new(secret,message,digestmod=hashlib.sha256).digest()).decode('utf-8')   
    print("####this is the txStatus: "+str(postData["txStatus"]))
    messageData = MessageDetails.query.filter_by(description = postData["txStatus"]).first()

    #updating response transaction details into the DB
    transactionData = PaymentTransaction.query.filter_by(order_id=postData["orderId"]).first()
    currency = transactionData.currency
 
    transactionData.gateway_ref_id = postData["referenceId"]
    if transactionData.tran_status!=263:
        transactionData.tran_status = messageData.msg_id
    transactionData.payment_mode = postData["paymentMode"]
    transactionData.tran_msg = postData["txMsg"]
    transactionData.tran_time = postData["txTime"]
    transactionData.response_sign_hash = postData["signature"]
    if postData["signature"]==computedsignature:
        transactionData.response_sign_check="Matched"
    else:
        transactionData.response_sign_check="Not Matched"
    schoolData = SchoolProfile.query.filter_by(school_id=transactionData.school_id).first()
    if payment!='sub':
        #updating school data
        if transactionData.tran_status==258 or transactionData.tran_status==263:
            courseBatchData = CourseBatch.query.filter_by(batch_id = transactionData.batch_id, is_archived='N').first()
            if courseBatchData!=None:
                courseBatchData.total_fee_received = int(courseBatchData.total_fee_received)  + int(transactionData.amount)
                courseBatchData.students_enrolled = int(courseBatchData.students_enrolled) + 1

                courseEnrollmentData = CourseEnrollment(course_id= courseBatchData.course_id, batch_id = transactionData.batch_id, student_user_id=current_user.id, is_archived='N', 
                    last_modified_date = datetime.today())   
                db.session.add(courseEnrollmentData)
                courseDataQuery = "select course_id, course_name, tp.teacher_id, teacher_name from course_detail cd"
                courseDataQuery = courseDataQuery + " inner join teacher_profile tp on tp.teacher_id=cd.teacher_id"
                courseDataQuery = courseDataQuery + " and course_id="+ str(courseBatchData.course_id) 
                courseData = db.session.execute(courseDataQuery).first()
    db.session.commit()

    return render_template('paymentResponse.html',courseData=courseData, courseBatchData=courseBatchData,transactionData = transactionData,payment=payment,postData=postData,computedsignature=computedsignature, schoolData=schoolData,currency=currency)




@app.route('/notifyUrl',methods=["POST"])
def notifyUrl():
    postData = {
      "orderId" : request.form['orderId'], 
      "orderAmount" : request.form['orderAmount'], 
      "referenceId" : request.form['referenceId'], 
      "txStatus" : request.form['txStatus'], 
      "paymentMode" : request.form['paymentMode'], 
      "txMsg" : request.form['txMsg'], 
      "txTime" : request.form['txTime'], 
    }
    
    transactionData = Transaction.query.filter_by(order_id = postData["orderId"]).first()
    schoolData = SchoolProfile.query.filter_by(school_id=transactionData.school_id).first()
    if transactionData!=None:
        transactionData.tran_status = 263
        db.session.commit()        
        #donation_success_email_donor(schoolData.name, transactionData.donor_name,transactionData.donor_email,postData)
    else:
        print('############### no transaction detail found')
    return str(0)


def requestSignGenerator(appId, orderId, orderAmount, orderCurrency, orderNote, customerName, customerPhone,customerEmail, returnUrl, notifyUrl):    
    postData = {
      "appId" : appId,
      "orderId" : orderId,
      "orderAmount" : orderAmount,
      "orderCurrency" : orderCurrency,
      "orderNote" : orderNote,
      "customerName" : customerName,
      "customerPhone" : customerPhone,
      "customerEmail" : customerEmail,
      "returnUrl" : returnUrl,
      "notifyUrl" : notifyUrl
    }
    sortedKeys = sorted(postData)
    signatureData = ""
    for key in sortedKeys:
      signatureData += key+postData[key]

    message = bytes(signatureData,encoding='utf-8')
    #get secret key from your config
    secret = bytes(app.config['ALLLEARN_CASHFREE_SECRET_KEY'],encoding='utf-8')
    signature = base64.b64encode(hmac.new(secret, message,digestmod=hashlib.sha256).digest())
    return signature


def verifyResponseSign(receivedResponseSign, postData):
    signatureData = postData["orderId"] + postData["orderAmount"] + postData["referenceId"] + postData["txStatus"] + postData["paymentMode"] + postData["txMsg"] + postData["txTime"]
    message = bytes(signatureData).encode('utf-8')
    #get secret key from your config
    secret = bytes(app.config['ALLLEARN_CASHFREE_SECRET_KEY']).encode('utf-8')
    signature = base64.b64encode(hmac.new(secret, message,digestmod=hashlib.sha256).digest())
    if signature==receivedResponseSign:
        return True
    else:
        return False


##Routes to manage class notifications
@app.route('/classNotification')
def classNotification():    
    return render_template('classNotification.html')

@app.route('/sendClassNotification')
def sendClassNotification():
    upcomingClassStudentsQuery = "select *from public.user"  ##This query needs to be replaced with a new one
    upcomngClassStudentsData = db.session.execute(upcomingClassStudentsQuery).fetchall()
    ##This section to send email notifications
    for val in upcomngClassStudentsData:
        send_notification_email(val.email, val.first_name+ str(' ')+val.last_name, 'Course')
    return jsonify(['0'])
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
        #By default we're setting the user as course taker
        user = User(username=form.email.data, email=form.email.data, user_type='140', access_status='145', phone=form.phone.data,
            first_name = form.first_name.data,school_id=1,last_name= form.last_name.data)
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
                print('Email not registered')
                return redirect(url_for('login'))
        else: 
            user=User.query.filter_by(email=form.email.data).first()   
            try:             
                if user is None or not user.check_password(form.password.data):        
                    flash("Invalid email or password")
                    return redirect(url_for('login'))
            except:
                flash("Invalid email or password")
                return redirect(url_for('login'))

        #logging in the user with flask login
        try:
            login_user(user,remember=form.remember_me.data)
        except:
            flash("Invalid email or password")
            return redirect(url_for('login'))

        next_page = request.args.get('next')
        print('next_page',next_page)
        if not next_page or url_parse(next_page).netloc != '':
            print('if next_page is not empty',next_page)
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
        if current_user.user_type==253:
            school_id=1
        elif current_user.user_type==71:
            userProfileData = User.query.filter_by(id=current_user.id).first()
            school_id = userProfileData.school_id
        elif current_user.user_type==134:
            studentProfileData = StudentProfile.query.filter_by(user_id=current_user.id).first()
            school_id = studentProfileData.school_id            
            session['studentId'] = studentProfileData.student_id
        else:
            userData = User.query.filter_by(id=current_user.id).first()
            school_id = userData.school_id

        school_pro = SchoolProfile.query.filter_by(school_id=school_id).first()
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
            # print(det.module_name)
            # print(det.module_url)
            eachList.append(det.module_name)
            eachList.append(det.module_url)
            eachList.append(det.module_type)
            # detList.append(str(det.module_name)+":"+str(det.module_url)+":"+str(det.module_type))
            detList.append(eachList)
        session['moduleDet'] = detList
        # for each in session['moduleDet']:
        #     print('module_name'+str(each[0]))
        #     print('module_url'+str(each[1]))
        #     print('module_type'+str(each[2]))
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


@app.route('/privacyPolicy')
def privacyPolicy():
    return render_template('privacyPolicy.html')

@app.route('/sendUserNotificationEmail',methods=['POST','GET'])
def sendUserNotificationEmail():
    if request.method == 'POST':
        jsonData = request.json
        # jsonExamData = {"results": {"weightage": "10","topics": "1","subject": "1","question_count": "10","class_val": "3","uploadStatus":"Y","duration":"0","resultStatus":"Y","instructions":"","advance":"Y","negativeMarking":"0","test_type":"Class Feedback"},"custom_key": "custom_value","contact": {"phone": "9008262739"}}
        a = json.dumps(jsonData)
        z = json.loads(a)
        conList = []
        print('data:')
        for con in z['contact'].values():
            conList.append(con)
        print(conList)
        contactNo = conList[2]
        print('phone:'+str(contactNo))
        name = conList[1]
        print('name:'+str(name))
        email = 'contact@alllearn.in'
        email2 = 'paragsinha+w6uwk6zar1ell7m5oemd@boards.trello.com'
        notificationEmail(email,email2,name,contactNo)
        return jsonify({'phone':contactNo,'name':name})

@app.route('/sendNotificationEmail')
def sendNotificationEmail():
    student_id=request.args.get('student_id')
    resp_session_id = request.args.get('resp_session_id')
    userId = User.query.filter_by(id=current_user.id).first()
    school = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    school_id = school.school_id
    adminEmail=db.session.execute(text("select t2.email,t2.full_name,t1.school_name from school_profile t1 inner join student_profile t2 on t1.school_id=t2.school_id where t1.school_id='"+str(school_id)+"' and t2.student_id='"+str(student_id)+"'")).first()
    testDate = SessionDetail.query.filter_by(resp_session_id=resp_session_id).first()
    respCapture = ResponseCapture.query.filter_by(resp_session_id=resp_session_id).first()
    subject = MessageDetails.query.filter_by(msg_id=respCapture.subject_id).first()
    testType = TestDetails.query.filter_by(test_id=testDate.test_id).first()
    print('Test Type:'+str(testType.test_type))
    print('Response_session_id:'+str(resp_session_id))
    print('Student_id:'+str(student_id))
    if adminEmail!=None:
        test_report_email(adminEmail.email,adminEmail.full_name, adminEmail.school_name,school_id,testDate.last_modified_date,testType.test_type,resp_session_id,student_id,subject.description)
        return jsonify(["0"])
    else:
        return jsonify(["1"])

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
    indic='DashBoard'
    return render_template('syllabus.html',indic=indic,title='Syllabus',generalBoard=generalBoard,boardRowsId = boardRows.msg_id , boardRows=boardRows.description,subjectValues=subjectValues,school_name=school_id.school_name,classValues=classValues,classValuesGeneral=classValuesGeneral,bookName=bookName,chapterNum=chapterNum,topicId=topicId,fromSchoolRegistration=fromSchoolRegistration,user_type_val=str(current_user.user_type))


@app.route('/grantSchoolAdminAccess')
def grantSchoolAdminAccess():
    school_id=request.args.get('school_id')
    teacher_id=request.args.get('teacher_id')
    schoolTableDetails = SchoolProfile.query.filter_by(school_id=school_id).first()
    schoolTableDetails.school_admin=teacher_id
    db.session.commit()
    return jsonify(["String"])

@app.route('/grantSchoolAccess')
def grantSchoolAccess():
    username=request.args.get('username')    
    school_id=request.args.get('school_id')
    school=schoolNameVal()
    print("we're in grant access request. ")
    userTableDetails = User.query.filter_by(username=username).first()
    print("#######User Type: "+ str(userTableDetails.user_type))
    SchoolDetailData = SchoolProfile.query.filter_by(school_id=userTableDetails.school_id).first()
    if SchoolDetailData:
        print('if checkSchoolProfile not none')
        print('checkSchoolProfile.is_veirfied:'+str(SchoolDetailData.is_verified))
        print('checkSchoolProfile.school_id'+str(SchoolDetailData.school_id))
        SchoolDetailData.is_verified = 'Y'
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
        if checkTeacherProfile:
            print('if checkTeacherProfile not none')
            checkSchoolProfile = SchoolProfile.query.filter_by(school_id=checkTeacherProfile.school_id).first()
            if checkSchoolProfile:
                print('if checkSchoolProfile not none')
                print('checkSchoolProfile.is_veirfied:'+str(checkSchoolProfile.is_verified))
                print('checkSchoolProfile.school_id'+str(checkSchoolProfile.school_id))
                checkSchoolProfile.is_verified = 'Y'
                db.session.commit()
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

@app.route('/findSection',methods=['GET','POST'])
def findSection():
    class_val=request.args.get('class_val')
    school_id = User.query.filter_by(id=current_user.id).first()
    print('Class:'+str(class_val))
    print('School Id:'+str(school_id.school_id))
    sections = ClassSection.query.filter_by(school_id=school_id.school_id,class_val=class_val)
    sec = []
    for section in sections:
        sec.append(section.section)
    return jsonify(sec)

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

@app.route('/sendSMS',methods=["GET","POST"])
def sendSMS():
        # commType = request.form.get('commType')
    commType = 'sms'
    message = request.args.get('message')
    student_id = request.args.get('student_id')
    print('Message:'+str(message))
    print('student_id:'+str(student_id))
    class_sec = StudentProfile.query.filter_by(student_id=student_id).first()
    class_sec_id = class_sec.class_sec_id
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

@app.route('/fetchStudentTestReport', methods=['GET','POST'])
def fetchStudentTestReport():
    student_id = request.args.get('student_id')
    print('Student Id:'+str(student_id))
    testHistoryQuery = "SELECT *FROM fn_student_performance_response_capture("+str(student_id)+") order by test_date desc limit 50"
    testHistory = db.session.execute(testHistoryQuery).fetchall()
    testResData = []
    for test in testHistory:
        testData = {}
        testData['subject'] = test.subject
        testData['topics'] = test.topics
        testData['test_date'] = test.test_date.strftime('%d %B %Y')
        testData['perf_percentage'] = test.perf_percentage
        testData['resp_session_id'] = test.resp_session_id
        testResData.append(testData)
    print('Test Res Data:')
    print(testResData)
    return jsonify({'testResult':testResData})

@app.route('/feedbackCollectionStudDev', methods=['GET', 'POST'])
def feedbackCollectionStudDev():
    resp_session_id=request.args.get('resp_session_id')
    print('inside feedbackCollectionStudDev')
    print('Resp_session_id:'+str(resp_session_id))
    instructionsRows = SessionDetail.query.filter_by(resp_session_id=resp_session_id).first()
    if instructionsRows:
        instructions = instructionsRows.instructions
    else:
        instructions = ''
    student_id = request.args.get('student_id')
    school_id = request.args.get('school_id')
    uploadStatus=request.args.get('uploadStatus')
    resultStatus = request.args.get('resultStatus')
    advance = request.args.get('advance')
    print('upload status:'+str(uploadStatus))
    print('result status:'+str(resultStatus))
    print('advance:'+str(advance))
    print('Student Id:'+str(student_id))
    studId = None
    if student_id!=None:
        studId=student_id
    if current_user.is_anonymous:
        print('user not registered')
    else:
        studentDetails = StudentProfile.query.filter_by(user_id=current_user.id).first()
        studId = studentDetails.student_id

    if studId==None:
        print('Student Id is null')
        return render_template('feedbackCollectionStudDev.html',resp_session_id=str(resp_session_id),studId=studId,uploadStatus=uploadStatus,resultStatus=resultStatus,advance=advance)
    emailDet = StudentProfile.query.filter_by(student_id=studId).first()
    user = ''
    if emailDet:
        user = User.query.filter_by(email=emailDet.email).first()
    if user:
        login_user(user,remember='Y')
        session['schoolName'] = schoolNameVal()
        
        print('user name')
        #print(session['username'])
        school_id = ''
        print('user type')
        #print(session['userType'])
        session['studentId'] = ''
        if current_user.user_type==253:
            school_id=1
        elif current_user.user_type==71:
            teacherProfileData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
            school_id = teacherProfileData.school_id
        elif current_user.user_type==134:
            studentProfileData = StudentProfile.query.filter_by(user_id=current_user.id).first()
            school_id = studentProfileData.school_id            
            session['studentId'] = studentProfileData.student_id
        else:
            userData = User.query.filter_by(id=current_user.id).first()
            school_id = userData.school_id

        school_pro = SchoolProfile.query.filter_by(school_id=school_id).first()
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
    else:
        flash('please create student account first')
        return render_template('feedbackCollectionStudDev.html',resp_session_id=str(resp_session_id),studId=None)

    print('student_id in feedbackCollectionStudDev:'+str(studId))
    print('Response Session Id:'+str(resp_session_id))
    studentRow = StudentProfile.query.filter_by(student_id=studId).first()
    classData = ClassSection.query.filter_by(class_sec_id=studentRow.class_sec_id).first()
    sessionDetailRow = SessionDetail.query.filter_by(resp_session_id=str(resp_session_id)).first()
    print('Session Detail Row:'+str(sessionDetailRow))
    if sessionDetailRow==None:
        print('Response Session id is wrong')
        flash('please enter correct test id')
        return render_template('qrSessionScannerStudent.html',user_type_val=str(current_user.user_type),studentDetails=studentRow)
    testDet = TestDetails.query.filter_by(test_id=sessionDetailRow.test_id).first()
    print('Test of Class:'+str(testDet.class_val))
    print('Student of class:'+str(classData.class_val))
    responseExist = "select rc.student_id,sd.test_id from response_capture rc inner join session_detail sd on rc.resp_session_id = sd.resp_session_id where sd.resp_session_id='"+str(resp_session_id)+"' and rc.student_id='"+str(studId)+" '"
    responseExist = db.session.execute(text(responseExist)).first()
    
    if responseExist:
        print('Inside if test already attempt')
        flash('Sorry, you have already attempt this test')
        studenId = None
        return render_template('feedbackCollectionStudDev.html',resp_session_id=str(resp_session_id),studId=studenId)
    if((str(testDet.class_val)!=str(classData.class_val)) and (school_id==classData.school_id)):
        print('Inside if classes are same')
        flash('Sorry, you can not attempt this test')
        studenId = None
        return render_template('feedbackCollectionStudDev.html',resp_session_id=str(resp_session_id),studId=studenId)
    if sessionDetailRow!=None:
        print("This is the session status - "+str(sessionDetailRow.session_status))
        if sessionDetailRow.session_status=='80':
            sessionDetailRow.session_status='81'        
            db.session.commit()    
        classSectionRow = ClassSection.query.filter_by(class_sec_id=sessionDetailRow.class_sec_id).first()        
        testDetailRow = TestDetails.query.filter_by(test_id = sessionDetailRow.test_id).first()
        testQuestions = TestQuestions.query.filter_by(test_id=sessionDetailRow.test_id,is_archived='N').all()

        if testQuestions!=None:
            questionListSize = len(testQuestions)
        print('Student ID:'+str(studentRow.student_id))
        return render_template('feedbackCollectionStudDev.html',class_val = classSectionRow.class_val, 
            section=classSectionRow.section,questionListSize=questionListSize,
            resp_session_id=str(resp_session_id), questionList=testQuestions, subject_id=testDetailRow.subject_id, test_type=testDetailRow.test_type,disconn=1,student_id = studId,studentName=studentRow.full_name,uploadStatus=uploadStatus,resultStatus=resultStatus,advance=advance,instructions=instructions)
    else:
        flash('This is not a valid id or there are no question in this test')
        return redirect('index')
        #return render_template('qrSessionScannerStudent.html',disconn=1)

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
@login_required
def leaderBoard():
    form = LeaderBoardQueryForm()
    qclass_val = request.args.get("class_val")
    print('Class:'+str(qclass_val))
    #print('class:'+str(qclass_val))
    if current_user.is_authenticated:        
        user = User.query.filter_by(username=current_user.username).first_or_404()
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first() 
        distinctClasses = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacher_id.school_id)+" GROUP BY class_val order by s")).fetchall()    
        form.subject_name.choices = [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
        class_sec_id=ClassSection.query.filter_by(class_val='1',school_id=teacher_id.school_id).first()
        form.test_type.choices= [(i.description,i.description) for i in MessageDetails.query.filter_by(category='Test type').all()]

        # form.testdate.choices = [(i.exam_date,i.exam_date) for i in ResultUpload.query.filter_by(class_sec_id=class_sec_id.class_sec_id).all()]
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
            indic='leaderBoard'
            return render_template('leaderBoard.html',indic=indic,title='Leaderboard',classSecCheckVal=classSecCheckVal,form=form,distinctClasses=distinctClasses,leaderBoardData=leaderBoardData,colAll=colAll,columnNames=columnNames, qclass_val=qclass_val,subject=subj,subColumn=subColumn,subHeader=subHeader,user_type_val=str(current_user.user_type))

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
            indic='leaderBoard'
            return render_template('leaderBoard.html',indic=indic,title='Leaderboard',classSecCheckVal=classSecCheckVal,form=form,distinctClasses=distinctClasses,leaderBoardData=data,colAll=colAll,columnNames=columnNames, qclass_val=qclass_val,subject=subj,subColumn=subColumn,subHeader=subHeader,user_type_val=str(current_user.user_type))
    # classSecCheckVal=''
    indic='leaderBoard'
    return render_template('leaderBoard.html',indic=indic,title='Leaderboard',classSecCheckVal=classSecCheckVal,form=form,distinctClasses=distinctClasses,leaderBoardData=data,colAll=colAll,columnNames=columnNames, qclass_val=qclass_val,subject=subj,subColumn=subColumn,subHeader=subHeader,user_type_val=str(current_user.user_type))

# API for existed Test Paper and Test Link Generation
@app.route('/existedTestPaperLinkGenerate',methods=['POST'])
def existedTestPaperLinkGenerate():
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    school_id=teacher_id.school_id
    print('SchoolId:',school_id)
    uploadStatus=request.args.get('uploadStatus')
    duration = request.args.get('duration')
    if duration =='':
        duration = 0
    print('Duration:'+str(duration))
    if uploadStatus=='' or uploadStatus==None:
        uploadStatus = 'Y'
    resultStatus = request.args.get('resultStatus')
    if resultStatus=='' or resultStatus==None:
        resultStatus = 'Y'
    instructions = request.args.get('instructions')

    advance = request.args.get('advance')
    if advance=='' or advance==None:
        advance = 'Y'
    weightage = request.args.get('weightage')
    if weightage=='' or weightage==None:
        weightage = 10
    NegMarking = request.args.get('negativeMarking')
    if NegMarking=='' or NegMarking==None:
        NegMarking = 0
    testId = request.args.get('test_id')
    testPaperLinkQuery = TestDetails.query.filter_by(test_id=testId).first()
    test_paper_link = testPaperLinkQuery.test_paper_link
    selectOption = request.args.get('selectOption')
    print('SelectOption:'+str(selectOption))
    currClassSecRow=ClassSection.query.filter_by(school_id=str(testPaperLinkQuery.school_id),class_val=str(testPaperLinkQuery.class_val).strip()).first()
    resp_session_id = str(testPaperLinkQuery.subject_id).strip()+ str(datetime.today().strftime("%d%m%Y%H%M%S")).strip() + str(currClassSecRow.class_sec_id).strip()
    if selectOption=='0':
        print('download test paper')
        return jsonify({'testPaperLink':test_paper_link})
    elif selectOption=='1':
        print('test link generate')
        linkForTeacher=url_for('testLinkWhatsappBoot',resp_session_id=resp_session_id,test_id=testId,weightage=weightage,negativeMarking=NegMarking,uploadStatus=uploadStatus,resultStatus=resultStatus,advance=advance,instructions=instructions,duration=duration,class_val=testPaperLinkQuery.class_val,section=currClassSecRow.section,subject_id=testPaperLinkQuery.subject_id, _external=True)
        linkForStudent=url_for('feedbackCollectionStudDev',resp_session_id=resp_session_id,school_id=testPaperLinkQuery.school_id,uploadStatus=uploadStatus,resultStatus=resultStatus,advance=advance, _external=True)
        return jsonify({'onlineTestLinkForTeacher':linkForTeacher,'onlineTestLinkForStudent':linkForStudent})
    else:
        print('test link generate and download paper')
        linkForTeacher=url_for('testLinkWhatsappBoot',resp_session_id=resp_session_id,test_id=testId,weightage=weightage,negativeMarking=NegMarking,uploadStatus=uploadStatus,resultStatus=resultStatus,advance=advance,instructions=instructions,duration=duration,class_val=testPaperLinkQuery.class_val,section=currClassSecRow.section,subject_id=testPaperLinkQuery.subject_id, _external=True)
        linkForStudent=url_for('feedbackCollectionStudDev',resp_session_id=resp_session_id,school_id=testPaperLinkQuery.school_id,uploadStatus=uploadStatus,resultStatus=resultStatus,advance=advance, _external=True)
        return jsonify({'testPaperLink':test_paper_link,'onlineTestLinkForTeacher':linkForTeacher,'onlineTestLinkForStudent':linkForStudent})

# Start API
@app.route('/testApp',methods=['POST'])
def testApp():
    if request.method == 'POST':
        jsonExamData = request.json
        a = json.dumps(jsonExamData)
        z = json.loads(a)
        paramList = []
        conList = []
        for data in z['results'].values():
            paramList.append(data)
        for con in z['contact'].values():
            conList.append(con)
        testIDQuery = TestDetails.query.filter_by(test_id=paramList[0]).first()
        subjectQuery = MessageDetails.query.filter_by(msg_id=testIDQuery.subject_id).first()
        userId = User.query.filter_by(phone=conList[0]).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
        print('Test ID:'+str(paramList[0]))
        quesIdQuery = TestQuestions.query.filter_by(test_id=paramList[0]).all()
        document = Document()
        document.add_heading(schoolNameVal(), 0)
        document.add_heading('Class '+str(testIDQuery.class_val)+" - "+str(testIDQuery.test_type)+" - "+str(datetime.today().strftime("%d%m%Y%H%M%S")) , 1)
        document.add_heading("Subject : "+str(subjectQuery.description),2)
        document.add_heading("Total Marks : "+str(testIDQuery.total_marks),3)
        p = document.add_paragraph()
        for question in quesIdQuery:
            data=QuestionDetails.query.filter_by(question_id=int(question.question_id), archive_status='N').first()
            options=QuestionOptions.query.filter_by(question_id=data.question_id).all()
            #add question desc
            document.add_paragraph(
                data.question_description, style='List Number'
            )    
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
        cl = testIDQuery.class_val.replace("/","-")
        file_name=str(teacher_id.school_id)+str(cl)+str(subjectQuery.description)+str(testIDQuery.test_type)+str(datetime.today().strftime("%Y%m%d"))+str(testIDQuery.total_marks)+'.docx'
   
        if not os.path.exists('tempdocx'):
            os.mkdir('tempdocx')
        document.save('tempdocx/'+file_name.replace(" ", ""))
        #uploading to s3 bucket
        client = boto3.client('s3', region_name='ap-south-1')
        client.upload_file('tempdocx/'+file_name.replace(" ", "") , os.environ.get('S3_BUCKET_NAME'), 'test_papers/{}'.format(file_name.replace(" ", "")),ExtraArgs={'ACL':'public-read'})
        #deleting file from temporary location after upload to s3
        os.remove('tempdocx/'+file_name.replace(" ", ""))
        file_name_val='https://'+os.environ.get('S3_BUCKET_NAME')+'.s3.ap-south-1.amazonaws.com/test_papers/'+file_name.replace(" ", "")
        print('Test Created successfully:'+str(file_name_val))
    return jsonify({'fileName':file_name_val})

#End API

def insertData(class_sec_id,resp_session_id,question_ids,test_type,total_marks,class_val,teacher_id,school_id):
    with app.app_context():
        print('inside insertData')
        subjId = ''
        topicID = ''
        boardID = ''
        print('question_ids:')
        print(question_ids)
        for det in question_ids:
            subjId = det.subject_id
            topicID = det.topic_id
            boardID = det.board_id
            break
        format = "%Y-%m-%d %H:%M:%S"
        schoolQuery = SchoolProfile.query.filter_by(school_id=school_id).first()
        schoolName = schoolQuery.school_name
        now_utc = datetime.now(timezone('UTC'))
        now_local = now_utc.astimezone(get_localzone())
        print('Date of test creation:'+str(now_local.strftime(format)))
        subjectQuery = MessageDetails.query.filter_by(msg_id=subjId).first()
        document = Document()
        document.add_heading(schoolName, 0)
        document.add_heading('Class '+str(class_val)+" - "+str(test_type)+" - "+str(datetime.today().strftime("%d%m%Y%H%M%S")) , 1)
        document.add_heading("Subject : "+str(subjectQuery.description),2)
        document.add_heading("Total Marks : "+str(total_marks),3)
        p = document.add_paragraph()
        for question in question_ids:
            data=QuestionDetails.query.filter_by(question_id=int(question.question_id), archive_status='N').first()
            options=QuestionOptions.query.filter_by(question_id=data.question_id).all()
            #add question desc
            document.add_paragraph(
                data.question_description, style='List Number'
            )    
            print(data.reference_link)
            if data.reference_link!='' or data.reference_link!=None:
                print('inside threadUse if ')
                print(data.reference_link)
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
        cl = class_val.replace("/","-")
        file_name=str(school_id)+str(cl)+str(subjectQuery.description)+str(test_type)+str(datetime.today().strftime("%Y%m%d"))+str(total_marks)+'.docx'
   
        if not os.path.exists('tempdocx'):
            os.mkdir('tempdocx')
        document.save('tempdocx/'+file_name.replace(" ", ""))
        #uploading to s3 bucket
        client = boto3.client('s3', region_name='ap-south-1')
        client.upload_file('tempdocx/'+file_name.replace(" ", "") , os.environ.get('S3_BUCKET_NAME'), 'test_papers/{}'.format(file_name.replace(" ", "")),ExtraArgs={'ACL':'public-read'})
        #deleting file from temporary location after upload to s3
        os.remove('tempdocx/'+file_name.replace(" ", ""))
        file_name_val='https://'+os.environ.get('S3_BUCKET_NAME')+'.s3.ap-south-1.amazonaws.com/test_papers/'+file_name.replace(" ", "")

        testDetailsUpd = TestDetails(test_type=str(test_type), total_marks=str(total_marks),last_modified_date= datetime.now(),
            board_id=str(boardID), subject_id=int(subjId),class_val=str(class_val),date_of_creation=now_local.strftime(format),
            date_of_test=datetime.now(),test_paper_link=file_name_val, school_id=school_id, teacher_id=teacher_id)
        db.session.add(testDetailsUpd)
        db.session.commit()
        sessionDetailRowInsert=SessionDetail(resp_session_id=resp_session_id,session_status='80',teacher_id= teacher_id,
            test_id=str(testDetailsUpd.test_id).strip(),class_sec_id=class_sec_id,correct_marks=10,incorrect_marks=0, test_time=0,total_marks=total_marks, last_modified_date = str(now_local.strftime(format)))
        db.session.add(sessionDetailRowInsert)
        for questionVal in question_ids:
            testQuestionInsert= TestQuestions(test_id=testDetailsUpd.test_id, question_id=questionVal.question_id, last_modified_date=datetime.now(),is_archived='N')
            db.session.add(testQuestionInsert)
        db.session.commit()
        print('after insertData')

def threadUse(class_sec_id,resp_session_id,question_ids,test_type,total_marks,class_val,teacher_id,school_id):
    print('Inside threadUse')
    Thread(target=insertData,args=(class_sec_id,resp_session_id,question_ids,test_type,total_marks,class_val,teacher_id,school_id)).start()
    

# API for New Test Paper Link and Test Link Generation

@app.route('/getLeaderBoardLink',methods=['GET','POST'])
@login_required
def getLeaderBoardLink():
    if request.method == 'POST':
        leaderBoardLink = url_for('leaderBoard', _external=True)
        return jsonify({'leaderboardLink':leaderBoardLink})

@app.route('/getCustomerSupportLink',methods=['GET','POST'])
@login_required
def getCustomerSupportLink():
    if request.method == 'POST':
        customerSupportLink = url_for('help',_external=True)
        return jsonify({'helpLink':customerSupportLink})

@app.route('/getTopicList',methods=['POST','GET'])
def getTopicList():
    if request.method == 'POST':
        print('inside getTopicList')
        jsonData = request.json
        # jsonData = {"contact": {"phone":"9008262739" },"results": {"class_val":"4","subject":"1","custom_key": "custom_value"}}
        data = json.dumps(jsonData)
        dataList = json.loads(data)
        conList = []
        selectedOptions = []
        for con in dataList['contact'].values():
            conList.append(con)
        print('Data Contact')
        # print(conList[2])
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
        classesListData = ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()
        classList = [] 
        j=1
        for classlist in classesListData:
            classVal = str(j)+str(' - ')+str(classlist.class_val)
            classList.append(classVal)
            j=j+1
        for clas in dataList['results'].values():
            selectedOptions.append(clas)
        selClass = ''
        selSubject = ''
        for className in classList:
            num = className.split('-')[0]
            print('num:'+str(num))
            print('class:'+str(selectedOptions[0]))
            if int(num) == int(selectedOptions[0]):
                print(className)
                selClass = className.split('-')[1]
                print('selClass:'+str(selClass))
        print('class')
        selClass = selClass.strip()
        print(selClass)
        subQuery = "select md.description as subject,md.msg_id from board_class_subject bcs inner join message_detail md on bcs.subject_id = md.msg_id where school_id='"+str(teacher_id.school_id)+"' and class_val = '"+str(selClass)+"'"
        print(subQuery)
        subjectData = db.session.execute(text(subQuery)).fetchall()
        print(subjectData)
        subjectList = []
        k=1
        subId = ''
        for subj in subjectData:
            sub = str(k)+str('-')+str(subj.subject)
            subjectList.append(sub)
            k=k+1
        for subjectName in subjectList:
            num = subjectName.split('-')[0]
            print('num:'+str(num))
            print('class:'+str(selectedOptions[1]))
            if int(num) == int(selectedOptions[1]):
                print(subjectName)
                selSubject = subjectName.split('-')[1]
                print('selSubject:'+str(selSubject))
                
        print('Subject:')
        selSubject = selSubject.strip()
        subQuery = MessageDetails.query.filter_by(description=selSubject).first()
        subId = subQuery.msg_id
        print(selSubject)
        print('SubId:'+str(subId))
        extractChapterQuery = "select td.chapter_name ,td.chapter_num ,bd.book_name from topic_detail td inner join book_details bd on td.book_id = bd.book_id where td.class_val = '"+str(selClass)+"' and td.subject_id = '"+str(subId)+"'"
        print('Query:'+str(extractChapterQuery))
        extractChapterData = db.session.execute(text(extractChapterQuery)).fetchall()
        print(extractChapterData)
        c=1
        chapterDetList = []
        for chapterDet in extractChapterData:
            if c==1:
                chap = str('Here’s the full list of chapters:\n')+str(c)+str('-')+str(chapterDet.chapter_name)+str('-')+str(chapterDet.book_name)+str("\n")
            else:
                chap = str(c)+str('-')+str(chapterDet.chapter_name)+str('-')+str(chapterDet.book_name)+str("\n")
            chapterDetList.append(chap)
            c=c+1
        msg = 'no topics available'
        if chapterDetList:
            return jsonify({'chapterDetList':chapterDetList})
        else:
            return jsonify({'chapterDetList':msg})


@app.route('/getSubjectsList',methods=['POST','GET'])
def getSubjectsList():
    if request.method == 'POST':
        print('inside getSubjectsList')
        jsonData = request.json
        # jsonData = {"contact": {"phone":"9008262739" },"results": {"class_val":"4","custom_key": "custom_value"}}
        data = json.dumps(jsonData)
        dataList = json.loads(data)
        
        conList = []
        selectedClassOption = []
        for con in dataList['contact'].values():
            conList.append(con)
        print('Data Contact')
        # print(conList[2])
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
        classesListData = ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()
        classList = [] 
        j=1
        for classlist in classesListData:
            classVal = str(j)+str(' - ')+str(classlist.class_val)
            classList.append(classVal)
            j=j+1
        for clas in dataList['results'].values():
            selectedClassOption.append(clas)
        selClass = ''
        print('Selected Class option:')
        print(selectedClassOption[0])
        for className in classList:
            num = className.split('-')[0]
            print('num:'+str(num))
            print('class:'+str(selectedClassOption[0]))
            if int(num) == int(selectedClassOption[0]):
                print(className)
                selClass = className.split('-')[1]
                print('selClass:'+str(selClass))
        print('class')
        selClass = selClass.strip()
        print(selClass)
        
        subQuery = "select md.description as subject from board_class_subject bcs inner join message_detail md on bcs.subject_id = md.msg_id where school_id='"+str(teacher_id.school_id)+"' and class_val = '"+str(selClass)+"'"
        print(subQuery)
        subjectData = db.session.execute(text(subQuery)).fetchall()
        print(subjectData)
        subjectList = []
        k=1
        for subj in subjectData:
            if k==1:
                sub = str('Which Subject?\n')+str(k)+str('-')+str(subj.subject)+str("\n")
            else:
                sub = str(k)+str('-')+str(subj.subject)+str("\n")
            subjectList.append(sub)
            k=k+1
        msg = 'no subjects available'
        if subjectList:
            return jsonify({'subject_list':subjectList}) 
        else:
            return jsonify({'subject_list':msg})

@app.route('/getStudentDetails',methods=['POST','GET'])
def getStudentDetails():
    if request.method == 'POST':
        print('inside getStudentDetails')
        jsonData = request.json
        data = json.dumps(jsonData)
        dataList = json.loads(data)
        selectedStudentOption = []
        for data in dataList['results'].values():
            selectedStudentOption.append(data)
        conList = []
        print('SelectedOption:'+str(selectedStudentOption))
        for con in dataList['contact'].values():
            conList.append(con)
        print(conList[2])
        print('Data Contact')
        # print(conList[2])
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
        classesListData = ClassSection.query.filter_by(school_id=teacher_id.school_id).all()
        classList = [] 
        j=1
        for classlist in classesListData:
            classVal = str(j)+str(' - ')+str(classlist.class_val)+str('-')+str(classlist.section)
            classList.append(classVal)
            j=j+1
        print(classList)
        selClass = ''
        selSection = ''
        for clas in classList:
            option = clas.split('-')[0]
            if int(option) == selectedStudentOption[1]:
                selClass = clas.split('-')[1]
                selSection = clas.split('-')[2]
        selClass = selClass.strip()
        selSection = selSection.strip()
        print('Class:'+str(selClass))
        print('Section:'+str(selSection))
        classSec = ClassSection.query.filter_by(class_val=selClass,section=selSection,school_id=teacher_id.school_id).first()
        classSecId = classSec.class_sec_id
        studentListQuery = StudentProfile.query.filter_by(school_id=teacher_id.school_id,class_sec_id=classSecId).all()
        l=1
        studentList = []
        for student in studentListQuery:
            stud = str(l)+str('-')+str(student.full_name)+str("-")+str(student.student_id)
            studentList.append(stud)
            l=l+1
        selStudentId = ''
        for stud in studentList:
            option = stud.split('-')[0]
            print(option)
            print(selectedStudentOption[0])
            if int(option) == int(selectedStudentOption[0]):
                print(stud)
                selStudentId = stud.split('-')[2]
        print('getStudentDetails student_id:'+str(selStudentId))
        studentDetailLink = url_for('studentProfile',student_id=selStudentId, _external=True)
        newLink = ''
        if studentDetailLink:
            newLink = str('Student Detail Link:\n')+str(studentDetailLink)
        if newLink:
            return jsonify({'studentDetailLink':newLink})
        else:
            msg = 'No students available'
            return jsonify({'studentDetailLink':msg})

@app.route('/getStudentsList',methods=['GET','POST'])
def getStudentsList():
    if request.method == 'POST':
        print('inside getStudentsList')
        jsonData = request.json
        data = json.dumps(jsonData)
        dataList = json.loads(data)
        conList = []
        for con in dataList['contact'].values():
            conList.append(con)
        print(conList[2])
        print('Data Contact')
        # print(conList[2])
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
        classesListData = ClassSection.query.filter_by(school_id=teacher_id.school_id).all()
        classList = [] 
        j=1
        for classlist in classesListData:
            classVal = str(j)+str(' - ')+str(classlist.class_val)+str('-')+str(classlist.section)
            classList.append(classVal)
            j=j+1
        print(classList)
        selectedClassOption = ''
        selClass = ''
        selSection = ''
        for data in dataList['results'].values():
            selectedClassOption = data
        for clas in classList:
            option = clas.split('-')[0]
            if int(option) == selectedClassOption:
                selClass = clas.split('-')[1]
                selSection = clas.split('-')[2]
        selClass = selClass.strip()
        selSection = selSection.strip()
        print('Class:'+str(selClass))
        print('Section:'+str(selSection))
        classSec = ClassSection.query.filter_by(class_val=selClass,section=selSection,school_id=teacher_id.school_id).first()
        classSecId = classSec.class_sec_id
        studentListQuery = StudentProfile.query.filter_by(school_id=teacher_id.school_id,class_sec_id=classSecId).all()
        l=1
        studentList = []
        for student in studentListQuery:
            if l==1:
                stud = str("Here's your students list:\n")+str(l)+str('-')+str(student.full_name)+str("\n")
            else:
                stud = str(l)+str('-')+str(student.full_name)+str("\n")
            studentList.append(stud)
            l=l+1
        msg = 'no students available'
        if studentList:
            return jsonify({'studentNewList':studentList})
        else:
            return jsonify({'studentNewList':msg})
    

@app.route('/getClassSectionList',methods=['POST','GET'])
def getClassSectionList():
    if request.method == 'POST':
        print('inside getClassSectionList')
        jsonData = request.json
        data = json.dumps(jsonData)
        dataList = json.loads(data)
        conList = []
        for con in dataList['contact'].values():
            conList.append(con)
        print('Data Contact')
        # print(conList[2])
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        teacher_id = ''
        if userId:
            teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
        else:
            Msg = 'you are not a registered user'
            return jsonify({'class_list':Msg})
        classesListData = ''
        if teacher_id:
            classesListData = ClassSection.query.filter_by(school_id=teacher_id.school_id).all()
        else:
            Msg = 'you are not a registered teacher'
            return jsonify({'class_list':Msg})
        
        classList = [] 
        j=1
        for classlist in classesListData:
            if j==1:
                classVal = str('Which class?\n')+str(j)+str(' - ')+str(classlist.class_val)+str('-')+str(classlist.section)+str("\n")
            else:
                classVal = str(j)+str(' - ')+str(classlist.class_val)+str('-')+str(classlist.section)+str("\n")
            classList.append(classVal)
            j=j+1
        print(classList)
        # return jsonify({'class_list':classList}) 
        msg = 'no classes available'
        if classList:
            return jsonify({'class_list':classList})
        else:
            return jsonify({'class_list':msg})

@app.route('/getClassList',methods=['POST','GET'])
def getClassList():
    if request.method == 'POST':
        print('inside getClassList')
        jsonData = request.json
        data = json.dumps(jsonData)
        dataList = json.loads(data)
        print('all data:')
        print(dataList)
        conList = []
        for con in dataList['contact'].values():
            conList.append(con)
        print('Data Contact')
        # print(conList[2])
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        teacher_id = ''
        if userId:
            print('you are registered user')
            teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
        else:
            Msg = 'you are not a registered user'
            return jsonify({'class_list':Msg})
        classesListData = ''
        if teacher_id:
            classesListData = ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()
        else:
            Msg = 'you are not a registered teacher'
            return jsonify({'class_list':Msg})
        
        classList = [] 
        j=1
        for classlist in classesListData:
            if j==1:
                classVal = str('Which class?\n')+str(j)+str(' - ')+str(classlist.class_val)+str("\n")
            else:
                classVal = str(j)+str(' - ')+str(classlist.class_val)+str("\n")
            classList.append(classVal)
            j=j+1
        print(classList)
        msg = 'no classes available'
        if classList:
            return jsonify({'class_list':classList})
        else:
            return jsonify({'class_list':msg})

# @app.route('/getReqTopicList',methods=['POST','GET'])
# def getReqTopicList():
#     if request.method == 'POST':
#         jsonData = request.json
#         a = json.dumps(jsonData)
#         data = json.loads(a)
#         for value in data['results'].values():
#             print(value)
#     dataValue = 10
#     return jsonify({'Data':dataValue})

@app.route('/getStudentPerformance',methods=['POST','GET'])
def getStudentPerformance():
    if request.method == 'POST':
        print('inside getStudentPerformance')
        jsonExamData = request.json
        a = json.dumps(jsonExamData)
        z = json.loads(a)
        conList = []
        for con in z['contact'].values():
            conList.append(con)
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        studentDetails = StudentProfile.query.filter_by(user_id=userId.id).first()
        emailDet = studentDetails.email
        if emailDet:
            user = User.query.filter_by(email=studentDetails.email).first()
        if user:
            login_user(user,remember='Y')
        link = url_for('studentProfile',student_id=studentDetails.student_id,_external=True)
        return jsonify({'studentProfile':link})

# @app.route('/getStudentDashboard',methods=['POST','GET'])
# def getStudentDashboard():
#     if request.method == 'POST':
#         print('inside getStudentDashboard')
#         jsonExamData = request.json
#         a = json.dumps(jsonExamData)
#         z = json.loads(a)
#         conList = []
#         for con in z['contact'].values():
#             conList.append(con)
#         contactNo = conList[2][-10:]
#         print(contactNo)
#         userId = User.query.filter_by(phone=contactNo).first()
#         studentDetails = StudentProfile.query.filter_by(user_id=userId.id).first()
#         emailDet = studentDetails.email
#         if emailDet:
#             user = User.query.filter_by(email=studentDetails.email).first()
#         if user:
#             login_user(user,remember='Y')
#         link = url_for('studentDashboard',student_id=studentDetails.student_id,_external=True)
#         return jsonify({'studentDashboard':link})

@app.route('/getStudentDet',methods=['POST','GET'])
def getStudentDet():
    if request.method == 'POST':
        print('inside getStudentDetails')
        jsonExamData = request.json
        a = json.dumps(jsonExamData)
        z = json.loads(a)
        conList = []
        for con in z['contact'].values():
            conList.append(con)
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        studentDetails = StudentProfile.query.filter_by(user_id=userId.id).first()
        if studentDetails:
            msg = 'What do you want to do today?\n1-See dashboard\n2-see performance\n3-Start practice test'
            return jsonify({'studentDetails':msg})
        else:
            msg = 'you are not a registered student'
            return jsonify({'studentDetails':msg})

@app.route('/getUserDetails',methods=['POST','GET'])
def getUserDetails():
    if request.method == 'POST':
        print('inside getUserDetails')
        jsonExamData = request.json
        a = json.dumps(jsonExamData)
        z = json.loads(a)
        conList = []
        for con in z['contact'].values():
            conList.append(con)
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
        if teacher_id:
            msg = ' What do you want to do today?\n1 - Create or start Online Tests\n2 - Create Online Class Link\n3 - See student profile (Performance report included)\n4 - See Leaderboard\n5 - Customer Support'
            return jsonify({'userDetails':msg})
        else:
            msg = 'you are not a registered teacher'
            return jsonify({'userDetails':msg})

@app.route('/getEnteredTopicList',methods=['POST','GET'])
def getEnteredTopicList():
    if request.method == 'POST':
        jsonExamData = request.json
        # jsonExamData = {"results": {"weightage": "10","topics": "1","subject": "1","question_count": "10","class_val": "3","uploadStatus":"Y","duration":"0","resultStatus":"Y","instructions":"","advance":"Y","negativeMarking":"0","test_type":"Class Feedback"},"custom_key": "custom_value","contact": {"phone": "9008262739"}}
        
        a = json.dumps(jsonExamData)
      
        z = json.loads(a)
        
        
        paramList = []
        conList = []
        print('data:')
        # print(z['result'].class_val)
        # print(z['result'])
        for data in z['results'].values():
            
            paramList.append(data)
        for con in z['contact'].values():
            conList.append(con)
        print(paramList)
        print(conList[2])
        
        print('Data Contact')
        # print(conList[2])
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
        classesListData = ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()
        classList = [] 
        j=1
        for classlist in classesListData:
            classVal = str(j)+str(' - ')+str(classlist.class_val)
            classList.append(classVal)
            j=j+1
        
        selClass = ''
        print('Selected Class option:')
        print(paramList[4])
        for className in classList:
            num = className.split('-')[0]
            print('num:'+str(num))
            print('class:'+str(paramList[4]))
            if int(num) == int(paramList[4]):
                print(className)
                selClass = className.split('-')[1]
                print('selClass:'+str(selClass))
        print('class')
        selClass = selClass.strip()
        print(selClass)
        subQuery = "select md.description as subject,md.msg_id from board_class_subject bcs inner join message_detail md on bcs.subject_id = md.msg_id where school_id='"+str(teacher_id.school_id)+"' and class_val = '"+str(selClass)+"'"
        print(subQuery)
        subjectData = db.session.execute(text(subQuery)).fetchall()
        print(subjectData)
        subjectList = []
        k=1
        subId = ''
        for subj in subjectData:
            sub = str(k)+str('-')+str(subj.subject)
            subjectList.append(sub)
            k=k+1
        for subjectName in subjectList:
            num = subjectName.split('-')[0]
            print('num:'+str(num))
            print('class:'+str(paramList[2]))
            if int(num) == int(paramList[2]):
                print(subjectName)
                selSubject = subjectName.split('-')[1]
                print('selSubject:'+str(selSubject))
                
        print('Subject:')
        selSubject = selSubject.strip()
        # Start for topic
        subQuery = MessageDetails.query.filter_by(description=selSubject).first()
        subId = subQuery.msg_id
        print(selSubject)
        print('SubId:'+str(subId))
        topics = paramList[1].strip()
        topicList = topics.split(',')
        print(topicList[0])
        topic = topicList[0].capitalize()
        print('Topic:'+str(topic))
        dateVal= datetime.today().strftime("%d%m%Y%H%M%S")
        p =1
        for topic in topicList:
            fetchQuesIdsQuery = "select td.board_id,qd.suggested_weightage,qd.question_type,qd.question_id,qd.question_description,td.subject_id,td.topic_id "
            fetchQuesIdsQuery = fetchQuesIdsQuery + "from question_details qd inner join topic_detail td on qd.topic_id = td.topic_id inner join message_detail md on md.msg_id = td.subject_id "
            fetchQuesIdsQuery = fetchQuesIdsQuery + "where td.topic_name like '"+str(topic)+"%' and td.class_val='"+str(selClass)+"' and md.description ='"+str(selSubject)+"' limit '"+str(paramList[3])+"'"
            if p<len(topicList):
                fetchQuesIdsQuery = fetchQuesIdsQuery + "union "
            p=p+1
        print('fetchQuesIds Query:'+str(fetchQuesIdsQuery))
        fetchQuesIds = db.session.execute(fetchQuesIdsQuery).fetchall()
        Msg = 'no questions available'
        if len(fetchQuesIds)==0:
            return jsonify({'onlineTestLink':Msg})
        listLength = len(fetchQuesIds)
        count_marks = int(paramList[0]) * int(listLength)
        
        subjId = ''
        topicID = ''
        boardID = ''
        for det in fetchQuesIds:
            subjId = det.subject_id
            topicID = det.topic_id
            boardID = det.board_id
            break
        print('subjId:'+str(subjId))
        print(fetchQuesIds)
        currClassSecRow=ClassSection.query.filter_by(school_id=str(teacher_id.school_id),class_val=str(selClass).strip()).first()
        resp_session_id = str(subId).strip()+ str(dateVal).strip() + str(randint(10,99)).strip()
        threadUse(currClassSecRow.class_sec_id,resp_session_id,fetchQuesIds,paramList[11],count_marks,selClass,teacher_id.teacher_id,teacher_id.school_id)

        clasVal = selClass.replace('_','@')
        testType = paramList[11].replace('_','@')
        linkForTeacher=url_for('testLinkWhatsappBot',testType=paramList[11],totalMarks=count_marks,respsessionid=resp_session_id,fetchQuesIds=fetchQuesIds,weightage=10,negativeMarking=paramList[10],uploadStatus=paramList[5],resultStatus=paramList[7],advance=paramList[9],instructions=paramList[8],duration=paramList[6],classVal=clasVal,section=currClassSecRow.section,subjectId=subId,phone=contactNo, _external=True)
        # allLink = str('Here is the link to the online test:\n')+str(linkForTeacher)+str('\nDo you want to download the question paper?\n1 - Yes\n2 - No')
        # linkForStudent=url_for('feedbackCollectionStudDev',respsessionid=resp_session_id,schoolId=teacher_id.school_id,uploadStatus=paramList[5],resultStatus=paramList[7],advance=paramList[9], _external=True)
        key = '265e29e3968fc62f68da76a373e5af775fa60'
        url = urllib.parse.quote(linkForTeacher)
        name  = ''
        r = rq.get('http://cutt.ly/api/api.php?key={}&short={}&name={}'.format(key, url, name))
        print('New Link')
        print(r.text)
        print(type(r.text))
        linkList = []
        jsonLink = json.dumps(r.text)
        newData = json.loads(r.text)
        print(type(newData))
        for linkData in newData['url'].values():
            linkList.append(linkData)
        finalLink = linkList[3]
        newLink = str('Here is the link to the online test:\n')+finalLink+str('\nDo you want to download the question paper?\n1 - Yes\n2 - No')
        print('newLink'+str(newLink))
        return jsonify({'onlineTestLink':newLink})


@app.route('/newTestLinkGenerate',methods=['POST','GET'])
def newTestLinkGenerate():
    if request.method == 'POST':
        jsonExamData = request.json
        # jsonExamData = {"results": {"weightage": "10","topics": "1","subject": "1","question_count": "10","class_val": "3","uploadStatus":"Y","duration":"0","resultStatus":"Y","instructions":"","advance":"Y","negativeMarking":"0","test_type":"Class Feedback"},"custom_key": "custom_value","contact": {"phone": "9008262739"}}
        
        a = json.dumps(jsonExamData)
      
        z = json.loads(a)
        
        
        paramList = []
        conList = []
        print('data:')
        # print(z['result'].class_val)
        # print(z['result'])
        for data in z['results'].values():
            
            paramList.append(data)
        for con in z['contact'].values():
            conList.append(con)
        print(paramList)
        print(conList[2])
        # Test for topic
        print('Testing for topic')
        print(type(paramList[1]))
        print(int(paramList[1]))
        # 
        print('Data Contact')
        # print(conList[2])
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
        classesListData = ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()
        classList = [] 
        j=1
        for classlist in classesListData:
            classVal = str(j)+str(' - ')+str(classlist.class_val)
            classList.append(classVal)
            j=j+1
        
        selClass = ''
        print('Selected Class option:')
        print(paramList[4])
        for className in classList:
            num = className.split('-')[0]
            print('num:'+str(num))
            print('class:'+str(paramList[4]))
            if int(num) == int(paramList[4]):
                print(className)
                selClass = className.split('-')[1]
                print('selClass:'+str(selClass))
        print('class')
        selClass = selClass.strip()
        print(selClass)
        subQuery = "select md.description as subject,md.msg_id from board_class_subject bcs inner join message_detail md on bcs.subject_id = md.msg_id where school_id='"+str(teacher_id.school_id)+"' and class_val = '"+str(selClass)+"'"
        print(subQuery)
        subjectData = db.session.execute(text(subQuery)).fetchall()
        print(subjectData)
        subjectList = []
        k=1
        subId = ''
        for subj in subjectData:
            sub = str(k)+str('-')+str(subj.subject)
            subjectList.append(sub)
            k=k+1
        for subjectName in subjectList:
            num = subjectName.split('-')[0]
            print('num:'+str(num))
            print('class:'+str(paramList[2]))
            if int(num) == int(paramList[2]):
                print(subjectName)
                selSubject = subjectName.split('-')[1]
                print('selSubject:'+str(selSubject))
                
        print('Subject:')
        selSubject = selSubject.strip()
        # Start for topic
        subQuery = MessageDetails.query.filter_by(description=selSubject).first()
        subId = subQuery.msg_id
        print(selSubject)
        print('SubId:'+str(subId))
        extractChapterQuery = "select td.chapter_name ,td.chapter_num ,bd.book_name from topic_detail td inner join book_details bd on td.book_id = bd.book_id where td.class_val = '"+str(selClass)+"' and td.subject_id = '"+str(subId)+"'"
        print('Query:'+str(extractChapterQuery))
        extractChapterData = db.session.execute(text(extractChapterQuery)).fetchall()
        print(extractChapterData)
        c=1
        chapterDetList = []
        for chapterDet in extractChapterData:
            chap = str(c)+str('-')+str(chapterDet.chapter_name)+str('-')+str(chapterDet.book_name)+str("\n")
            chapterDetList.append(chap)
            c=c+1
        selChapter = ''
        for chapterName in chapterDetList:
            num = chapterName.split('-')[0]
            print('num:'+str(num))
            print('class:'+str(paramList[1]))
            if int(num) == int(paramList[1]):
                print(chapterName)
                selChapter = chapterName.split('-')[1]
                print('selChapter:'+str(selChapter))
        #End topic
        selChapter = selChapter.strip()
        print('Chapter'+str(selChapter))
        dateVal= datetime.today().strftime("%d%m%Y%H%M%S")
        fetchQuesIdsQuery = "select td.board_id,qd.suggested_weightage,qd.question_type,qd.question_id,qd.question_description,td.subject_id,td.topic_id from question_details qd "
        fetchQuesIdsQuery = fetchQuesIdsQuery + "inner join topic_detail td on qd.topic_id = td.topic_id "
        fetchQuesIdsQuery = fetchQuesIdsQuery + "inner join message_detail md on md.msg_id = td.subject_id "
        fetchQuesIdsQuery = fetchQuesIdsQuery + "where td.chapter_name = '"+str(selChapter)+"' and md.description = '"+str(selSubject)+"' and td.class_val = '"+str(selClass)+"' limit '"+str(paramList[3])+"'"
        print('fetchQuesIds Query:'+str(fetchQuesIdsQuery))
        fetchQuesIds = db.session.execute(fetchQuesIdsQuery).fetchall()
        msg = 'no questions available'
        print('fetchQuesIds:'+str(fetchQuesIds))
        if len(fetchQuesIds)==0 or fetchQuesIds=='':
            return jsonify({'onlineTestLink':msg})
        listLength = len(fetchQuesIds)
        count_marks = int(paramList[0]) * int(listLength)
        
        subjId = ''
        topicID = ''
        boardID = ''
        for det in fetchQuesIds:
            subjId = det.subject_id
            topicID = det.topic_id
            boardID = det.board_id
            break
        print('subjId:'+str(subjId))
        print(fetchQuesIds)
        currClassSecRow=ClassSection.query.filter_by(school_id=str(teacher_id.school_id),class_val=str(selClass).strip()).first()
        resp_session_id = str(subId).strip()+ str(dateVal).strip() + str(randint(10,99)).strip()
        threadUse(currClassSecRow.class_sec_id,resp_session_id,fetchQuesIds,paramList[11],count_marks,selClass,teacher_id.teacher_id,teacher_id.school_id)

        clasVal = selClass.replace('_','@')
        testType = paramList[11].replace('_','@')
        linkForTeacher=url_for('testLinkWhatsappBot',testType=paramList[11],totalMarks=count_marks,respsessionid=resp_session_id,fetchQuesIds=fetchQuesIds,weightage=10,negativeMarking=paramList[10],uploadStatus=paramList[5],resultStatus=paramList[7],advance=paramList[9],instructions=paramList[8],duration=paramList[6],classVal=clasVal,section=currClassSecRow.section,subjectId=subId,phone=contactNo, _external=True)
        key = '265e29e3968fc62f68da76a373e5af775fa60'
        url = urllib.parse.quote(linkForTeacher)
        name  = ''
        r = rq.get('http://cutt.ly/api/api.php?key={}&short={}&name={}'.format(key, url, name))
        print('New Link')
        print(r.text)
        print(type(r.text))
        linkList = []
        jsonLink = json.dumps(r.text)
        newData = json.loads(r.text)
        print(type(newData))
        for linkData in newData['url'].values():
            linkList.append(linkData)
        finalLink = linkList[3]
        newLink = str('Here is the link to the online test:\n')+finalLink+str('\nDo you want to download the question paper?\n1 - Yes\n2 - No')
        print('newLink'+str(newLink))
        return jsonify({'onlineTestLink':newLink})

@app.route('/getNewUrl',methods=['POST','GET'])
def getNewUrl():
    jsonData = {"url":{"status":7,"fullLink":"https:\/\/alllearnreview-pr-229.herokuapp.com\/testLinkWhatsappBot?testType=Class+Feedback&totalMarks=50&respsessionid=3320402202117572449&fetchQuesIds=%281004%2C+10%2C+%27Subjective%27%2C+6046%2C+%27Double+Attack%3A+White+to+Move%27%2C+332%2C+3081%29&fetchQuesIds=%281004%2C+10%2C+%27Subjective%27%2C+6048%2C+%27Double+Attack%3A+White+to+Move%27%2C+332%2C+3081%29&fetchQuesIds=%281004%2C+10%2C+%27Subjective%27%2C+6047%2C+%27Double+Attack%3A+White+to+Move%27%2C+332%2C+3081%29&fetchQuesIds=%281004%2C+10%2C+%27Subjective%27%2C+6051%2C+%27Double+Attack%3A+White+to+Move%27%2C+332%2C+3081%29&fetchQuesIds=%281004%2C+10%2C+%27Subjective%27%2C+6049%2C+%27Double+Attack%3A+White+to+Move%27%2C+332%2C+3081%29&weightage=10&negativeMarking=0&uploadStatus=Y&resultStatus=Y&advance=Y&instructions=&duration=0&classVal=Beginner%40Level%403&section=Abhishek+P&subjectId=332&phone=8802362259","date":"2021-02-04","shortLink":"https:\/\/cutt.ly\/IkkYl2L","title":"allLearn"}}
    linkList = []
    jsonLink = json.dumps(jsonData)
    newData = json.loads(jsonLink)
    print(newData)
    for linkData in newData['url'].values():
        linkList.append(linkData)
    finalLink = linkList[3]
    return jsonify({'data':finalLink})
@app.route('/getTestPaperLink',methods=['POST','GET'])
def getTestPaperLink():
    if request.method == 'POST':
        # jsonData = request.json        
        # a = json.dumps(jsonData)
        # z = json.loads(a)
        # print('inside getTestPaperLink')
        # for data in z['results'].values():
        #     print(data)
        testPaperQuery = "select test_paper_link from test_details order by test_id desc limit 1"
        print(testPaperQuery)
        testPaperData = db.session.execute(text(testPaperQuery)).first()
        testPaperLink = str("Here's the test paper link:\n")+str(testPaperData.test_paper_link)
        print('testPaperLink:'+str(testPaperLink))
        return jsonify({'TestPaperLink':testPaperLink})

    
@app.route('/testLinkWhatsappBot', methods=['POST','GET'])
def testLinkWhatsappBot(): 
    phone = request.args.get('phone') 
    user = User.query.filter_by(phone=phone).first()
    teacher= TeacherProfile.query.filter_by(user_id=user.id).first() 
    student = StudentProfile.query.filter_by(user_id=user.id).first()
    subject_id = request.args.get('subjectId')
    subjectQuery = MessageDetails.query.filter_by(msg_id=subject_id).first()
    subjectName = subjectQuery.description
    classVal = request.args.get('classVal')
    emailDet = ''
    if student:
      emailDet = StudentProfile.query.filter_by(student_id=student.student_id).first()
    user = ''
    
    if emailDet:
        user = User.query.filter_by(email=teacher.email).first()
    if user:
        login_user(user,remember='Y')
    clasVal = classVal.replace('@','_')
    respsessionid = request.args.get('respsessionid')
    testQuery = SessionDetail.query.filter_by(resp_session_id=respsessionid).first()
    testId = testQuery.test_id
    section = request.args.get('section')
    fetchQuesQuery = "select question_id from test_questions where test_id='"+str(testId)+"'"
    fetchQuesIds = db.session.execute(fetchQuesQuery).fetchall()
    quesIds = []
    for fetchIds in fetchQuesIds:
        quesIds.append(fetchIds.question_id)
    questions = QuestionDetails.query.filter(QuestionDetails.question_id.in_(quesIds)).all()  
    for ques in questions:
        print('question description:')
        print(ques.question_id)
        print(ques.question_description)
    # questions = QuestionDetails.query.filter(QuestionDetails.question_id.in_(fetchQuesIds)).all()
    questionListSize = len(fetchQuesIds)
    respsessionid = request.args.get('respsessionid')
    total_marks = request.args.get('totalMarks')
    weightage = request.args.get('weightage')
    test_type = request.args.get('testType')
    test_type = test_type.replace('@','_')
    uploadStatus = request.args.get('uploadStatus')
    resultStatus = request.args.get('resultStatus')
    advance = request.args.get('advance')
    print('inside testLinkWhatsappBot')
    print('Subject Id:'+str(subject_id))
    studId = None
    if current_user.is_anonymous:
        print('user id student')
        return redirect(url_for('feedbackCollectionStudDev',student_id=studId,resp_session_id=respsessionid,school_id=teacher.school_id,uploadStatus=uploadStatus,resultStatus=resultStatus,advance=advance,_external=True))
        # return render_template('feedbackCollectionStudDev.html',resp_session_id=str(respsessionid),studId=studId,uploadStatus=uploadStatus,resultStatus=resultStatus,advance=advance)
    else:
        print('user is teacher') 
        url = "http://www.school.alllearn.in/feedbackCollectionStudDev?resp_session_id="+str(respsessionid)+"&school_id="+str(teacher.school_id)
        responseSessionIDQRCode = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="+url
        return render_template('feedbackCollectionTeachDev.html',classSecCheckVal='Y', subject_id=subject_id, 
            class_val = clasVal, section = section,questions=questions, questionListSize = questionListSize, resp_session_id = respsessionid,responseSessionIDQRCode=responseSessionIDQRCode,
            subjectName = subjectName, totalMarks=total_marks,weightage=weightage, 
            batch_test=0,testType=test_type,school_id=teacher.school_id,uploadStatus=uploadStatus,resultStatus=resultStatus,advance=advance)

    # else:
    #     return redirect(url_for('classCon'))


# route for fetching next question and updating db for each response from student - tablet assessment process

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
  

@app.route('/studentDashboard',methods=['GET','POST'])
@login_required
def studentDashboard():
    print('inside student dashboard')
    # student_id = ''
    # studentDet = ''
    # if current_user.is_anonymous:
    #     student_id = request.args.get('student_id')
    #     studentDet = StudentProfile.query.filter_by(student_id=student_id).first()
    # else:
    studentDet = StudentProfile.query.filter_by(user_id=current_user.id).first()
    student_id = studentDet.student_id
    print('Student Id:'+str(student_id))
    testHistoryQuery = "SELECT fsprc.student_id,fsprc.subject,fsprc.topics,fsprc.test_date,fsprc.resp_session_id,fsprc.perf_percentage from fn_student_performance_response_capture("+str(student_id)+") fsprc order by test_date desc"
    # testHistoryQuery = testHistoryQuery + "inner join response_capture rc on fsprc.resp_session_id = rc.resp_session_id order by test_date desc limit 50"
    testHistory = db.session.execute(testHistoryQuery).fetchall()
    homeworkDetailQuery = "select sd.homework_id, homework_name, question_count, sd.last_modified_date,count(ssr.answer) as ans_count "
    homeworkDetailQuery = homeworkDetailQuery+ "from homework_detail sd left join student_homework_response ssr on ssr.homework_id =sd.homework_id "
    homeworkDetailQuery = homeworkDetailQuery+" where sd.school_id ="+str(studentDet.school_id)+ " and sd.is_archived='N' and sd.class_sec_id='"+str(studentDet.class_sec_id)+"' group by sd.homework_id,homework_name,question_count, sd.last_modified_date"
    homeworkDetailQuery = homeworkDetailQuery+" order by sd.last_modified_date desc limit 10"
    print(homeworkDetailQuery)
    homeworkData = db.session.execute(homeworkDetailQuery).fetchall()
    upcomingTestDetailQuery ="select md.description as subject,sd.test_due_date,sd.test_time, sd.total_marks,sd.test_link, sd.incorrect_marks, sd.test_id from session_detail sd "
    upcomingTestDetailQuery = upcomingTestDetailQuery + "inner join test_details td on sd.test_id = td.test_id "
    upcomingTestDetailQuery = upcomingTestDetailQuery + "inner join message_detail md on md.msg_id = td.subject_id "
    upcomingTestDetailQuery = upcomingTestDetailQuery + "where sd.resp_session_id not in (select distinct rc.resp_session_id from response_capture rc where student_id = '"+str(studentDet.student_id)+"') and sd.test_due_date > now() and sd.class_sec_id='"+str(studentDet.class_sec_id)+"'"
    print('fetch upcoming Test Query')
    print(upcomingTestDetailQuery)
    upcomigTestDetails = db.session.execute(upcomingTestDetailQuery).fetchall()
    print('Test Res Data:')
    print(testHistory)
    # Overall Performance
    overallSum = 0
    overallPerfValue = 0
    sumMarks = 0
    sum1 = 0
    sum2 = 0
    totalOfflineTestMarks = "select sum(marks_scored) as sum1 from result_upload ru where student_id = '"+str(student_id)+"'"
    print(totalOfflineTestMarks)
    totalOfflineTestMarks = db.session.execute(text(totalOfflineTestMarks)).first()
    if totalOfflineTestMarks.sum1:
        print(totalOfflineTestMarks.sum1)
        sum1 = totalOfflineTestMarks.sum1
    totalOnlineTestMarks = "select sum(student_score) as sum2 from performance_detail pd where student_id = '"+str(student_id)+"'"
    totalOnlineTestMarks = db.session.execute(text(totalOnlineTestMarks)).first()
    
    if totalOnlineTestMarks.sum2:
        print(totalOnlineTestMarks.sum2)
        sum2 = totalOnlineTestMarks.sum2
    sumMarks = int(sum1) + int(sum2)
    print('Total Marks:'+str(sumMarks))
    total1 = "select total_marks as offlineTotal from result_upload ru where student_id = '"+str(student_id)+"'"
    print(total1)
    total1 = db.session.execute(text(total1)).first()
    tot1 = 0
    if total1:
        print(total1.offlinetotal)
        tot1 = total1.offlinetotal
    total2 = "select count(*) as count from performance_detail pd where student_id = '"+str(student_id)+"'"
    total2 = db.session.execute(text(total2)).first()
    total3 = 0
    grandTotal = 0
    if total2.count:
        print(total2.count)
        total3 = total2.count*100
    grandTotal = int(tot1) + int(total3)
    print('Grand Total:'+str(grandTotal))
    # for rows in perfRows:
    #     overallSum = overallSum + int(rows.student_score)
        #print(overallSum)
    try:
        overallPerfValue = round(sumMarks/(grandTotal)*100,2)    
    except:
        overallPerfValue=0 
    # End
    subjectPerfQuery = "select subject,student_score from fn_leaderboard_responsecapture() where student_id='"+str(student_id)+"' "
    subjectPerf = db.session.execute(subjectPerfQuery).fetchall()
    topicTrackerQuery = "with cte_total_topics as "
    topicTrackerQuery = topicTrackerQuery + "(select subject_id,  "
    topicTrackerQuery = topicTrackerQuery +"count(is_covered) as total_topics , max(last_modified_Date) as last_updated_date "
    topicTrackerQuery = topicTrackerQuery +"  from topic_tracker where class_sec_id = '"+ str(studentDet.class_sec_id)+"' group by subject_id)  "
    topicTrackerQuery = topicTrackerQuery +"select c1.subject_id,  t2.description as subject_name, c1.last_updated_date, "
    topicTrackerQuery = topicTrackerQuery +"CASE WHEN COUNT(t1.subject_id) <> 0 THEN COUNT(c1.subject_id) ELSE 0 END "
    topicTrackerQuery = topicTrackerQuery +"topics_covered, c1.total_topics  "
    topicTrackerQuery = topicTrackerQuery +"from topic_tracker t1  "
    topicTrackerQuery = topicTrackerQuery +"right outer join cte_total_topics c1  "
    topicTrackerQuery = topicTrackerQuery +"on c1.subject_id=t1.subject_id and class_sec_id= '"+ str(studentDet.class_sec_id)+"'  "
    topicTrackerQuery = topicTrackerQuery +"and t1.is_covered='Y'  "
    topicTrackerQuery = topicTrackerQuery +"inner join   "
    topicTrackerQuery = topicTrackerQuery +"message_detail t2 on   "
    topicTrackerQuery = topicTrackerQuery +"c1.subject_id=t2.msg_id  "
    topicTrackerQuery = topicTrackerQuery +"group by c1.subject_id, t2.description, c1.total_topics,  c1.last_updated_date"                
    topicRows  = db.session.execute(text(topicTrackerQuery)).fetchall()
    classQuery = ClassSection.query.filter_by(class_sec_id = studentDet.class_sec_id).first()
    qclass_val = classQuery.class_val
    writtenTestCountQuery = "SELECT fsprc.student_id,fsprc.subject,fsprc.topics,fsprc.test_date,fsprc.resp_session_id,fsprc.perf_percentage from fn_student_performance_response_capture("+str(student_id)+") fsprc order by test_date desc"
    writtenTestCountData = db.session.execute(text(writtenTestCountQuery)).fetchall()
    writtenTestCount = len(writtenTestCountData)
    pendingTestCountQuery = "select count(*) from session_detail sd "
    pendingTestCountQuery = pendingTestCountQuery + "inner join test_details td on sd.test_id = td.test_id "
    pendingTestCountQuery = pendingTestCountQuery + "inner join message_detail md on md.msg_id = td.subject_id "
    pendingTestCountQuery = pendingTestCountQuery + "where sd.resp_session_id not in (select distinct rc.resp_session_id from response_capture rc where student_id = '"+str(studentDet.student_id)+"') and sd.test_due_date > now() and sd.class_sec_id='"+str(studentDet.class_sec_id)+"'"
    pendingTestCount = db.session.execute(text(pendingTestCountQuery)).first()
    writtenHomeworkCountQuery = "select distinct homework_id from student_homework_response shr where student_id = '"+str(studentDet.student_id)+"'"
    writtenHomeworkCountData = db.session.execute(text(writtenHomeworkCountQuery)).fetchall()
    writtenHomeworkCount = len(writtenHomeworkCountData)
    pendingHomeworkCountQuery = "select distinct count(*) from homework_detail hd where homework_id not in "
    pendingHomeworkCountQuery = pendingHomeworkCountQuery + "(select distinct homework_id from student_homework_response shr where student_id = '"+str(studentDet.student_id)+"' ) and class_sec_id = '"+str(studentDet.class_sec_id)+"'"
    pendingHomeworkCount = db.session.execute(text(pendingHomeworkCountQuery)).first()
    topicCoveredCountQuery = "select distinct count(*) from topic_tracker tt where is_covered = 'Y' and school_id = '"+str(studentDet.school_id)+"' and is_archived = 'N'"
    topicCoveredCount = db.session.execute(text(topicCoveredCountQuery)).first()
    topicunCoveredCountQuery = "select distinct count(*) from topic_tracker tt where is_covered = 'N' and school_id = '"+str(studentDet.school_id)+"' and is_archived = 'N'"
    topicUncoveredCount = db.session.execute(text(topicunCoveredCountQuery)).first()
    return render_template('studentDashboard.html',topicUncoveredCount=topicUncoveredCount,topicCoveredCount=topicCoveredCount,pendingHomeworkCount=pendingHomeworkCount,writtenHomeworkCount=writtenHomeworkCount,pendingTestCount=pendingTestCount,writtenTestCount=writtenTestCount,qclass_val=qclass_val,topicRows=topicRows,subjectPerf=subjectPerf,overallPerfValue=overallPerfValue,upcomigTestDetails=upcomigTestDetails,homeworkData=homeworkData,testHistory=testHistory,studentDet=studentDet)


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
