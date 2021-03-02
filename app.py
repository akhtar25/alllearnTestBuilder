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