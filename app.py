from flask import Flask, render_template, request, flash, redirect, url_for, Response,session,jsonify
from send_email import newsletterEmail, send_password_reset_email
from applicationDB import *
from qrReader import *
from config import Config
from forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm,ResultQueryForm,MarksForm, TestBuilderQueryForm,SchoolRegistrationForm, PaymentDetailsForm, addEventForm,QuestionBuilderQueryForm, SingleStudentRegistration, SchoolTeacherForm, feedbackReportForm, testPerformanceForm, studentPerformanceForm, QuestionUpdaterQueryForm,  QuestionBankQueryForm
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from logging.handlers import RotatingFileHandler
import os
import logging
import datetime as dt
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
from miscFunctions import subjects,topics,subjectPerformance,signs3Folder
from docx import Document
from docx.shared import Inches
from urllib.request import urlopen,Request
from io import StringIO
from collections import defaultdict
from sqlalchemy.inspection import inspect
#from flask_material import Material

app=Flask(__name__)
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
        dateVal= datetime.today().strftime("%d%m%Y")
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/alllearn.log'+str(dateVal), maxBytes=10240, backupCount=10)
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
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.search_form = SearchForm()
    

#helper methods
def school_name():
    if current_user.is_authenticated:
        teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        if teacher_id != None:
            school_name_row=SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
            if school_name!=None:
                name=school_name_row.school_name            
                return name
            else:
                return None            
        else:
            return None
    else:
        return None


@app.route("/loaderio-ad2552628971ece0389988c13933a170/")
def performanceTestLoaderFunction():
    return render_template("loaderio-ad2552628971ece0389988c13933a170.html")

@app.route("/account/")
@login_required
def account():
    return render_template('account.html',School_Name=school_name())

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
    folder_url=signs3Folder(folder_name,file_type)
    print(folder_url)
    print(s3)

    presigned_post = s3.generate_presigned_post(
      Bucket = S3_BUCKET,
      Key = folder_url+"/"+file_name,
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


@app.route('/schoolRegistration', methods=['GET','POST'])
@login_required
def schoolRegistration():  
    S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
    form = SchoolRegistrationForm()
    form.board.choices=[(str(i.description), str(i.description)) for i in MessageDetails.query.with_entities(MessageDetails.description).distinct().filter_by(category='Board').all()]
    if form.validate_on_submit():
        address_id=Address.query.filter_by(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data).first()
        if address_id is None:
            address_data=Address(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data,country=form.country.data)
            db.session.add(address_data)
            address_id=db.session.query(Address).filter_by(address_1=form.address1.data,address_2=form.address2.data,locality=form.locality.data,city=form.city.data,state=form.state.data,pin=form.pincode.data).first()
        board_id=MessageDetails.query.filter_by(description=form.board.data).first()
        school_picture=request.files['school_image']
        school_picture_name=request.form['file-input']       
        school=SchoolProfile(school_name=form.schoolName.data,board_id=board_id.msg_id,address_id=address_id.address_id,registered_date=dt.datetime.now())
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
            class_data=ClassSection(class_val=int(class_val[i]),section=class_section[i],student_count=int(student_count[i]),school_id=school_id.school_id)
            db.session.add(class_data)
        teacher=TeacherProfile(school_id=school.school_id,email=current_user.email,user_id=current_user.id)
        db.session.add(teacher)
        db.session.commit()
        data=ClassSection.query.filter_by(school_id=school_id.school_id).all()
        flash('Succesfull Resgistration !')
        return render_template('schoolRegistrationSuccess.html',data=data,School_Name=school_name())
    return render_template('schoolRegistration.html',form=form)

@app.route('/teacherRegistration',methods=['GET','POST'])
@login_required
def teacherRegistration():
    school_name_val = school_name()
    
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
                    teacher_data=TeacherProfile(teacher_name=teacher_name[i],school_id=teacher_id.school_id,class_sec_id=class_sec_id.class_sec_id,email=teacher_email[i],subject_id=int(teacher_subject[i]))
                    db.session.add(teacher_data)
                else:
                    teacher_data=TeacherProfile(teacher_name=teacher_name[i],school_id=teacher_id.school_id,email=teacher_email[i],subject_id=int(teacher_subject[i]))
                    db.session.add(teacher_data)
            db.session.commit()
            flash('Successful registration !')
            return render_template('teacherRegistration.html',form=form,School_Name=school_name())
        return render_template('teacherRegistration.html',form=form,School_Name=school_name())

@app.route('/bulkStudReg')
def bulkStudReg():
    return render_template('_bulkStudReg.html')


@app.route('/singleStudReg')
def singleStudReg():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher_id.school_id).all()
    section_list=[(i.section,i.section) for i in available_section]
    form=SingleStudentRegistration()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()]
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
            class_sec=ClassSection.query.filter_by(class_val=int(form.class_val.data),section=form.section.data).first()
            gender=MessageDetails.query.filter_by(description=form.gender.data).first()
            student=StudentProfile(first_name=form.first_name.data,last_name=form.last_name.data,full_name=form.first_name.data +" " + form.last_name.data,
            school_id=teacher_id.school_id,class_sec_id=class_sec.class_sec_id,gender=gender.msg_id,
            dob=request.form['birthdate'],phone=form.phone.data,profile_picture=request.form['profile_image'],address_id=address_id.address_id,school_adm_number=form.school_admn_no.data,
            roll_number=int(form.roll_number.data))
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
            return render_template('studentRegistration.html',School_Name=school_name())
        else:
            csv_file=request.files['file-input']
            df1=pd.read_csv(csv_file)
            df1=df1.replace(np.nan, '', regex=True)
            print(df1)
            for index ,row in df1.iterrows():
                address_data=Address(address_1=row['address_1'],address_2=row['address_2'],locality=row['locality'],city=row['city'],state=row['state'],pin=str(row['pin']),country=row['country'])
                db.session.add(address_data)
                address_id=db.session.query(Address).filter_by(address_1=row['address_1'],address_2=row['address_2'],locality=row['locality'],city=row['city'],state=row['state'],pin=str(row['pin']),country=row['country']).first()
                teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
                class_sec=ClassSection.query.filter_by(class_val=row['class_val'],section=row['section']).first()
                gender=MessageDetails.query.filter_by(description=row['gender']).first()
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
            return render_template('studentRegistration.html',School_Name=school_name())
    return render_template('studentRegistration.html',School_Name=school_name())


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
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template(
        'edit_profile.html', title='Edit Profile', form=form,School_Name=school_name())


@app.route('/')
@app.route('/index')
@app.route('/dashboard')
@login_required
def index():
    user = User.query.filter_by(username=current_user.username).first_or_404()        
    teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    

    school_name_val = school_name()
    
    if school_name_val ==None:
        print('did we reach here')
        return redirect(url_for('disconnectedAccount'))
    else:
    #####Fetch school perf graph information##########
        performanceQuery = "select * from fn_class_performance("+str(teacher.school_id)+") order by perf_date"
        performanceRows = db.session.execute(text(performanceQuery)).fetchall()
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


        #dateRange = performanceRows.date
        #below code needs to be rejected. Only being kept for reference right now
        #df = pd.read_csv('data.csv').drop('Open', axis=1)
        #chart_data = df.to_dict(orient='records')
        #chart_data = json.dumps(chart_data, indent=2)
        #data = {'chart_data': chart_data}
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
        return render_template('dashboard.html',title='Home Page',School_Name=school_name(), 
            graphJSON=graphJSON, topicToCoverDetails = topicToCoverDetails, EventDetailRows = EventDetailRows, topStudentsRows = topStudentsRows)


@app.route('/disconnectedAccount')
@login_required
def disconnectedAccount():    
    return render_template('disconnectedAccount.html', title='Disconnected Account', disconn = 1,School_Name=school_name())

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
        "submitPost.html", title='Submit Post', form=form, posts=posts,School_Name=school_name())


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

    return render_template('explore.html', title='Explore', posts=posts,School_Name=school_name())


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()    
    print(user.id)
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc())
    school_name_val = school_name()
    
    if school_name_val ==None:
        print('did we reach here')
        return redirect(url_for('disconnectedAccount'))
    else:
        return render_template('user.html', user=user, posts=posts,School_Name=school_name())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for('login'))
        login_user(user,remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
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
            newsletterEmail(email, name)
            return render_template('newsletterSuccess.html')
        else:
            return render_template('index.html',text='Error: Email already used.')

@app.route('/feeManagement')
@login_required
def feeManagement():
    return render_template('feeManagement.html',School_Name=school_name())


@app.route('/questionBank',methods=['POST','GET'])
@login_required
def questionBank():
    topic_list=None
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form=QuestionBankQueryForm()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()]
    form.subject_name.choices= ''
#  [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.chapter_num.choices= [(str(i.chapter_num), "Chapter - "+str(i.chapter_num)) for i in Topic.query.with_entities(Topic.chapter_num).distinct().order_by(Topic.chapter_num).all()]
    form.test_type.choices= [(i.description,i.description) for i in MessageDetails.query.filter_by(category='Test type').all()]
    if request.method=='POST':
        # if request.form['chapter_num']=='':
        #     flash('Select Chapter')
        #     form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(int(form.class_val.data))]
        #     return render_template('questionBank.html',form=form,School_Name=school_name())
        topic_list=Topic.query.filter_by(class_val=int(form.class_val.data),subject_id=int(form.subject_name.data),chapter_num=int(form.chapter_num.data)).all()
        subject=MessageDetails.query.filter_by(msg_id=int(form.subject_name.data)).first()
        session['class_val']=form.class_val.data
        # session['date']=request.form['test_date']
        session['sub_name']=subject.description
        session['test_type_val']=form.test_type.data
        session['chapter_num']=form.chapter_num.data
        form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(int(form.class_val.data))]
        return render_template('questionBank.html',form=form,School_Name=school_name(),topics=topic_list)
    return render_template('questionBank.html',form=form,School_Name=school_name())

@app.route('/questionBankQuestions',methods=['GET','POST'])
def questionBankQuestions():
    questions=[]
    topicList=request.get_json()
    for topic in topicList:
        # question_Details=QuestionDetails.query.filter_by(QuestionDetails.topic_id == int(topic)).first()
        # questionList = QuestionDetails.query.join(QuestionOptions, QuestionDetails.question_id==QuestionOptions.question_id).add_columns(QuestionDetails.question_id, QuestionDetails.question_description, QuestionDetails.question_type, QuestionDetails.suggested_weightage).filter(QuestionDetails.topic_id == int(topic)).filter(QuestionOptions.is_correct=='Y').all()
        questionList = QuestionDetails.query.filter_by(topic_id=int(topic)).all()
        questions.append(questionList)
        for q in questionList:
            print("Question List"+str(q))
    print("Inside questionBankquestions")
    return render_template('questionBankQuestions.html',questions=questions,School_Name=school_name())

@app.route('/questionBankFileUpload',methods=['GET','POST'])
def questionBankFileUpload():
    #question_list=request.get_json()
    data=request.get_json()
    question_list=data[0]
    count_marks=data[1]
    document = Document()
    document.add_heading(school_name(), 0)
    document.add_heading('Class '+session.get('class_val',None)+" - "+session.get('test_type_val',None)+" - "+str(session.get('date',None)) , 1)
    document.add_heading("Subject : "+session.get('sub_name',None),2)
    document.add_heading("Total Marks : "+str(count_marks),3)
    p = document.add_paragraph()
    for question in question_list:
        data=QuestionDetails.query.filter_by(question_id=int(question)).first()
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
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()]
    form.subject_name.choices= ''
    # [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.test_type.choices= [(i.description,i.description) for i in MessageDetails.query.filter_by(category='Test type').all()]
    # print(request.form['class_val'])
    # print(request.form['subject_id'])
    if request.method=='POST':
        if request.form['test_date']=='':
            # flash('Select Date')
            # form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(int(form.class_val.data))]
            return render_template('testBuilder.html',form=form,School_Name=school_name())
        topic_list=Topic.query.filter_by(class_val=int(form.class_val.data),subject_id=int(form.subject_name.data)).all()
        subject=MessageDetails.query.filter_by(msg_id=int(form.subject_name.data)).first()
        session['class_val']=form.class_val.data
        session['date']=request.form['test_date']
        session['sub_name']=subject.description
        session['sub_id']=form.subject_name.data
        session['test_type_val']=form.test_type.data
        form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(int(form.class_val.data))]
        return render_template('testBuilder.html',form=form,School_Name=school_name(),topics=topic_list)
    return render_template('testBuilder.html',form=form,School_Name=school_name())

@app.route('/testBuilderQuestions',methods=['GET','POST'])  
def testBuilderQuestions():
    questions=[]
    topicList=request.get_json()
    for topic in topicList:
        questionList = QuestionDetails.query.join(QuestionOptions, QuestionDetails.question_id==QuestionOptions.question_id).add_columns(QuestionDetails.question_id, QuestionDetails.question_description, QuestionDetails.question_type, QuestionOptions.weightage).filter(QuestionDetails.topic_id == int(topic)).filter(QuestionOptions.is_correct=='Y').all()
        questions.append(questionList)
    return render_template('testBuilderQuestions.html',questions=questions,School_Name=school_name())

@app.route('/testBuilderFileUpload',methods=['GET','POST'])
def testBuilderFileUpload():
    #question_list=request.get_json()
    data=request.get_json()
    question_list=data[0]
    count_marks=data[1]
    document = Document()
    document.add_heading(school_name(), 0)
    document.add_heading('Class '+session.get('class_val',None)+" - "+session.get('test_type_val',None)+" - "+str(session.get('date',None)) , 1)
    document.add_heading("Subject : "+session.get('sub_name',None),2)
    document.add_heading("Total Marks : "+str(count_marks),3)
    p = document.add_paragraph()
    for question in question_list:
        data=QuestionDetails.query.filter_by(question_id=int(question)).first()
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

    #topicFromTracker = TopicTracker.query.filter_by(school_id = teacher.school_id, topic_id=qtopic_id).first()
    #topicFromTracker.is_covered='N'
    #topicFromTracker.reteach_count=int(topicFromTracker.reteach_count)+1
    #db.session.commit()

    #test_type, total_marks, year, month, last_modified_date, 
    #board_id, subject_id, class_val, date_of creation, date_of_test,
    #schoold_id, teacher_id, test_paper_link

    file_name_val='https://'+os.environ.get('S3_BUCKET_NAME')+'.s3.ap-south-1.amazonaws.com/test_papers/'+file_name

    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()

    testDetailsUpd = TestDetails(test_type=session.get('test_type_val',None), total_marks=str(count_marks),last_modified_date= datetime.utcnow(),
        board_id='1001', subject_id=int(session.get('sub_id',None)),class_val=session.get('class_val',"0"),date_of_creation=datetime.utcnow(),
        date_of_test=str(session.get('date',None)), school_id=teacher_id.school_id,test_paper_link=file_name_val, teacher_id=current_user.id)
    db.session.add(testDetailsUpd)
    db.session.commit()
    return render_template('testPaperDisplay.html',file_name=file_name_val)

@app.route('/testPapers')
@login_required
def testPapers():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #testPaperData= TestDetails.query.filter_by(school_id=teacher_id.school_id).join(MessageDetails,MessageDetails.msg_id==TestDetails.subject_id).all()
    testPaperData= TestDetails.query.filter_by(school_id=teacher_id.school_id).all()
    subjectNames=MessageDetails.query.filter_by(category='Subject')
    #for val in testPaperData:
    #    for row in val.message_detail:
    #        print(row.description)
    return render_template('testPapers.html',School_Name=school_name(),testPaperData=testPaperData,subjectNames=subjectNames)

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html',School_Name=school_name())

@app.route('/schoolPerformanceRanking')
@login_required
def schoolPerformanceRanking():
    return render_template('schoolPerformanceRanking.html',School_Name=school_name())

@app.route('/recommendations')
@login_required
def recommendations():
    return render_template('recommendations.html',School_Name=school_name())


@app.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html',School_Name=school_name())

@app.route('/guardianDashboard')
@login_required
def guardianDashboard():
    guardian=GuardianProfile.query.filter_by(user_id=current_user.id).all()
    student=[]
    for g in guardian:
        student_data=StudentProfile.query.filter_by(student_id=g.student_id).first()
        student.append(student_data)
    return render_template('guardianDashboard.html',students=student,School_Name=school_name())

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


        return render_template('studentPerfDetails.html',date=date,subjects=subject,students=student,School_Name=school_name())
    return render_template('performanceDetails.html',students=student,School_Name=school_name(), student_id=student_id,form1=form1)


@app.route('/studentfeedbackreporttemp')
def studentfeedbackreporttemp():
    student_name=request.args.get('student_name')
    return render_template('studentfeedbackreporttemp.html',student_name=student_name,School_Name=school_name())

@app.route('/class')
@login_required
def classCon():
    if current_user.is_authenticated:        
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
        qclass_val = request.args.get('class_val',1)
        qsection=request.args.get('section','A')

        #db query

        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).all()
        for section in classSections:
            print("Class Section:"+section.section)
        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val")).fetchall()

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
        return render_template('class.html', classsections=classSections, qclass_val=qclass_val, qsection=qsection, class_sec_id=selectedClassSection.class_sec_id, distinctClasses=distinctClasses,topicRows=topicRows, courseDetails=courseDetails,School_Name=school_name())
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

# @app.route('/questionUpdateUpload')
# def questionUpdateUpload():
#     return render_template('questionUpdateUpload.html')

#new mobile specific pages


@app.route('/mobDashboard')
def mobDashboard():
    return render_template('mobDashboard.html')

@app.route('/qrSessionScanner')
@login_required
def qrSessionScanner():
    return render_template('qrSessionScanner.html')


@app.route('/mobFeedbackCollection')
def mobQuestionLoader():
    resp_session_id=request.args.get('resp_session_id')
    print(resp_session_id)
    
    return render_template('mobFeedbackCollection.html')


@app.route('/mobQuestion')
def mobQuestion():
    return render_template('_mobQuestion.html')


@app.route('/mobResponseCapture')
def mobResponseCapture():
    return render_template('_mobResponseCapture.html')

@app.route('/mobResponseResult')
def mobResponseResult():
    return render_template('_mobResponseResult.html')

#end of mobile specific pages





@app.route('/updateQuestion')
def updateQuestion():
    question_id = request.args.get('question_id')
    updatedCV = request.args.get('updatedCV')
    topicId = request.args.get('topicName')
    subId = request.args.get('subName')
    qType = request.args.get('qType')
    qDesc = request.args.get('qDesc')
    correctOption = request.args.get('correctOption')
    weightage = request.args.get('weightage')
    imageUrl = request.args.get('preview')
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
    print("Updated class Value:"+updatedCV)
    print(str(updatedCV)+" "+str(topicId)+" "+str(subId)+" "+str(qType)+" "+str(qDesc)+" "+str(correctOption)+" "+str(weightage)+" "+str(imageUrl))
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()]
    form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.topics.choices=[(str(i['topic_id']), str(i['topic_name'])) for i in topics(1,54)]
    flag = False
    # updateQuery = "update question_details t1 set topic_id='" + str(topicId) + "' where question_id='" + question_id + "'"
    updateQuery = "update question_details set class_val='" + str(updatedCV) +  "',topic_id='"+ str(topicId) + "',subject_id='"+ str(subId) + "',question_type='" + str(qType) + "',question_description='"+ str(qDesc) + "',reference_link='"+ str(imageUrl) +"' where question_id='" + str(question_id) + "'"

    queryOneExe = db.session.execute(text(updateQuery))
    updateWeightage = "update question_details set suggested_weightage='" + str(weightage) + "' where question_id='" + str(question_id) + "'" 
    querytwoExe = db.session.execute(text(updateWeightage))

    option_id_list = QuestionOptions.query.filter_by(question_id=question_id).order_by(QuestionOptions.option_id).all()
    print(option_id_list)
    i=0
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
    if str(correctOption)!='':
        updatequery1 = "update question_options set is_correct='N' where is_correct='Y' and question_id='" +str(question_id)+"'"
        update1 = db.session.execute(text(updatequery1))
        updateCorrectOption = "update question_options set is_correct='Y' where option_desc='"+str(correctOption)+"' and question_id='"+str(question_id)+"'"
        print(updateCorrectOption)
        updateOp = db.session.execute(text(updateCorrectOption))
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
    #query = "select option_desc from question_options where question_id='" + question_id + "'"
    #avail_options = db.session.execute(text(query)).fetchall()
    # if avail_options:
    #     options = json.dumps(avail_options)
    # for option in avail_options:
    #     ans = []
    #     print(option)
    #     ans.append(option)
    questionOptionsList=[]
    for value in questionOptionResults:
        print("This is the value: "+str(value))        
        questionOptionsList.append(value.option+". "+value.option_desc)

    print(questionOptionsList)

    return jsonify([questionOptionsList])


@app.route('/questionDetails')
def questionDetails():
    flag = True
    question_id = request.args.get('question_id')
    print("Question Id-:"+question_id)
    form = QuestionBuilderQueryForm()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()]
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
        print(query)
        avail_options = db.session.execute(text(query)).fetchall()
        queryCorrectoption = "select option_desc from question_options where is_correct='Y' and question_id='" + question_id + "'"  
        print(queryCorrectoption)
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

@app.route('/classDelivery')
@login_required
def classDelivery():
    if current_user.is_authenticated:        
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    

        qtopic_id=request.args.get('topic_id')
        qsubject_id=request.args.get('subject_id')
        qclass_sec_id = request.args.get('class_sec_id')
        retake = request.args.get('retake')
        print('this is retake val: '+str(retake))


        #db query 
            #sidebar
        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).order_by(ClassSection.class_val).all()
        for classSec in classSections:
            print("class Section:"+str(classSec.section))
        currClassSecDet = ClassSection.query.filter_by(class_sec_id=qclass_sec_id).first()
        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val")).fetchall()        
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


        
    return render_template('classDelivery.html', classsections=classSections, currClassSecDet= currClassSecDet, distinctClasses=distinctClasses,topicDet=topicDet ,bookDet=bookDet,topicTrackerDetails=topicTrackerDetails,School_Name=school_name())




@app.route('/feedbackCollection', methods=['GET', 'POST'])
@login_required
def feedbackCollection():
    if request.method == 'POST':
        allCoveredTopics = request.form.getlist('topicCheck')
        class_val = request.form['class_val']
        section = request.form['section']
        subject_id = request.form['subject_id']

        print("topic List "+str(allCoveredTopics))
        print("section  is = " + str(section))
#
        #sidebar queries
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    

        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).order_by(ClassSection.class_val).all()
        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val")).fetchall()
        # end of sidebarm
    
        #start of - db update to ark the checked topics as completed
        teacherProfile = TeacherProfile.query.filter_by(user_id=current_user.id).first()
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

        questionList = QuestionDetails.query.filter(QuestionDetails.topic_id.in_(currCoveredTopics),QuestionDetails.question_type.like('%MCQ%')).all()  
        questionListSize = len(questionList)

        responseSessionID = str(dateVal) + str(subject_id) + str(classSections.class_sec_id)
        responseSessionIDQRCode = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="+responseSessionID
        #changes for use with PC+ mobile cam combination hahaha
        if questionListSize >0:
            sessionDetailRowInsert=SessionDetail(resp_session_id=responseSessionID,session_status='80',teacher_id= teacherProfile.teacher_id,
                        class_sec_id=classSections.class_sec_id, current_question='0')
            db.session.add(sessionDetailRowInsert)
            db.session.commit()

            #respSessionQuestionRowInsert = RespSessionQuestion()



        if teacherProfile.device_preference==78:        
            return render_template('feedbackCollection.html', subject_id=subject_id,classSections = classSections, distinctClasses = distinctClasses, class_val = class_val, section = section, questionList = questionList, questionListSize = questionListSize,School_Name=school_name())
        else:
            return render_template('feedbackCollectionExternalCam.html', responseSessionIDQRCode = responseSessionIDQRCode, responseSessionID = responseSessionID,  subject_id=subject_id,classSections = classSections, distinctClasses = distinctClasses, class_val = class_val, section = section, questionList = questionList, questionListSize = questionListSize,School_Name=school_name())
    else:
        return redirect(url_for('classCon'))


@app.route('/currentQuestionID')
@login_required
def curentQuestionID():
    resp_session_id = request.args.get('resp_session_id')
    sessionDetailRow = SessionDetail.query.filter_by(resp_session_id=resp_session_id).first()
    if sessionDetailRow.session_status=='80':
        


@app.route('/loadQuestion')
@login_required
def loadQuestion():
    question_id = request.args.get('question_id')
    totalQCount = request.args.get('total')
    qnum= request.args.get('qnum')
    question = QuestionDetails.query.filter_by(question_id=question_id).first()
    questionOp = QuestionOptions.query.filter_by(question_id=question_id).all()
    for option in questionOp:
        print(option.option_desc)
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
    responseList=request.json
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
                    
                    studentDetailQuery = "select class_sec_id from student_profile where student_id=" + responseSplit[0]
                    studentDetailRow = db.session.execute(text(studentDetailQuery)).first()

                    #studentDetailQuery = "select class_sec_id from student_profile where student_id=" + responseSplit[0]
                    questionDetailRow = QuestionDetails.query.filter_by(question_id=splitVal[0]).first()
                    
                    dateVal= datetime.today().strftime("%d%m%Y")

                    responseSessionID = str(dateVal) + str(questionDetailRow.subject_id) + str(studentDetailRow.class_sec_id)
                    print('this is the response session id: ' + responseSessionID)
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
                    class_sec_id=studentDetailRow.class_sec_id, subject_id = questionDetailRow.subject_id, resp_session_id = responseSessionID,last_modified_date= datetime.utcnow())
                    db.session.add(responsesForQuest)
                    db.session.commit()
                #flash('Response Entered')
                return jsonify(['Data ready for entry'])
    return jsonify(['No records entered to DB'])
  
@app.route('/feedbackReport')
def feedbackReport():    
    questionListJson=request.args.get('question_id')
    class_val=request.args.get('class_val')
    subject_id=request.args.get('subject_id')
    #print('here is the class_val '+ str(class_val))
    section=request.args.get('section')
    section = section.strip()
    dateVal = request.args.get('date')
    #print('here is the section '+ str(section))
    #if (questionListJson != None) and (class_val != None) and (section != None):
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()

    if (class_val != None) and (section != None):

        classSecRow = ClassSection.query.filter_by(class_val=class_val, section=section, school_id=teacher.school_id).first()       
        print('here is the subject_id: '+ str(subject_id))
        #questionDetailRow = QuestionDetails.query.filter_by(question_id=questionListJson[1]).first()
        
        if dateVal == None or dateVal=="":
            dateVal= datetime.today().strftime("%d%m%Y")
        else:
            tempDate=dt.datetime.strptime(dateVal,'%Y-%m-%d').date()
            dateVal= tempDate.strftime("%d%m%Y")

        responseSessionID = str(dateVal) + str(subject_id) + str(classSecRow.class_sec_id)
        print('Here is response session id in feedback report: ' + responseSessionID)
        responseResultQuery = "WITH sum_cte AS ( "
        responseResultQuery = responseResultQuery + "select sum(weightage) as total_weightage  from  "
        responseResultQuery = responseResultQuery + "question_options where question_id in  "
        responseResultQuery = responseResultQuery + "(select distinct question_id from response_capture where resp_session_id='" + responseSessionID + "')) "
        responseResultQuery = responseResultQuery + "select distinct sp.roll_number, sp.full_name, sp.student_id, "
        responseResultQuery = responseResultQuery + "SUM(qo.weightage) as points_scored, "
        responseResultQuery = responseResultQuery + "sum_cte.total_weightage "
        responseResultQuery = responseResultQuery + "from  "
        responseResultQuery = responseResultQuery + "student_profile sp  "
        responseResultQuery = responseResultQuery + "inner join  "
        responseResultQuery = responseResultQuery + "response_capture rc on sp.student_id=rc.student_id  "
        responseResultQuery = responseResultQuery + "inner join  "
        responseResultQuery = responseResultQuery + "question_options qo on rc.question_id=qo.question_id  "
        responseResultQuery = responseResultQuery + "and rc.response_option = qo.option "
        responseResultQuery = responseResultQuery + "inner join  "
        responseResultQuery = responseResultQuery + "question_options qo2 on  "
        responseResultQuery = responseResultQuery + "rc.question_id=qo2.question_id "
        responseResultQuery = responseResultQuery + "and qo2.is_correct='Y', "        
        responseResultQuery = responseResultQuery + "sum_cte "
        responseResultQuery = responseResultQuery + "where resp_session_id = '" + responseSessionID + "' "
        responseResultQuery = responseResultQuery + "group by  sp.roll_number, sp.full_name, sp.student_id, rc.response_option, qo2.weightage, sum_cte.total_weightage"


        responseResultRow = db.session.execute(text(responseResultQuery)).fetchall()

        if responseResultRow != None:
            totalPointsScored =  0
            totalPointsLimit = 0            
            for row in responseResultRow:
                totalPointsScored = totalPointsScored + row.points_scored
                totalPointsLimit = totalPointsLimit + row.total_weightage

            if totalPointsLimit !=0 and totalPointsLimit != None:
                classAverage = (totalPointsScored/totalPointsLimit) *100
            else:
                classAverage = 0
                print("total Points limit is zero")

            responseResultRowCount = len(responseResultRow)
        print('Here is the questionListJson: ' + str(questionListJson))
    else:
        print("Error collecting data from ajax request. Some values could be null")

    if responseResultRowCount>0:
        return render_template('_feedbackReport.html', responseResultRow= responseResultRow,classAverage =classAverage,  responseResultRowCount = responseResultRowCount, resp_session_id = responseSessionID)
    else:
         return jsonify(['No Data for the selected Date'])


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
    responseCaptureQuery = responseCaptureQuery +"inner join question_Details qd on rc.question_id = qd.question_id  "    
    responseCaptureQuery = responseCaptureQuery +"inner join question_options qo on qo.question_id = rc.question_id and qo.is_correct='Y'  "
    responseCaptureQuery = responseCaptureQuery +"left join question_options qo2 on qo2.question_id = rc.question_id and qo2.option = rc.response_option "
    responseCaptureQuery = responseCaptureQuery +"where student_id='" +  student_id + "'"

    responseCaptureRow = db.session.execute(text(responseCaptureQuery)).fetchall()

    return render_template('studentFeedbackReport.html',student_name=student_name, student_id=student_id, resp_session_id = resp_session_id, responseCaptureRow = responseCaptureRow)

@app.route('/testPerformance')
@login_required
def testPerformance():
    user = User.query.filter_by(username=current_user.username).first_or_404()        
    teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
    
    #setting up testperformance form
    form=testPerformanceForm()        

    available_class=ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher.school_id).all()
    available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher.school_id).all()    
    available_test_type=MessageDetails.query.filter_by(category='Test type').all()


    class_list=[(str(i.class_val), "Class "+str(i.class_val)) for i in available_class]
    section_list=[(i.section,i.section) for i in available_section]    
    test_type_list=[(i.msg_id,i.description) for i in available_test_type]

    #selectfield choices
    form.class_val.choices = class_list
    form.section.choices= ''
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

    #selectfield choices
    form1.class_val1.choices = class_list
    form1.section1.choices= ''
    # section_list    
    form1.test_type1.choices=test_type_list
    form1.student_name1.choices = ''
    # student_list

    

     #####Fetch school perf graph information##########
    performanceQuery = "select * from fn_class_performance("+str(teacher.school_id)+") order by perf_date"
    performanceRows = db.session.execute(text(performanceQuery)).fetchall()
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
    return render_template('testPerformance.html',graphJSON=graphJSON,form=form,form1=form1,School_Name=school_name())


@app.route('/testPerformanceGraph')
@login_required
def testPerformanceGraph():    
    class_val=request.args.get('class_val')
    section=request.args.get('section')
    section = section.strip()    
    test_type=request.args.get('test_type')
    #print('here is the class_val '+ str(class_val))
    dateVal = request.args.get('date')
    
    if dateVal ==None or dateVal=="":
        dateVal= datetime.today()

    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    classSectionRows=ClassSection.query.filter_by(class_val=int(class_val),section=section, school_id=teacher.school_id).first()

    
    #testPerformanceRecords = db.session.query(StudentProfile.full_name,PerformanceDetail.student_score,
    #    MessageDetails.description)).join(StudentProfile).join(MessageDetails, MessageDetails.msg_id==PerformanceDetail.subject_id).filter_by(class_sec_id=classSectionRows.class_sec_id, date=dateVal,test_type=test_type).all()
    
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

        #result = defaultdict(list)
        #for obj in testPerformanceRecords:
        #    instance = inspect(obj)
        #    for key, x in instance.attrs.items():
        #        result[key].append(x.value)
        #
        #df = pd.DataFrame(result)

        df = pd.DataFrame( [[ij for ij in i] for i in testPerformanceRecords])
        df.rename(columns={0: 'full_name', 1: 'student_score', 2: 'subject'}, inplace=True)

        student_names= list(df['full_name'])
        student_scores= list(df['student_score'])
        subject= list(df['subject'])    

        distinct_subjects= df['subject'].unique()
        ##print(dateRange)
        ###Class 1
        #print(distinct_subjects)
        subLevelData=[]
        i=0
        for subVal in distinct_subjects:
            filtered_df=df[df.subject==subVal]
            filtered_df_student = list(filtered_df['full_name'])
            filtered_df_student_scored = list(filtered_df['student_score'])
            #subLevelData.append(data=[dict(y=filtered_df_student,x=filtered_df_student_scored,type='bar', name=subVal,orientation='h')])
            tempDict = dict(y=filtered_df_student,x=filtered_df_student_scored,type='bar',name=subVal,orientation='h')
            subLevelData.append(tempDict)
        print(str(subLevelData))

        graphData=[dict()]

        graphJSON = json.dumps(subLevelData, cls=plotly.utils.PlotlyJSONEncoder)
        #return str(graphJSON)
        return render_template('_testPerformanceGraph.html',graphJSON=graphJSON)
    else:
        return jsonify(['No records found for the selected date'])
    

@app.route('/studentPerformanceGraph')
@login_required
def studentPerformanceGraph():    
    class_val=request.args.get('class_val')
    section=request.args.get('section')
    if section!=None:
        section = section.strip()    
    test_type=request.args.get('test_type')
    student_id=request.args.get('student_id')
    #print('here is the class_val '+ str(class_val))
    dateVal = request.args.get('date')
    
    if dateVal ==None or dateVal=="":
        dateVal= datetime.today()
    
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    fromTestPerformance=0
    if class_val!=None:
        fromTestPerformance=1
        classSectionRows=ClassSection.query.filter_by(class_val=int(class_val),section=section, school_id=teacher.school_id).first()

    
    
    #testPerformanceRecords = db.session.query(StudentProfile.full_name,PerformanceDetail.student_score,
    #    MessageDetails.description)).join(StudentProfile).join(MessageDetails, MessageDetails.msg_id==PerformanceDetail.subject_id).filter_by(class_sec_id=classSectionRows.class_sec_id, date=dateVal,test_type=test_type).all()
    
    studPerformanceQuery = "select pd.date, CAST(pd.student_score AS INTEGER) as student_score,md.description "
    studPerformanceQuery = studPerformanceQuery + "from performance_detail pd "
    studPerformanceQuery = studPerformanceQuery + "inner join "
    studPerformanceQuery = studPerformanceQuery + "message_detail md on md.msg_id=pd.subject_id "
    studPerformanceQuery = studPerformanceQuery + "and "
    if fromTestPerformance==1:
        studPerformanceQuery = studPerformanceQuery + "pd.class_sec_id='"+str(classSectionRows.class_sec_id) +"' "
        studPerformanceQuery = studPerformanceQuery + "and "
    studPerformanceQuery = studPerformanceQuery + "pd.student_id='"+ str(student_id) +"' "
    studPerformanceQuery = studPerformanceQuery + "and test_type='"+ str(test_type)+ "' order by date"  


    studPerformanceRecords = db.session.execute(text(studPerformanceQuery)).fetchall()
        
    if len(studPerformanceRecords) !=0:
        df = pd.DataFrame( [[ij for ij in i] for i in studPerformanceRecords])
        df.rename(columns={0: 'date', 1: 'student_score', 2: 'subject'}, inplace=True)

        dateRange= list(df['date'])
        student_scores= list(df['student_score'])
        subject= list(df['subject'])

        distinct_subjects= df['subject'].unique()
        ##print(dateRange)
        ###Class 1
        #print(distinct_subjects)
        subLevelData=[]
        i=0
        for subVal in distinct_subjects:
            filtered_df=df[df.subject==subVal]
            filtered_df_date = list(filtered_df['date'])
            filtered_df_student_scored = list(filtered_df['student_score'])
            #subLevelData.append(data=[dict(y=filtered_df_student,x=filtered_df_student_scored,type='bar', name=subVal,orientation='h')])
            tempDict = dict(y=filtered_df_student_scored,x=filtered_df_date,mode= 'lines+markers',type='scatter',name=subVal,line_shape="spline", smoothing= '1.5')
            subLevelData.append(tempDict)
        print(str(subLevelData))

        graphData=[dict()]

        graphJSON = json.dumps(subLevelData, cls=plotly.utils.PlotlyJSONEncoder)
        #return str(graphJSON)
        return render_template('_studentPerformanceGraph.html',graphJSON=graphJSON)
    else:
        return jsonify(['No records found for the selected values'])
  
    



@app.route('/classPerformance')
@login_required
def classPerformance():
    form=feedbackReportForm()

    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()

    available_class=ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()
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

    return render_template('classPerformance.html',form=form,School_Name=school_name())


@app.route('/resultUpload',methods=['POST','GET'])
@login_required
def resultUpload():
    #selectfield choices list
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()

    available_class=ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()
    available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher_id.school_id).all()
    available_test_type=MessageDetails.query.filter_by(category='Test type').all()
    available_subject=MessageDetails.query.filter_by(category='Subject').all()


    class_list=[(str(i.class_val), "Class "+str(i.class_val)) for i in available_class]
    section_list=[(i.section,i.section) for i in available_section]
    test_type_list=[(i.description,i.description) for i in available_test_type]
    subject_name_list=[(i.description,i.description) for i in available_subject]

    form = ResultQueryForm()
    form1=MarksForm()

    #selectfield choices
    form.class_val.choices = class_list
    form.section.choices= section_list
    form.test_type.choices= test_type_list
    form.subject_name.choices=subject_name_list
    if not form1.upload.data:
        if form.validate_on_submit() :
            if current_user.is_authenticated:
                date=request.form['testdate']
                print(date)
                if date=='':
                    flash('Please select date !')
                    return render_template('resultUpload.html',form=form,School_Name=school_name())
                
                sub_name=form.subject_name.data
                test_type=form.test_type.data
        
                #class_val=MessageDetails.query.filter_by(description=form.class_val.data).first()
                #sec_val=MessageDetails.query.filter_by(description=form.section.data).first()
                sub_val=MessageDetails.query.filter_by(description=form.subject_name.data).first()
                test_type_val=MessageDetails.query.filter_by(description=form.test_type.data).first()

                class_sec_id=ClassSection.query.filter_by(class_val=int(form.class_val.data),section=form.section.data).first()

                teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()

                student_list=StudentProfile.query.filter_by(class_sec_id=class_sec_id.class_sec_id,school_id=teacher_id.school_id).all()

                if student_list:
                    session['class_sec_id']=class_sec_id.class_sec_id
                    session['school_id']=teacher_id.school_id
                    session['date']=date
                    session['sub_val']=sub_val.msg_id
                    session['test_type_val']=test_type_val.msg_id
                    session['teacher_id']=teacher_id.teacher_id
                
                    result_check=ResultUpload.query.filter_by(exam_date=session.get('date',None),
                    class_sec_id=session.get('class_sec_id',None),subject_id=session.get('sub_val',None)).first()

                    if result_check:
                        flash('Result already uploaded !')
                        return render_template('resultUpload.html', form=form,School_Name=school_name())

                    else:
                        return render_template('resultUpload.html',form=form,form1=form1,student_list=student_list,totalmarks=100,test_type=test_type,test_date=date,sub_name=sub_name,School_Name=school_name())

                else:
                    flash('No Student list for the given class and section')
                   
                    return render_template('resultUpload.html', form=form,School_Name=school_name())
        
            else:
                flash('Login required !')
                return render_template('resultUpload.html', form=form,School_Name=school_name())

        else:
            return render_template('resultUpload.html', form=form,School_Name=school_name())
    else:
        if form1.validate_on_submit():
            marks_list=request.form.getlist('marks')
            i=0
            student_list=StudentProfile.query.filter_by(class_sec_id=session.get('class_sec_id',None),school_id=session.get('school_id',None)).all()
            for student in student_list:
                if marks_list[i]=='-1':
                    marks=0
                    is_present=MessageDetails.query.filter_by(description='Not Present').first()
                else:
                    marks=marks_list[i]
                    is_present=MessageDetails.query.filter_by(description='Present').first()
                
                #test_id=schoold_id+class_sec_id+subject+test_type+exam date
                upload_id=str(session.get('school_id',None))+str(session.get('class_sec_id',None))+str(session.get('sub_val',None)) + str(session.get('test_type_val',None)) + str(session.get('date',None))
                upload_id=upload_id.replace('-','')
                Marks=ResultUpload(school_id=session.get('school_id',None),student_id=student.student_id,
                exam_date=session.get('date',None),marks_scored=marks,class_sec_id=session.get('class_sec_id',None),
                test_type=session.get('test_type_val',None),subject_id=session.get('sub_val',None),is_present=is_present.msg_id,
                uploaded_by=session.get('teacher_id',None), upload_id=upload_id,last_modified_date=datetime.today()
                )
                db.session.add(Marks)
                i+=1
            db.session.commit()
            flash('Marks Uploaded !')
        return render_template('resultUpload.html',form=form,School_Name=school_name())



@app.route('/resultUpload/<class_val>')
def section(class_val):
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    sections = ClassSection.query.distinct().filter_by(class_val=class_val,school_id=teacher_id.school_id).all()
    sectionArray = []

    for section in sections:
        sectionObj = {}
        sectionObj['section_id'] = section.class_sec_id
        sectionObj['section_val'] = section.section
        sectionArray.append(sectionObj)

    return jsonify({'sections' : sectionArray})


@app.route('/resultUploadHistory')
def resultUploadHistory():
    uploadHistoryQuery = "select distinct upload_id, cs.class_val, cs.section, "
    uploadHistoryQuery = uploadHistoryQuery + "md.description as test_type, md2.description as subject, date(ru.last_modified_date) as upload_date "
    uploadHistoryQuery = uploadHistoryQuery +"from result_upload ru inner join  class_section cs on  cs.class_sec_id=ru.class_sec_id "
    uploadHistoryQuery = uploadHistoryQuery +"inner join message_detail md on md.msg_id=ru.test_type inner join message_detail md2 on md2.msg_id=ru.subject_id"
    
    uploadHistoryRecords = db.session.execute(text(uploadHistoryQuery)).fetchall()
    return render_template('resultUploadHistory.html',uploadHistoryRecords=uploadHistoryRecords, School_Name=school_name())



@app.route('/uploadHistoryDetail',methods=['POST','GET'])
def uploadHistoryDetail():
    upload_id=request.args.get('upload_id')
    resultDetailQuery = "select sp.full_name, ru.total_marks, ru.marks_scored, md.description as test_type, ru.exam_date,cs.class_val, cs.section "
    resultDetailQuery = resultDetailQuery + "from result_upload ru inner join student_profile sp on sp.student_id=ru.student_id "
    resultDetailQuery = resultDetailQuery + "inner join message_detail md on md.msg_id=ru.test_type "
    resultDetailQuery = resultDetailQuery + "and ru.upload_id='"+ str(upload_id) +"' inner join class_section cs on cs.class_sec_id=ru.class_sec_id" 
    resultUploadRows = db.session.execute(text(resultDetailQuery)).fetchall()

    runcount=0
    class_val_record = ""    
    section_record=""
    test_type_record=""
    exam_date_record=""
    for value in resultUploadRows:
        if runcount==0:        
            class_val_record = value.class_val
            section_record = value.section
            test_type_record=value.test_type
            exam_date_record= value.exam_date
        runcount+1

    return render_template('_uploadHistoryDetail.html',resultUploadRows=resultUploadRows, class_val_record=class_val_record,section_record=section_record, test_type_record=test_type_record,exam_date_record=exam_date_record,School_Name=school_name())

# @app.route('/questionUpdate')
# def questionUpdate():
#     question_id=request.args.get('question_id')
#     return render_template('questionUpdate.html',question_id=question_id)


# @app.route('/questionPageUpdate',methods=['POST','GET'])
# @login_required
# def questionPageUpdate():
#     form=QuestionUpdaterQueryForm() 
#     if request.method=='POST':
#         if form.submit.data:
#             question=QuestionDetails(class_val=int(request.form['class_val']),subject_id=int(request.form['subject_name']),question_description=request.form['question_desc'],
#             reference_link=request.form['reference'],topic_id=int(request.form['topics']),question_type=form.question_type.data)
#             db.session.add(question)
#             if form.question_type.data=='Subjective':
#                 question_id=db.session.query(QuestionDetails).filter_by(class_val=int(request.form['class_val']),topic_id=int(request.form['topics']),question_description=request.form['question_desc']).first()
#                 options=QuestionOptions(question_id=question_id.question_id,weightage=request.form['weightage'])
#                 db.session.add(options)
#                 db.session.commit()
#                 flash('Success')
#                 return render_template('questionUpdate.html',School_Name=school_name())
#             else:
#                 option_list=request.form.getlist('option_desc')
#                 question_id=db.session.query(QuestionDetails).filter_by(class_val=int(request.form['class_val']),topic_id=int(request.form['topics']),question_description=request.form['question_desc']).first()
#                 if request.form['correct']=='':
#                     flash('Correct option not seleted !')
#                     return render_template('questionUpdate.html',School_Name=school_name())
#                 for i in range(len(option_list)):
#                     if int(request.form['option'])==i+1:
#                         correct='Y'
#                         weightage=int(request.form['weightage'])
#                     else:
#                         weightage=0
#                         correct='N'
#                     if i+1==1:
#                         option='A'
#                     elif i+1==2:
#                         option='B'
#                     elif i+1==3:
#                         option='C'
#                     else:
#                         option='D'
#                     options=QuestionOptions(option_desc=option_list[i],question_id=question_id.question_id,is_correct=correct,weightage=weightage,option=option)
#                     db.session.add(options)
#                 db.session.commit()
#                 flash('Success')
#                 return render_template('questionUpdate.html',School_Name=school_name())
#         else:
#             csv_file=request.files['file-input']
#             df1=pd.read_csv(csv_file)
#             for index ,row in df1.iterrows():
#                 question=QuestionDetails(class_val=int(request.form['class_val']),subject_id=int(request.form['subject_name']),question_description=row['Question Description'],
#                 topic_id=int(request.form['topics']),question_type='MCQ1',reference_link=request.form['reference-url'+str(index+1)])
#                 db.session.add(question)
#                 question_id=db.session.query(QuestionDetails).filter_by(class_val=int(request.form['class_val']),topic_id=int(request.form['topics']),question_description=row['Question Description']).first()
#                 for i in range(1,5):
#                     option_no=str(i)
#                     option_name='Option'+option_no
#                     weightage_name='Weightage'+option_no
#                     if row['CorrectAnswer']=='option '+option_no:
#                         correct='Y'
#                         weightage=row[weightage_name]
#                     else:
#                         correct='N'
#                         weightage='0'
#                     if i==1:
#                             option_val='A'
#                     elif i==2:
#                             option_val='B'
#                     elif i==3:
#                             option_val='C'
#                     else:
#                         option_val='D'

#                     option=QuestionOptions(option_desc=row[option_name],question_id=question_id.question_id,is_correct=correct,option=option_val,weightage=int(weightage))
#                     db.session.add(option)
#             db.session.commit()
#             flash('Successfullly Uploaded !')
#             return render_template('questionUpdate.html',School_Name=school_name())
#     return render_template('questionUpdate.html',School_Name=school_name())

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
            reference_link=request.form['reference'],topic_id=int(request.form['topics']),question_type=form.question_type.data)
            print(question)
            db.session.add(question)
            if form.question_type.data=='Subjective':
                question_id=db.session.query(QuestionDetails).filter_by(class_val=int(request.form['class_val']),topic_id=int(request.form['topics']),question_description=request.form['question_desc']).first()
                options=QuestionOptions(question_id=question_id.question_id,weightage=request.form['weightage'])
                print(options)
                db.session.add(options)
                db.session.commit()
                flash('Success')
                return render_template('questionBuilder.html',School_Name=school_name())
            else:
                option_list=request.form.getlist('option_desc')
                question_id=db.session.query(QuestionDetails).filter_by(class_val=int(request.form['class_val']),topic_id=int(request.form['topics']),question_description=request.form['question_desc']).first()
                if request.form['correct']=='':
                    flash('Correct option not seleted !')
                    return render_template('questionBuilder.html',School_Name=school_name())
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
                    options=QuestionOptions(option_desc=option_list[i],question_id=question_id.question_id,is_correct=correct,weightage=weightage,option=option)
                    print("Options in question Builder:"+str(options))
                    db.session.add(options)
                db.session.commit()
                flash('Success')
                return render_template('questionBuilder.html',School_Name=school_name())
        else:
            csv_file=request.files['file-input']
            df1=pd.read_csv(csv_file)
            for index ,row in df1.iterrows():
                question=QuestionDetails(class_val=int(request.form['class_val']),subject_id=int(request.form['subject_name']),question_description=row['Question Description'],
                topic_id=int(request.form['topics']),question_type='MCQ1',reference_link=request.form['reference-url'+str(index+1)])
                db.session.add(question)
                question_id=db.session.query(QuestionDetails).filter_by(class_val=int(request.form['class_val']),topic_id=int(request.form['topics']),question_description=row['Question Description']).first()
                for i in range(1,5):
                    option_no=str(i)
                    option_name='Option'+option_no
                    weightage_name='Weightage'+option_no
                    if row['CorrectAnswer']=='option '+option_no:
                        correct='Y'
                        weightage=row[weightage_name]
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

                    option=QuestionOptions(option_desc=row[option_name],question_id=question_id.question_id,is_correct=correct,option=option_val,weightage=int(weightage))
                    print(option)
                    db.session.add(option)
            db.session.commit()
            flash('Successfully Uploaded !')
            return render_template('questionBuilder.html',School_Name=school_name())
    return render_template('questionBuilder.html',School_Name=school_name())

@app.route('/questionUpload',methods=['GET'])
def questionUpload():
    flag = False
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form=QuestionBuilderQueryForm()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()]
    form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.topics.choices=[(str(i['topic_id']), str(i['topic_name'])) for i in topics(1,54)]
    if form.class_val.data!='None' and form.subject_name.data!='None' and  form.chapter_num.data!='None':
        print('Inside if question Upload')
        topic_list=Topic.query.filter_by(class_val=str(form.class_val.data),subject_id=str(form.subject_name.data),chapter_num=str(form.chapter_num.data)).all()
        return render_template('questionUpload.html',form=form, flag=flag,topic_list=topic_list)
    else:
        return render_template('questionUpload.html',form=form,flag=flag)

# @app.route('/questionUpdateUpload',methods=['GET'])
# def questionUpdateUpload():
#     teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
#     form=QuestionUpdaterQueryForm()
#     form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()]
#     form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
#     form.topics.choices=[(str(i['topic_id']), str(i['topic_name'])) for i in topics(1,54)]
#     return render_template('questionUpdateUpload.html',form=form)

@app.route('/questionFile',methods=['GET'])
def questionFile():
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form=QuestionBuilderQueryForm()
    form.class_val.choices = [(str(i.class_val), "Class "+str(i.class_val)) for i in ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher_id.school_id).all()]
    form.subject_name.choices= [(str(i['subject_id']), str(i['subject_name'])) for i in subjects(1)]
    form.topics.choices=[(str(i['topic_id']), str(i['topic_name'])) for i in topics(1,54)]
    return render_template('questionFile.html',form=form)



#Subject list generation dynamically

@app.route('/questionBuilder/<class_val>')
def subject_list(class_val):
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

@app.route('/questionChapterpicker/<class_val>/<subject_id>')
def chapter_list(class_val,subject_id):
    chapter_num = "select distinct chapter_num from topic_detail where class_val='"+class_val+"' and subject_id='"+subject_id+"' order by chapter_num"
    print(chapter_num)
    print('Inside chapterPicker')
    # Topic.query.filter_by(class_val=class_val,subject_id=subject_id).distinct().order_by(Topic.chapter_num).all()
    chapter_num_list = db.session.execute(text(chapter_num))
    chapter_num_array=[]
    for chapterno in chapter_num_list:
        chapterNo = {}
        chapterNo['chapter_num']=chapterno.chapter_num
        chapter_num_array.append(chapterNo)
    return jsonify({'chapterNum':chapter_num_array})

# @app.route('/questionChapterpicker/<subject_id>')
# def chapter_list_from_subject(subject_id):
#     chapter_num_list = Topic.query.filter_by(subject_id=subject_id).distinct().order_by(Topic.chapter_num).all()
#     chapter_num_array=[]
#     for chapterno in chapter_num_list:
#         chapterNo = {}
#         chapterNo['chapter_num']=chapterno.chapter_num
#         chapter_num_array.append(chapterNo)
#     return jsonify({'chapterNum':chapter_num_array})



# @app.route('/questionBuilder/<class_val>/<subject_id>')
# def chapterNum(class_val,subject_id):
#     chapter_num_list=Topic.query.filter_by(class_val=class_val,subject_id=subject_id).all()
#     chapterArray = []
#     for chapter_num in chapter_num_list:
#         topicObj={}
#         topicObj['chapter_num']=chapter_num.

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
    return render_template('studentProfile.html',School_Name=school_name())

@app.route('/indivStudentProfile')
@login_required
def indivStudentProfile():    
    student_id=request.args.get('student_id')
    print(student_id)
    studentProfileQuery = "select full_name, email, phone, dob, gender,class_val, section,roll_number,school_adm_number,profile_picture from student_profile sp inner join class_section cs on sp.class_sec_id= cs.class_sec_id "
    studentProfileQuery = studentProfileQuery + "and sp.student_id='"+str(student_id)+"'" + "left join address_detail ad on ad.address_id=sp.address_id "    
    studentProfileRow = db.session.execute(text(studentProfileQuery)).first()    

    guardianRows = GuardianProfile.query.filter_by(student_id=student_id).all()

    #print("reached indiv student ")
    #print(studentProfileRow)
    return render_template('_indivStudentProfile.html',School_Name=school_name(),studentProfileRow=studentProfileRow,guardianRows=guardianRows)


@app.route('/studentProfile')
@login_required
def studentProfile():    
    form=studentPerformanceForm()
    user = User.query.filter_by(username=current_user.username).first_or_404()        
    teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
    
    available_class=ClassSection.query.with_entities(ClassSection.class_val).distinct().filter_by(school_id=teacher.school_id).all()
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
    # student_list
    return render_template('studentProfileNew.html',School_Name=school_name(),form=form)


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
    return render_template('help.html',School_Name=school_name())


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
        prev_url=prev_url,School_Name=school_name())


if __name__=="__main__":
    app.debug=True
    app.jinja_env.filters['zip'] = zip
    app.run(host=os.getenv('IP', '127.0.0.1'), 
            port=int(os.getenv('PORT', 8000)))
    #app.run()

