from flask import Flask, render_template, request, flash, redirect, url_for, Response,session,jsonify
from send_email import welcome_email, send_password_reset_email, user_access_request_email, access_granted_email, new_school_reg_email
from send_email import new_teacher_invitation,new_applicant_for_job, application_processed, job_posted_email
from applicationDB import *
from qrReader import *
from config import Config
from forms import LoginForm, RegistrationForm,ContentManager,LeaderBoardQueryForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm,ResultQueryForm,MarksForm, TestBuilderQueryForm,SchoolRegistrationForm, PaymentDetailsForm, addEventForm,QuestionBuilderQueryForm, SingleStudentRegistration, SchoolTeacherForm, feedbackReportForm, testPerformanceForm, studentPerformanceForm, QuestionUpdaterQueryForm,  QuestionBankQueryForm
from forms import createSubscriptionForm,ClassRegisterForm,postJobForm
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
import requests
from flask_talisman import Talisman, ALLOW_FROM

#from flask_material import Material

app=Flask(__name__)
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
            'logs/alllearn'+str(dateVal).replace(' ','').replace(':','').replace('.','')+'.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Alllearn startup')


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
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        if teacher_id != None:
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
    #S3_BUCKET = "alllearndatabucket"
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
    if current_user.user_type==134:
        value=1
    return render_template('schoolProfile.html', teacherRow=teacherRow, registeredStudentCount=registeredStudentCount, registeredTeacherCount=registeredTeacherCount,allTeachers=allTeachers,classSectionRows=classSectionRows, schoolProfileRow=schoolProfileRow,addressRow=addressRow,subscriptionRow=subscriptionRow,disconn=value)

@app.route('/schoolRegistration', methods=['GET','POST'])
@login_required
def schoolRegistration():
    #queries for subcription 
    subscriptionRow = SubscriptionDetail.query.filter_by(archive_status='N').order_by(SubscriptionDetail.sub_duration_months).all()    
    distinctSubsQuery = db.session.execute(text("select distinct group_name, sub_desc, student_limit, teacher_limit, test_limit from subscription_detail where archive_status='N' order by student_limit ")).fetchall()

    S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
    form = SchoolRegistrationForm()
    form.board.choices=[(str(i.description), str(i.description)) for i in MessageDetails.query.with_entities(MessageDetails.description).distinct().filter_by(category='Board').all()]
    if form.validate_on_submit():
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
        class_val=request.form.getlist('class_val')
        class_section=request.form.getlist('section')
        student_count=request.form.getlist('student_count')

        for i in range(len(class_val)):
            class_data=ClassSection(class_val=int(class_val[i]),section=str(class_section[i]).upper(),student_count=int(student_count[i]),school_id=school_id.school_id)
            db.session.add(class_data)
        teacher=TeacherProfile(school_id=school.school_id,email=current_user.email,user_id=current_user.id, designation=147, registration_date=dt.datetime.now(), last_modified_date=dt.datetime.now(), phone=current_user.phone, device_preference=78 )
        db.session.add(teacher)
        db.session.commit()
        newTeacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        newSchool = SchoolProfile.query.filter_by(school_id=school_id.school_id).first()        
        newSchool.school_admin = newTeacherRow.teacher_id

        #adding records to topic tracker while registering school
        
        classSecRows = ClassSection.query.filter_by(school_id=newSchool.school_id).all()
        for classRow in classSecRows:
            insertRow = "insert into topic_tracker (subject_id, class_sec_id, is_covered, topic_id, school_id, reteach_count, last_modified_date) (select subject_id, '"+str(classRow.class_sec_id)+"', 'N', topic_id, '"+str(newSchool.school_id)+"', 0,current_date from Topic_detail where class_val="+str(classRow.class_val)+")"
            db.session.execute(text(insertRow))

        #end of inser to topic tracker
        db.session.commit()
        data=ClassSection.query.filter_by(school_id=school_id.school_id).all()
        flash('School Registered Successfully!')
        new_school_reg_email(form.schoolName.data)
        return render_template('schoolRegistrationSuccess.html',data=data,school_id=school_id.school_id)
    return render_template('schoolRegistration.html',disconn = 1,form=form, subscriptionRow=subscriptionRow, distinctSubsQuery=distinctSubsQuery, School_Name=schoolNameVal())

@app.route('/admin')
@login_required
def admin():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    query = "select count(*) from public.user where user_type='161'"
    query2 = "SELECT count(*) FROM public.user WHERE last_seen >=current_date - 10;"
    count = db.session.execute(text(query)).fetchall()
    count2 = db.session.execute(text(query2)).fetchall()
    num = ''
    num2 = ''
    for c in count:
        num = c.count
    for c2 in count2:
        num2 = c2.count
    print('Count'+str(num))
    print('Count2:'+str(num2))
    return render_template('admin.html',count=num,number = num2)

@app.route('/classRegistration', methods=['GET','POST'])
@login_required
def classRegistration():
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    classSectionRows = ClassSection.query.filter_by(school_id=teacherRow.school_id).all()

    form = ClassRegisterForm()
    #if form.validate_on_submit():
    if request.method == 'POST':
        print('passed validation')
        class_val=request.form.getlist('class_val')
        class_section=request.form.getlist('section')
        student_count=request.form.getlist('student_count')

        for i in range(len(class_val)):
            print('there is a range')
            class_data=ClassSection(class_val=int(class_val[i]),section=str(class_section[i]).upper(),student_count=int(student_count[i]),school_id=teacherRow.school_id)
            db.session.add(class_data)
        
        db.session.commit()
        #adding records to topic tracker while registering school
        
        classSecRows = ClassSection.query.filter_by(school_id=teacherRow.school_id).all()

        topicTrackerRows = "select distinct class_sec_id from topic_tracker where school_id='"+str(teacherRow.school_id)+"'"

        classSecNotInTopicTracker = db.session.execute(text(topicTrackerRows)).fetchall()

        for classRow in classSecRows:
            if classRow.class_sec_id not in classSecNotInTopicTracker: 
                insertRow = "insert into topic_tracker (subject_id, class_sec_id, is_covered, topic_id, school_id, reteach_count, last_modified_date) (select subject_id, '"+str(classRow.class_sec_id)+"', 'N', topic_id, '"+str(teacherRow.school_id)+"', 0,current_date from Topic_detail where class_val="+str(classRow.class_val)+")"
                db.session.execute(text(insertRow))
        db.session.commit()

        flash('Classes added successfully!')
    return render_template('classRegistration.html', classSectionRows=classSectionRows,form=form)    
    



@app.route('/teacherRegistration',methods=['GET','POST'])
@login_required
def teacherRegistration():
    school_name_val = schoolNameVal()
    
    if school_name_val ==None:
        print('did we reach here')
        return redirect(url_for('disconnectedAccount'))
    else:
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
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
                    class_sec_id=ClassSection.query.filter_by(class_val=int(teacher_class[i]),section=teacher_class_section[i]).first()
                    teacher_data=TeacherProfile(teacher_name=teacher_name[i],school_id=teacher_id.school_id,class_sec_id=class_sec_id.class_sec_id,email=teacher_email[i],subject_id=int(teacher_subject[i]),last_modified_date= datetime.now(), registration_date = datetime.now())
                    db.session.add(teacher_data)
                else:
                    teacher_data=TeacherProfile(teacher_name=teacher_name[i],school_id=teacher_id.school_id,email=teacher_email[i],subject_id=int(teacher_subject[i]),last_modified_date= datetime.now(), registration_date = datetime.now(), device_preference=195)
                    db.session.add(teacher_data)
                    #send email to the teachers here
                new_teacher_invitation(teacher_email[i],teacher_name[i],school_name_val, str(teacher_id.teacher_name))
            db.session.commit()
            flash('Successful registration !')
            return render_template('teacherRegistration.html',form=form)
        return render_template('teacherRegistration.html',form=form)

@app.route('/bulkStudReg')
def bulkStudReg():
    return render_template('_bulkStudReg.html')


@app.route('/singleStudReg')
def singleStudReg():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher_id.school_id).all()
    section_list=[(i.section,i.section) for i in available_section]
    form=SingleStudentRegistration()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).order_by(ClassSection.class_val).all()]
    form.section.choices= section_list
    return render_template('_singleStudReg.html',form=form)


@app.route('/studentRegistration', methods=['GET','POST'])
@login_required
def studentRegistration():
    form=SingleStudentRegistration()
    if request.method=='POST':
        if form.submit.data:
            address_id=Address.query.filter_by(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data).first()
            if address_id is None:
                address_data=Address(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data,country=form.country.data)
                db.session.add(address_data)
                address_id=db.session.query(Address).filter_by(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data).first()
            teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
            print('Print Form Data:'+form.section.data)
            class_sec=ClassSection.query.filter_by(class_val=int(form.class_val.data),section=form.section.data,school_id=teacher_id.school_id).first()
            gender=MessageDetails.query.filter_by(description=form.gender.data).first()
            print('Section Id:'+str(class_sec.class_sec_id))
            student=StudentProfile(first_name=form.first_name.data,last_name=form.last_name.data,full_name=form.first_name.data +" " + form.last_name.data,
            school_id=teacher_id.school_id,class_sec_id=class_sec.class_sec_id,gender=gender.msg_id,
            dob=request.form['birthdate'],phone=form.phone.data,profile_picture=request.form['profile_image'],address_id=address_id.address_id,school_adm_number=form.school_admn_no.data,
            roll_number=int(form.roll_number.data))
            #print('Query:'+student)
            db.session.add(student)
            student_data=db.session.query(StudentProfile).filter_by(school_adm_number=form.school_admn_no.data).first()
            for i in range(4):
                if i==0:
                    option='A'
                    qr_link='https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + str(student_data.student_id) + '-' + form.roll_number.data + '-' + student_data.first_name + '@' + option
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
            for i in range(len(first_name)):
                relation_id=MessageDetails.query.filter_by(description=relation[i]).first()
                guardian_data=GuardianProfile(first_name=first_name[i],last_name=last_name[i],full_name=first_name[i] + ' ' + last_name[i],relation=relation_id.msg_id,
                email=email[i],phone=phone[i],student_id=student_data.student_id)
                db.session.add(guardian_data)
            db.session.commit()
            flash('Successful upload !')
            return render_template('studentRegistration.html')
        else:
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
                class_sec=ClassSection.query.filter_by(class_val=row['class_val'],section=row['section']).first()
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
                if relation_id is not None:
                    guardian_data=GuardianProfile(first_name=row['guardian'+str(i+1)+'_first_name'],last_name=row['guardian'+str(i+1)+'_last_name'],full_name=row['guardian'+str(i+1)+'_first_name'] + ' ' + row['guardian'+str(i+1)+'_last_name'],relation=relation_id.msg_id,
                    email=row['guardian'+str(i+1)+'_email'],phone=row['guardian'+str(i+1)+'_phone'],student_id=student_data.student_id)
                else:
                    guardian_data=GuardianProfile(first_name=row['guardian'+str(i+1)+'_first_name'],last_name=row['guardian'+str(i+1)+'_last_name'],full_name=row['guardian'+str(i+1)+'_first_name'] + ' ' + row['guardian'+str(i+1)+'_last_name'],
                    email=row['guardian'+str(i+1)+'_email'],phone=row['guardian'+str(i+1)+'_phone'],student_id=student_data.student_id)
                
                db.session.add(guardian_data)
                
            db.session.commit()
            flash('Successful upload !')
            return render_template('studentRegistration.html')
    return render_template('studentRegistration.html')


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
        

    return render_template(
        'edit_profile.html', title='Edit Profile', form=form,user_type_val=str(current_user.user_type), willing_to_travel=current_user.willing_to_travel)


@app.route('/')
@app.route('/index')
@app.route('/dashboard')
@login_required
def index():
    user = User.query.filter_by(username=current_user.username).first_or_404()        


    school_name_val = schoolNameVal()
    
    if user.user_type=='161':
        return redirect(url_for('openJobs'))
    if user.user_type=='134' and user.access_status=='145':        
        return redirect(url_for('qrSessionScannerStudent'))

    teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
    classSecCheckVal = classSecCheck()

    if school_name_val ==None:
        print('did we reach here')
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
        topStudentsQuery = "select *from fn_monthly_top_students("+str(teacher.school_id)+",8)"
        
        topStudentsRows = db.session.execute(text(topStudentsQuery)).fetchall()
        for val in topStudentsRows:
            print(val.student_name)
        #print("this is topStudentRows"+str(topStudentsRows))
    #####Fetch Event data##########
        EventDetailRows = EventDetail.query.filter_by(school_id=teacher.school_id).all()
    #####Fetch Course Completion infor##########    
        topicToCoverQuery = "select *from fn_topic_tracker_overall("+str(teacher.school_id)+") order by class, section"
        topicToCoverDetails = db.session.execute(text(topicToCoverQuery)).fetchall()
        #print(topicToCoverDetails)

    ##################Fetch Job post details################################
        jobPosts = JobDetail.query.filter_by(school_id=teacher.school_id).order_by(JobDetail.posted_on.desc()).all()

        return render_template('dashboard.html',title='Home Page',school_id=teacher.school_id, jobPosts=jobPosts,
            graphJSON=graphJSON, classSecCheckVal=classSecCheckVal,topicToCoverDetails = topicToCoverDetails, EventDetailRows = EventDetailRows, topStudentsRows = topStudentsRows)


@app.route('/disconnectedAccount')
@login_required
def disconnectedAccount():    
    userDetailRow=User.query.filter_by(username=current_user.username).first()
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()


    if teacher==None and userDetailRow.user_type!=161 and userDetailRow.user_type!=134:
        return render_template('disconnectedAccount.html', title='Disconnected Account', disconn = 1, userDetailRow=userDetailRow)
    elif userDetailRow.user_type==161:
        return redirect(url_for('openJobs'))
    elif userDetailRow.user_type==134 and userDetailRow.access_status==145:
        return redirect(url_for('qrSessionScannerStudent'))
    else:
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
@login_required
def openJobs():
    page=request.args.get('page',0, type=int)    
    first_login = request.args.get('first_login','0').strip()

    jobTermOptions = MessageDetails.query.filter_by(category='Teaching Term Option').all()
    jobTypeOptions = MessageDetails.query.filter_by(category='Job Type').all()

    if first_login=='1':
        print('this is the first login section')
        userRecord = User.query.filter_by(id=current_user.id).first()
        userRecord.user_type= '161'
        db.session.commit()
        flash('Please complete your profile before applying for jobs')
        return redirect('edit_profile')
    else:
        print('first login not registered')    
        return render_template('openJobs.html',title='Look for Jobs', user_type_val=str(current_user.user_type),first_login=first_login,jobTermOptions=jobTermOptions,jobTypeOptions=jobTypeOptions,classSecCheckVal=classSecCheck())


@app.route('/openJobsFilteredList')
@login_required
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
@login_required
def jobDetail():
    job_id = request.args.get('job_id')
    school_id=request.args.get('school_id')    
    #teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()    
    schoolProfileRow = SchoolProfile.query.filter_by(school_id =school_id).first()
    addressRow = Address.query.filter_by(address_id = schoolProfileRow.address_id).first()    
    jobDetailRow = JobDetail.query.filter_by(job_id=job_id).first()
    jobApplicationRow = JobApplication.query.filter_by(job_id=job_id, applier_user_id=current_user.id).first()
    if jobApplicationRow!=None:
        applied=1
    else:
        applied=0
    return render_template('jobDetail.html', title='Job Detail', 
        schoolProfileRow=schoolProfileRow,classSecCheckVal=classSecCheck(),addressRow=addressRow,jobDetailRow=jobDetailRow,applied=applied, user_type_val=str(current_user.user_type))



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


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
        if schoolAdminRow[0][0]==teacher.teacher_id:
            accessReqQuery = "select t1.username, t1.email, t1.phone, t2.description as user_type, t1.about_me, t1.school_id from public.user t1 inner join message_detail t2 on t1.user_type=t2.msg_id where t1.school_id='"+ str(teacher.school_id) +"' and t1.access_status=143"
            accessRequestListRows = db.session.execute(text(accessReqQuery)).fetchall()
        return render_template('user.html', classSecCheckVal=classSecCheck(),user=user,teacher=teacher,accessRequestListRows=accessRequestListRows, school_id=teacher.school_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.user_type=='161':
            return redirect(url_for('openJobs'))
        else:
            return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()                

        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password")
            return redirect(url_for('login'))
        login_user(user,remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        
        #setting global variables
        session['classSecVal'] = classSecCheck()
        session['schoolName'] = schoolNameVal()
        print(session['schoolName'])

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

@app.route('/feeManagement')
@login_required
def feeManagement():
    return render_template('feeManagement.html')


@app.route('/privacyPolicy')
def privacyPolicy():
    return render_template('privacyPolicy.html')


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
    boardRows = MessageDetails.query.filter_by(category='Board').all()
    return render_template('syllabus.html', boardRows=boardRows)


@app.route('/syllabusClasses')
@login_required
def syllabusClasses():
    board_id=request.args.get('board_id')
    classArray = []
    distinctClasses = db.session.execute(text("select distinct class_val from topic_detail where board_id='"+str(board_id)+"' order by class_val ")).fetchall()
    for val in distinctClasses:
        print(val.class_val)
        classArray.append(val.class_val)
    return jsonify([classArray])


@app.route('/syllabusSubjects')
@login_required
def syllabusSubjects():
    board_id=request.args.get('board_id')
    class_val=request.args.get('class_val')
    subjectQuery = "select distinct t1.subject_id, t2.description from topic_detail t1  inner join  message_detail t2 on "
    subjectQuery = subjectQuery+ "t1.subject_id=t2.msg_id where board_id='"+board_id+"' and class_val='"+class_val+"' order by subject_id"
    distinctSubjects = db.session.execute(text(subjectQuery)).fetchall()
    sujectArray=[]
    for val in distinctSubjects:
        print(val.description)
        sujectArray.append(str(val.subject_id)+":"+str(val.description))
    return jsonify([sujectArray])    

@app.route('/addSubject')
@login_required
def addSubject():
    subjectVal = request.args.get('subjectVal')
    board_id=request.args.get('board_id')
    class_val=request.args.get('class_val')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    insertSubject = db.session.execute(text("insert into class_section()"))


@app.route('/syllabusBooks')
@login_required
def syllabusBooks():
    subject_name=request.args.get('subject_name')
    class_val=request.args.get('class_val')
    #distinctBookQuery = "select distinct book_id, book_name from book_details where subject_id='"+subject_id+"'and class_val='"+class_val+"'"
    distinctBookQuery ="select distinct replace(book_name , ' ', '') as book_name from book_details t1  inner join  message_detail t2 on "
    distinctBookQuery=distinctBookQuery+"t1.subject_id=t2.msg_id and t2.description='"+subject_name+"' and t1.class_val='"+class_val+"'"
    distinctBooks = db.session.execute(text(distinctBookQuery)).fetchall()
    bookArray=[]
    for val in distinctBooks:
        print(val.book_name)
        bookArray.append(val.book_name)
    return jsonify([bookArray])  


@app.route('/syllabusChapters')
@login_required
def syllabusChapters():
    book_name=request.args.get('book_name')
    class_val=request.args.get('class_val')
    board_id=request.args.get('board_id')
    subject_id=request.args.get('subject_id')
    #distinctChapterQuery="select distinct chapter_num, chapter_name from topic_detail where book_name= '"+book_name+"'and class_val ='"+class_val+"' and board_id='"+board_id+"' and subject_id='"+subject_id+"'"
    distinctChapterQuery="select distinct t1.chapter_num, t1.chapter_name from topic_detail t1 inner join book_details t2 "
    distinctChapterQuery=distinctChapterQuery+ "on t1.book_id=t2.book_id where t2.book_name= '"+book_name+"' and t1.class_val ='"+class_val+"' and board_id='"+board_id+"' and t1.subject_id='"+subject_id+"'"
    distinctChapters = db.session.execute(text(distinctChapterQuery)).fetchall()
    chapterArray=[]
    for val in distinctChapters:
        print(val.chapter_num)
        chapterArray.append(str(val.chapter_num)+":"+str(val.chapter_name))
    return jsonify([chapterArray]) 



@app.route('/syllabusTopics')
@login_required
def syllabusTopics():
    subject_id=request.args.get('subject_id')
    board_id=request.args.get('board_id')
    chapter_num=request.args.get('chapter_num')
    chapter_name=request.args.get('chapter_name')
    class_val = request.args.get('class_val')

    distinctTopicQuery = "select topic_id, topic_name from topic_detail where subject_id='"+subject_id+"' and board_id='"+board_id+"' and chapter_num='"+chapter_num+"' and chapter_name='"+chapter_name+"' and class_val='"+class_val+"'"
    print('Fetch Topics:'+str(distinctTopicQuery))
    distinctTopics = db.session.execute(text(distinctTopicQuery)).fetchall()
    topicArray=[]
    for val in distinctTopics:
        print(val.topic_id)
        topicArray.append(str(val.topic_id)+":"+str(val.topic_name))
    return jsonify([topicArray]) 



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
    else:
        print('#########Gotten into else')
        pass
    access_granted_email(userTableDetails.email,userTableDetails.username,school )
    return jsonify(["0"])



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
        topic_list=Topic.query.filter_by(class_val=int(form.class_val.data),subject_id=int(form.subject_name.data),chapter_num=int(form.chapter_num.data)).all()
        subject=MessageDetails.query.filter_by(msg_id=int(form.subject_name.data)).first()
        session['class_val']=form.class_val.data
        session['sub_name']=subject.description
        session['test_type_val']=form.test_type.data
        session['chapter_num']=form.chapter_num.data    
        form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(int(form.class_val.data))]
        form.chapter_num.choices= [(int(i['chapter_num']), str(i['chapter_num'])+' - '+str(i['chapter_name'])) for i in chapters(int(form.class_val.data),int(form.subject_name.data))]
        return render_template('questionBank.html',form=form,topics=topic_list)
    return render_template('questionBank.html',form=form,classSecCheckVal=classSecCheck())

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
    # [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.test_type.choices= [(i.description,i.description) for i in MessageDetails.query.filter_by(category='Test type').all()]
    # print(request.form['class_val'])
    # print(request.form['subject_id'])
    if request.method=='POST':
        if request.form['test_date']=='':
            # flash('Select Date')
            # form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(int(form.class_val.data))]
            return render_template('testBuilder.html',form=form)
        topic_list=Topic.query.filter_by(class_val=int(form.class_val.data),subject_id=int(form.subject_name.data)).all()
        subject=MessageDetails.query.filter_by(msg_id=int(form.subject_name.data)).first()
        session['class_val']=form.class_val.data
        session['date']=request.form['test_date']
        session['sub_name']=subject.description
        session['sub_id']=form.subject_name.data
        session['test_type_val']=form.test_type.data
        form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(int(form.class_val.data))]
        return render_template('testBuilder.html',form=form,topics=topic_list)
    return render_template('testBuilder.html',form=form,classSecCheckVal=classSecCheck())

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
    print('Inside Test builder file upload Test Type value:'+str(session.get('test_type_val',None)))
    #question_list=request.get_json()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    data=request.get_json()
    question_list=data[0]
    count_marks=data[1]
    document = Document()
    document.add_heading(schoolNameVal(), 0)
    document.add_heading('Class '+session.get('class_val',None)+" - "+session.get('test_type_val',None)+" - "+str(session.get('date',None)) , 1)
    document.add_heading("Subject : "+session.get('sub_name',None),2)
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
    file_name=str(teacher_id.school_id)+str(session.get('class_val',"0"))+str(session.get('sub_name',"0"))+str(session.get('test_type_val',"0"))+str(datetime.today().strftime("%Y%m%d"))+str(count_marks)+'.docx'
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

    testDetailsUpd = TestDetails(test_type=session.get('test_type_val',None), total_marks=str(count_marks),last_modified_date= datetime.now(),
        board_id='1001', subject_id=int(session.get('sub_id',None)),class_val=session.get('class_val',"0"),date_of_creation=datetime.now(),
        date_of_test=str(session.get('date',None)), school_id=teacher_id.school_id,test_paper_link=file_name_val, teacher_id=teacher_id.teacher_id)
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

    return render_template('testPapers.html',testPaperData=testPaperData,subjectNames=subjectNames,classSecCheckVal=classSecCheck())

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
    guardian=GuardianProfile.query.filter_by(user_id=current_user.id).all()
    student=[]
    for g in guardian:
        student_data=StudentProfile.query.filter_by(student_id=g.student_id).first()
        student.append(student_data)
    return render_template('guardianDashboard.html',students=student)

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
            print("Class Section:"+section.section)
            #this section is to load the page for the first class section if no query value has been provided
            if count==0:
                getClassVal = section.class_val
                getSection = section.section
                count+=1

        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val order by class_val")).fetchall()
        #if no value has been passed for class and section in query string then use the values fetched from db
        if qclass_val==None:
            qclass_val = getClassVal
            qsection=getSection
            
        selectedClassSection=ClassSection.query.filter_by(school_id=teacher.school_id, class_val=qclass_val, section=qsection).order_by(ClassSection.class_val).first()
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
        print('this is the number of topicRows' + str(len(topicRows)))

        courseDetailQuery = "select t1.*,  t2.description as subject from topic_detail t1, message_detail t2 "
        courseDetailQuery = courseDetailQuery + "where t1.subject_id=t2.msg_id "
        courseDetailQuery = courseDetailQuery + "and class_val= '" + str(qclass_val)+ "'"
        courseDetails= db.session.execute(text(courseDetailQuery)).fetchall()        
        #endOfQueries  
        #db.session.execute(text('call sp_performance_detail_load_feedback()'))
        db.session.commit()      
        return render_template('class.html', classSecCheckVal=classSecCheck(),classsections=classSections, qclass_val=qclass_val, qsection=qsection, class_sec_id=selectedClassSection.class_sec_id, distinctClasses=distinctClasses,topicRows=topicRows, courseDetails=courseDetails)
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
    return render_template('qrSessionScannerStudent.html',disconn=1,user_type_val=str(current_user.user_type),studentDetails=studentDetails)


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
        flash('This is not a valid id')
        return render_template('qrSessionScannerStudent.html',disconn=1)


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

@app.route('/leaderBoard')
def leaderBoard():
    form = LeaderBoardQueryForm()
    qclass_val = request.args.get("class_val")
    print('class:'+str(qclass_val))
    if current_user.is_authenticated:        
        user = User.query.filter_by(username=current_user.username).first_or_404()
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first() 
        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val order by class_val")).fetchall()    
        form.subject_name.choices = [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
        class_sec_id=ClassSection.query.filter_by(class_val=int(1),school_id=teacher.school_id).first()
        form.test_type.choices= [(i.description,i.description) for i in MessageDetails.query.filter_by(category='Test type').all()]

        form.testdate.choices = [(i.exam_date,i.exam_date) for i in ResultUpload.query.filter_by(class_sec_id=class_sec_id.class_sec_id).all()]
        available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher.school_id).all()  
        form.section.choices= [(i.section,i.section) for i in available_section]
        # query = "select *from public.fn_performance_leaderboard('"+ str(teacher.school_id) +"') where subjects='All' and section<>'All' order by marks desc, student_name "
        query = "select  * from fn_performance_leaderboard_detail('"+str(teacher.school_id)+"')"

        if qclass_val!='' and qclass_val is not None and str(qclass_val)!='None':
            where = " where class='"+str(qclass_val)+"'"
        else:
            where = ""
        query = query + where
        print('Query:'+query)
        leaderBoardData = db.session.execute(text(query)).fetchall()
        # student_list=StudentProfile.query.filter_by(class_sec_id=session.get('class_sec_id',None),school_id=session.get('school_id',None)).all()
        #print('Inside leaderboard')    
        for data in leaderBoardData:
            print('count:'+str(data.section))
            print('marks:'+str(data.marks))
    return render_template('leaderBoard.html',classSecCheckVal=classSecCheck(),form=form,distinctClasses=distinctClasses,leaderBoardData=leaderBoardData, qclass_val=qclass_val)

@app.route('/classDelivery')
@login_required
def classDelivery():
    form = ContentManager()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).order_by(ClassSection.class_val).all()]
    form.subject_name.choices = ''
    # [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.chapter_num.choices = ''
    # [(str(i.chapter_num), "Chapter - "+str(i.chapter_num)) for i in Topic.query.with_entities(Topic.chapter_num).distinct().order_by(Topic.chapter_num).all()]
    form.topics.choices = ''
    # [(str(i['topic_id']), str(i['topic_name'])) for i in topics(1,54)]
    form.content_type.choices = ''
    if current_user.is_authenticated:        
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    

        qtopic_id=request.args.get('topic_id')
        qsubject_id=request.args.get('subject_id')
        qclass_sec_id = request.args.get('class_sec_id')
        retake = request.args.get('retake')
        print('this is retake val: '+str(retake))
        contentData = ContentDetail.query.filter_by(topic_id=int(qtopic_id),archive_status='N').all()
        subject_name = MessageDetails.query.filter_by(msg_id=qsubject_id).all()
        subName = ''
        for sub in subject_name:
            subName = sub.description
            break
        print('Subject Name:'+str(subName))
        print('Content Data:'+str(contentData))
        q=0
        for content in contentData:
            print('This is Content Data:'+str(content.content_name)+' '+str(content.reference_link)+' '+str(content.last_modified_date))
            q=q+1
        print('Times:'+str(q))
        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).order_by(ClassSection.class_val).all()
        for classSec in classSections:
            print("class Section:"+str(classSec.section))
        currClassSecDet = ClassSection.query.filter_by(class_sec_id=qclass_sec_id).first()
        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val order by class_val")).fetchall()        
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


        
    return render_template('classDelivery.html', classSecCheckVal=classSecCheck(),classsections=classSections, currClassSecDet= currClassSecDet, distinctClasses=distinctClasses,form=form ,topicDet=topicDet ,bookDet=bookDet,topicTrackerDetails=topicTrackerDetails,contentData=contentData,subName=subName)



@app.route('/contentManager',methods=['GET','POST'])
@login_required
def contentManager():
    topic_list=None
    formContent = ContentManager()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    formContent.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).order_by(ClassSection.class_val).all()]
    formContent.subject_name.choices = ''
    # [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    formContent.chapter_num.choices = ''
    # [(str(i.chapter_num), "Chapter - "+str(i.chapter_num)) for i in Topic.query.with_entities(Topic.chapter_num).distinct().order_by(Topic.chapter_num).all()]
    formContent.topics.choices = ''
    # [(str(i['topic_id']), str(i['topic_name'])) for i in topics(1,54)]
    formContent.content_type.choices = ''
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form=QuestionBankQueryForm() # resusing form used in question bank 
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().order_by(ClassSection.class_val).filter_by(school_id=teacher_id.school_id).all()]
    form.subject_name.choices= ''
    form.chapter_num.choices= ''
    form.test_type.choices= [(i.description,i.description) for i in MessageDetails.query.filter_by(category='Test type').all()]
    if request.method=='POST':
        topic_list=Topic.query.filter_by(class_val=int(form.class_val.data),subject_id=int(form.subject_name.data),chapter_num=int(form.chapter_num.data)).all()
        subject=MessageDetails.query.filter_by(msg_id=int(form.subject_name.data)).first()
        session['class_val']=form.class_val.data
        session['sub_name']=subject.description
        session['test_type_val']=form.test_type.data
        session['chapter_num']=form.chapter_num.data    
        form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(int(form.class_val.data))]
        form.chapter_num.choices= [(int(i['chapter_num']), str(i['chapter_num'])+' - '+str(i['chapter_name'])) for i in chapters(int(form.class_val.data),int(form.subject_name.data))]
        return render_template('contentManager.html',form=form,formContent=formContent,topics=topic_list)
    return render_template('contentManager.html',classSecCheckVal=classSecCheck(),form=form,formContent=formContent)


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
    today = date.today()
    d4 = today.strftime("%b-%d-%Y")
    print(d4)
    if reference!='':
        contentData = ContentDetail(content_name=str(contentName),class_val=int(class_val),subject_id=int(selected_subject),
        topic_id=int(selected_topic),content_type=contentTypeId,reference_link=reference,archive_status='N',last_modified_date=d4)
        db.session.add(contentData)
    else:
        contentData = ContentDetail(content_name=str(contentName),class_val=int(class_val),subject_id=int(selected_subject),
        topic_id=int(selected_topic),content_type=contentTypeId,reference_link=contentUrl,archive_status='N',last_modified_date=d4)
        db.session.add(contentData)
    db.session.commit()
    flash("content Uploaded Successfully")
    return "Upload"

@app.route('/contentManagerDetails',methods=['GET','POST'])
def contentManagerDetails():
    contents=[]
    topicList=request.get_json()
    for topic in topicList:
        contentList = ContentDetail.query.filter_by(topic_id=int(topic),archive_status='N').all()
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
            print('Inside question id list')
            print(questionIDList)          
            questionListSize = len(questionIDList)

            print('Question list size:'+str(questionListSize))
            #creating a record in the session detail table  
            if questionListSize !=0:
                sessionDetailRowCheck = SessionDetail.query.filter_by(resp_session_id=responseSessionID).first()
                print('Date:'+str(print (dateVal)))
                print('Response Session ID:'+str(responseSessionID))
                print('If Question list size is not zero')
                print(sessionDetailRowCheck)
                if sessionDetailRowCheck==None:
                    print('if sessionDetailRowCheck is none')
                    print(sessionDetailRowCheck)
                    sessionDetailRowInsert=SessionDetail(resp_session_id=responseSessionID,session_status='80',teacher_id= teacherProfile.teacher_id,
                    class_sec_id=currClassSecRow.class_sec_id, test_id=str(qtest_id).strip(), last_modified_date = date.today())
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
                return render_template('feedbackCollectionTeachDev.html',classSecCheckVal=classSecCheck(), subject_id=qsubject_id, class_val = qclass_val, section = qsection,questions=questions, questionListSize = questionListSize, resp_session_id = responseSessionID,responseSessionIDQRCode=responseSessionIDQRCode,subjectName = subjectQueryRow.description, totalMarks=totalMarks, testType=testType)
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

        #sidebar queries
        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).order_by(ClassSection.class_val).all()
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
@login_required
def loadQuestionStud():
    question_id = request.args.get('question_id')
    totalQCount = request.args.get('total')
    qnum= request.args.get('qnum')
    ######################################################
    response_option = request.args.get('response_option')
    resp_session_id = request.args.get('resp_session_id')
    subject_id =  request.args.get('subject_id')
    last_q_id =  request.args.get('last_q_id')    
    print('Before String conversion:'+resp_session_id)
    print('This is the response session id in: ' + str(resp_session_id) )
    studentRow=StudentProfile.query.filter_by(user_id=current_user.id).first()
    #print('#######this is the current user id'+ str(current_user.id))
    resp_id = str(resp_session_id)
    sessionDetailRow = SessionDetail.query.filter_by(resp_session_id = resp_id).first()
    #print('########### Session details have been fetched')
    print(sessionDetailRow)
    teacherID = sessionDetailRow.teacher_id

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
        responseStudUpdateQuery=ResponseCapture(school_id=studentRow.school_id,student_id=studentRow.student_id,
            question_id= last_q_id, response_option=response_option, is_correct = ansCheck, teacher_id= teacherID,
            class_sec_id=studentRow.class_sec_id, subject_id = subject_id, resp_session_id = resp_session_id,last_modified_date= date.today())
        print('Question numbering')
        print(responseStudUpdateQuery)
        db.session.add(responseStudUpdateQuery)
        db.session.commit()

        
        ######################################################

    if int(qnum)< int(totalQCount):
        print('###############q number LESS THAN TOTAL Q COUNT###############')
        question = QuestionDetails.query.filter_by(question_id=question_id, archive_status='N').first()
        questionOp = QuestionOptions.query.filter_by(question_id=question_id).order_by(QuestionOptions.option).all()
        print('this is the last q id#################:'+last_q_id)
        return render_template('_questionStud.html',question=question, questionOp=questionOp,qnum = qnum,totalQCount = totalQCount, last_q_id=question_id)
    else:        
        print('###############q number MORE THAN TOTAL Q COUNT###############')
        totalMarksQuery = "select sum(suggested_weightage) as total_marks, count(*) as num_of_questions  from question_details where question_id in "
        totalMarksQuery =  totalMarksQuery +"(select distinct question_id from test_questions t1 inner join session_detail t2 on "
        totalMarksQuery =  totalMarksQuery +"t1.test_id=t2.test_id and t2.resp_session_id='"+str(resp_session_id)+"') "
        print('Total Marks Query:'+totalMarksQuery)
        totalMarksVal = db.session.execute(text(totalMarksQuery)).first()

        marksScoredQuery =  "select sum(suggested_weightage) as marks_scored, count(*) as correct_ans from question_details where question_id "
        marksScoredQuery=marksScoredQuery+"in (select distinct question_id from response_capture where is_correct='Y' and "
        marksScoredQuery=marksScoredQuery+"student_id="+str(studentRow.student_id)+")"
        marksScoredVal = db.session.execute(text(marksScoredQuery)).first()
        print('Marks Scored Query:'+marksScoredQuery)
        print('Marks Scored:'+str(marksScoredVal.marks_scored))
        print('Total Marks:'+str(totalMarksVal.total_marks))
        marksPercentage=0
        marksPercentage = (marksScoredVal.marks_scored/totalMarksVal.total_marks) *100
        print('Marks Percentage:'+str(marksPercentage))
        # try:
        #     print('Inside try')
        #     print('Marks Scored:'+marksScoredVal.marks_scored)
        #     print('Total Marks:'+totalMarksVal.total_marks)
        #     marksPercentage = (marksScoredVal.marks_scored/totalMarksVal.total_marks) *100 
        #     print('Marks Scored:'+marksScoredVal.marks_scored)
        #     print('Total Marks:'+totalMarksVal.total_marks)
        #     print(marksPercentage)
        # except:
        #     marksPercentage=0

        return render_template('_feedbackReportIndiv.html',marksPercentage=marksPercentage, marksScoredVal= marksScoredVal,totalMarksVal =totalMarksVal, student_id=studentRow.student_id, student_name= studentRow.full_name, resp_session_id = resp_session_id )
    


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

                    responsesForQuest=ResponseCapture(school_id=teacherIDRow.school_id,student_id=responseSplit[0],
                    question_id= splitVal[0], response_option= responseSplit[3], is_correct = ansCheck, teacher_id= teacherIDRow.teacher_id,
                    class_sec_id=studentDetailRow.class_sec_id, subject_id = questionDetailRow.subject_id, resp_session_id = responseSessionID,last_modified_date= datetime.now())
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
        responseResultQuery = "with total_marks_cte as ( "
        responseResultQuery = responseResultQuery + "select sum(suggested_weightage) as total_weightage, count(*) as num_of_questions  from question_details where question_id in "
        responseResultQuery = responseResultQuery + "(select distinct question_id from test_questions t1 inner join session_detail t2 on "
        responseResultQuery = responseResultQuery + "t1.test_id=t2.test_id and t2.resp_session_id='"+str(responseSessionID)+"') ) "
        responseResultQuery = responseResultQuery + "select distinct sp.roll_number, sp.full_name, sp.student_id, "
        responseResultQuery = responseResultQuery + "CASE WHEN rc.is_correct='Y' THEN SUM(qd.suggested_weightage) ELSE '0' END AS  points_scored , "
        responseResultQuery = responseResultQuery + "total_marks_cte.total_weightage "
        responseResultQuery = responseResultQuery + "from response_capture rc inner join student_profile sp on "
        responseResultQuery = responseResultQuery + "rc.student_id=sp.student_id "
        responseResultQuery = responseResultQuery + "inner join question_details qd on "
        responseResultQuery = responseResultQuery + "qd.question_id=rc.question_id "
        responseResultQuery = responseResultQuery + "and rc.resp_session_id='"+str(responseSessionID)+"', total_marks_cte "
        responseResultQuery = responseResultQuery + "group by sp.roll_number, sp.full_name, sp.student_id, total_marks_cte.total_weightage , rc.is_correct"

        print('Query:'+str(responseResultQuery))
        responseResultRow = db.session.execute(text(responseResultQuery)).fetchall()

        if responseResultRow != None:
            totalPointsScored =  0
            totalPointsLimit = 0   
            print(responseResultRow)
            print('ResultRow length:'+str(len(responseResultRow)))         
            for row in responseResultRow:
                totalPointsScored = totalPointsScored + row.points_scored
                totalPointsLimit = totalPointsLimit + row.total_weightage

            if totalPointsLimit !=0 and totalPointsLimit != None:
                classAverage = (totalPointsScored/totalPointsLimit) *100
            else:
                classAverage = 0
                print("total Points limit is zero")

            responseResultRowCount = len(responseResultRow)
        #print('Here is the questionListJson: ' + str(questionListJson))
    else:
        print("Error collecting data from ajax request. Some values could be null")

    if responseResultRowCount>0:
        return render_template('_feedbackReport.html', classSecCheckVal=classSecCheck(),responseResultRow= responseResultRow,classAverage =classAverage,  responseResultRowCount = responseResultRowCount, resp_session_id = responseSessionID)
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
    responseCaptureQuery = responseCaptureQuery +"qo.option as correct_option, "
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
    
    if section!=None:
        section = section.strip()    
    test_type=request.args.get('test_type')
    student_id=request.args.get('student_id')        
    dateVal = request.args.get('date')
    
    if dateVal ==None or dateVal=="":
        dateVal= datetime.today()
    
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    fromTestPerformance=0
          
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
        return jsonify(['No records found for the selected values'])
  
    



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
    testDetailQuery = testDetailQuery+ " inner join teacher_profile t5 on t5.teacher_id=t1.teacher_id  and t5.school_id='"+str(teacher_id.school_id)+"'"
    testDetailRows= db.session.execute(text(testDetailQuery)).fetchall()
    return render_template('classPerformance.html',classSecCheckVal=classSecCheck(),form=form, school_id=teacher_id.school_id, testDetailRows=testDetailRows)



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
    distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val order by class_val")).fetchall()        
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
    test_details = TestDetails.query.distinct().filter_by(class_val=qclass_val,school_id=teacher_id.school_id).all()
    for section in classSections:
            print("Class Section:"+section.section)
    subject_name = []
    if current_user.is_authenticated:
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        print('Class value:'+str(qclass_val))
        print('school_id:'+str(teacher_id.school_id))
        class_sec_id=ClassSection.query.filter_by(class_val=int(qclass_val),school_id=teacher_id.school_id,section=qsection).all()
        
        print(teacher_id.school_id)
        class_value = int(qclass_val)
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
        return render_template('resultUpload.html',classSecCheckVal=classSecCheck(),test_details=test_details,test_type=test_type,qclass_val=qclass_val,subject_name=subject_name,qsection=qsection, distinctClasses=distinctClasses, classsections=classSections,student_list=student_list)
        

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

@app.route('/performanceSummary')
def performanceSummary():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_value = request.args.get('class_val')
    section = request.args.get('section')
    subject = request.args.get('subject')
    subName = ''
    if(subject!='All'):
        subject_name = MessageDetails.query.filter_by(msg_id=subject).first()
        subName = subject_name.description
    else:
        subName = subject

    print('Inside performance Summary')
    query = "Select * from fn_overall_performance_summary("+str(teacher_id.school_id)+") where class='"+str(class_value)+"' and section='"+str(section)+"' and subject='"+str(subName)+"'"
    print(query)
    resultSet = db.session.execute(text(query))
    print(resultSet)
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
    return jsonify({'result' : resultArray})
    # return render_template('testPerformance.html',form=form,form1=form1,resultSet=resultSet)


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
    return render_template('resultUploadHistory.html',uploadHistoryRecords=uploadHistoryRecords)


@app.route('/uploadHistoryDetail',methods=['POST','GET'])
def uploadHistoryDetail():
    upload_id=request.args.get('upload_id')
    resultDetailQuery = "select distinct sp.full_name, sp.profile_picture, ru.total_marks, ru.marks_scored as marks_scored, md.description as test_type, ru.exam_date,cs.class_val, cs.section, ru.question_paper_ref "
    resultDetailQuery = resultDetailQuery + "from result_upload ru inner join student_profile sp on sp.student_id=ru.student_id "
    resultDetailQuery = resultDetailQuery + "inner join message_detail md on md.msg_id=ru.test_type "
    resultDetailQuery = resultDetailQuery + "and ru.upload_id='"+ str(upload_id) +"' inner join class_section cs on cs.class_sec_id=ru.class_sec_id order by marks_scored desc" 
    resultUploadRows = db.session.execute(text(resultDetailQuery)).fetchall()

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

    return render_template('_uploadHistoryDetail.html',resultUploadRows=resultUploadRows, class_val_record=class_val_record,section_record=section_record, test_type_record=test_type_record,exam_date_record=exam_date_record,question_paper_ref=question_paper_ref)

@app.route('/studentList/<class_val>/<section>/')
def studentList(class_val,section):
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    classSecRow = ClassSection.query.filter_by(class_val=class_val, section=section,school_id=teacher_id.school_id).first()
    students = StudentProfile.query.distinct().filter_by(class_sec_id=classSecRow.class_sec_id).all()
    studentArray = []

    for student in students:
        studentObj = {}
        studentObj['student_id'] = student.student_id
        studentObj['student_name'] = student.full_name
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
            question=QuestionDetails(class_val=int(request.form['class_val']),subject_id=int(request.form['subject_name']),question_description=request.form['question_desc'],
            reference_link=request.form['reference'],topic_id=int(request.form['topics']),question_type=form.question_type.data,suggested_weightage=int(request.form['weightage']),archive_status=str('N'))
            print(question)
            db.session.add(question)
            if form.question_type.data=='Subjective':
                question_id=db.session.query(QuestionDetails).filter_by(class_val=int(request.form['class_val']),topic_id=int(request.form['topics']),question_description=request.form['question_desc']).first()
                options=QuestionOptions(question_id=question_id.question_id,weightage=request.form['weightage'])
                print('Options Desc:'+str(options))
                db.session.add(options)
                db.session.commit()
                flash('Success')
                return render_template('questionBuilder.html')
            else:
                option_list=request.form.getlist('option_desc')
                question_id=db.session.query(QuestionDetails).filter_by(class_val=int(request.form['class_val']),topic_id=int(request.form['topics']),question_description=request.form['question_desc']).first()
                if request.form['correct']=='':
                    flash('Correct option not seleted !')
                    return render_template('questionBuilder.html')
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
                return render_template('questionBuilder.html')
        else:
            csv_file=request.files['file-input']
            df1=pd.read_csv(csv_file)
            for index ,row in df1.iterrows():
                if row['Question Type']=='MCQ1':
                    print("Inside MCQ")
                    question=QuestionDetails(class_val=int(request.form['class_val']),subject_id=int(request.form['subject_name']),question_description=row['Question Description'],
                    topic_id=row['Topic Id'],question_type='MCQ1',reference_link=request.form['reference-url'+str(index+1)],archive_status=str('N'),suggested_weightage=row['Suggested Weightage'])
                    db.session.add(question)
                    question_id=db.session.query(QuestionDetails).filter_by(class_val=int(request.form['class_val']),topic_id=row['Topic Id'],question_description=row['Question Description']).first()
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
                    question=QuestionDetails(class_val=int(request.form['class_val']),subject_id=int(request.form['subject_name']),question_description=row['Question Description'],
                    topic_id=row['Topic Id'],question_type='Subjective',reference_link=request.form['reference-url'+str(index+1)],archive_status=str('N'),suggested_weightage=row['Suggested Weightage'])
                    db.session.add(question)
            db.session.commit()
            flash('Successfully Uploaded !')
            return render_template('questionBuilder.html')
    return render_template('questionBuilder.html')



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
    if form.class_val.data!='None' and form.subject_name.data!='None' and  form.chapter_num.data!='None':
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
    for marksSubjectWise in marks:
        if marksSubjectWise=='-1':
            marksSubjectWise=0
            is_present=MessageDetails.query.filter_by(description='Not Present').first()
        else:
            is_present=MessageDetails.query.filter_by(description='Present').first()
        #print('Marks:'+marksSubjectWise)
        upload_id=str(teacher_id.school_id)+str(class_sec_id.class_sec_id)+str(subject_id) + str(test_type) + dt_string
        upload_id=upload_id.replace('-','')
        if testId=='':
            Marks=ResultUpload(school_id=teacher_id.school_id,student_id=list_id[count],
            exam_date=testdate,marks_scored=marksSubjectWise,class_sec_id=class_sec_id.class_sec_id,
            test_type=test_type,subject_id=subject_id,is_present=is_present.msg_id,total_marks=Tmarks,
            uploaded_by=teacher_id.teacher_id, upload_id=upload_id,last_modified_date=datetime.today(),question_paper_ref=paperUrl
            )
        else:
            Marks=ResultUpload(school_id=teacher_id.school_id,student_id=list_id[count],
            exam_date=testdate,marks_scored=marksSubjectWise,class_sec_id=class_sec_id.class_sec_id,
            test_type=test_type,subject_id=subject_id,is_present=is_present.msg_id,total_marks=Tmarks,test_id=testId,
            uploaded_by=teacher_id.teacher_id, upload_id=upload_id,last_modified_date=datetime.today()
            )
        db.session.add(Marks)
        count = count + 1
    db.session.execute(text('call sp_performance_detail_load()'))
    db.session.commit()
    flash('Login required !')
    print('Class_val:'+str(classValue)+'subject_id:'+str(subject_id)+'classSection:'+class_section+"testdate:"+testdate+"Total marks:"+Tmarks+"TestId:"+testId+"Test type:"+test_type)
    


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
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        board_id=SchoolProfile.query.with_entities(SchoolProfile.board_id).filter_by(school_id=teacher_id.school_id).first()
        subject_id=Topic.query.with_entities(Topic.subject_id).distinct().filter_by(class_val=int(class_val),board_id=board_id).all()
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

@app.route('/indivStudentProfile')
@login_required
def indivStudentProfile():    
    student_id=request.args.get('student_id')
    
    studentProfileQuery = "select full_name, email, phone, dob, gender,class_val,section,roll_number,school_adm_number,profile_picture from student_profile sp "
    studentProfileQuery = studentProfileQuery + "left join class_section cs on sp.class_sec_id= cs.class_sec_id "
    studentProfileQuery = studentProfileQuery + "left join address_detail ad on ad.address_id=sp.address_id "
    studentProfileQuery = studentProfileQuery + "where sp.student_id='"+str(student_id)+"'" 
        
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
    print(testResultQuery)
    testResultRows = db.session.execute(text(testResultQuery)).fetchall()


    overallSum = 0
    overallPerfValue = 0

    for rows in perfRows:
        overallSum = overallSum + int(rows.student_score)
        print(overallSum)
    try:
        overallPerfValue = round(overallSum/(len(perfRows)),2)    
    except:
        overallPerfValue=0
    
    guardianRows = GuardianProfile.query.filter_by(student_id=student_id).all()
    qrRows = studentQROptions.query.filter_by(student_id=student_id).all()

    qrAPIURL = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="
    

    qrArray=[]
    x = range(4)    

    for n in x:               
        optionURL = qrAPIURL+str(student_id)+ '-'+str(studentProfileRow.roll_number)+'-'+ studentProfileRow.full_name.replace(" ", "%20")+'@'+string.ascii_uppercase[n]
        qrArray.append(optionURL)
        print(optionURL)
    return render_template('_indivStudentProfile.html',studentProfileRow=studentProfileRow,guardianRows=guardianRows, 
        qrArray=qrArray,perfRows=perfRows,overallPerfValue=overallPerfValue,student_id=student_id,testCount=testCount,
        testResultRows = testResultRows)


@app.route('/studentProfile')
@login_required
def studentProfile():    
    qstudent_id=request.args.get('student_id')

    if qstudent_id==None or qstudent_id=='':
        form=studentPerformanceForm()
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    

        available_class=ClassSection.query.with_entities(ClassSection.class_val).distinct().order_by(ClassSection.class_val).filter_by(school_id=teacher.school_id).all()
        available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher.school_id).all()    
        available_test_type=MessageDetails.query.filter_by(category='Test type').all()
        available_student_list=StudentProfile.query.filter_by(school_id=teacher.school_id).all()


        class_list=[(str(i.class_val), "Class "+str(i.class_val)) for i in available_class]
        section_list=[(i.section,i.section) for i in available_section]    
        test_type_list=[(i.msg_id,i.description) for i in available_test_type]
        student_list=[(i.student_id,i.full_name) for i in available_student_list]

        #selectfield choices
        form.class_val1.choices = class_list
        form.section1.choices= ''
        # section_list    
        form.test_type1.choices=test_type_list
        form.student_name1.choices = ''
        print('we are in the form one')
        return render_template('studentProfileNew.html',form=form)
    else:
        if current_user.user_type==134:
            disconn=1
        else:
            disconn=0
        print(qstudent_id)
        return render_template('studentProfileNew.html',qstudent_id=qstudent_id,disconn=disconn)


    


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
    return render_template('help.html')


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
