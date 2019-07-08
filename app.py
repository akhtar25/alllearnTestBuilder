from flask import Flask, render_template, request, flash, redirect, url_for, Response,session,jsonify
from send_email import newsletterEmail, send_password_reset_email
from applicationDB import *
from qrReader import *
from config import Config
from forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm,ResultQueryForm,MarksForm
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


app=Flask(__name__)
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
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/alllearn.log', maxBytes=10240, backupCount=10)
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
    #s3 = boto3.client('s3')
    s3 = boto3.client('s3', region_name='ap-south-1')

    print(s3)
    presigned_post = s3.generate_presigned_post(
      Bucket = S3_BUCKET,
      Key = file_name,
      Fields = {"acl": "public-read", "Content-Type": file_type},
      Conditions = [
        {"acl": "public-read"},
        {"Content-Type": file_type}
      ],
      ExpiresIn = 3600
    )
    return json.dumps({
      'data': presigned_post,
      'url': 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, file_name)
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
        df = pd.read_csv('data.csv').drop('Open', axis=1)
        chart_data = df.to_dict(orient='records')
        chart_data = json.dumps(chart_data, indent=2)
        data = {'chart_data': chart_data}
    #####Fetch Top Students infor##########

    #####Fetch Event data##########
        EventDetailRows = EventDetail.query.filter_by(school_id=school_name_val).all()
    

    #####Fetch Course Completion infor##########

    #####Fetch Topic to Cover today info##########
        topicToCoverQuery = "select *from vw_topic_tracker_overall"
        topicToCoverDetails = db.session.execute(text(topicToCoverQuery)).fetchall()
        print(topicToCoverDetails)
        return render_template('dashboard.html',title='Home Page',School_Name=school_name(),data=data, topicToCoverDetails = topicToCoverDetails)


@app.route('/disconnectedAccount')
@login_required
def disconnectedAccount():    
    return render_template('disconnectedAccount.html', title='Disconnected Account', disconn = 1)

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
            # possibly db.session.execute(text("<sql here>")).execution_options(autocommit=True))
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

@app.route('/testBuilder')
@login_required
def testBuilder():
    return render_template('testBuilder.html')

@app.route('/testPapers')
@login_required
def testPapers():
    return render_template('testPapers.html')

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

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

@app.route('/class')
@login_required
def classCon():
    if current_user.is_authenticated:        
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
        
        qclass_val = request.args.get('class_val',1)
        qsection=request.args.get('section','A')

        #db query

        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).order_by(ClassSection.class_val).all()
        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val")).fetchall()

        classTrackerQuery = "select t1.subject_id as sid, t3.description as subject, t1.next_topic as tid, t2.topic_name as topic, t2.chapter_name, t1.class_sec_id, t4.section, t4.class_val, t4.school_id "
        classTrackerQuery =classTrackerQuery + "from topic_tracker t1, topic_detail t2, message_detail t3, class_section t4   "
        classTrackerQuery =classTrackerQuery + "where t1.next_topic=t2.topic_id and  t2.subject_id=t3.msg_id and  t1.class_sec_id=t4.class_sec_id   "
        classTrackerQuery =classTrackerQuery + "and t4.class_val= " + str(qclass_val) + " and t4.section = '" + str(qsection) + "' and t4.school_id =" + str(teacher.school_id)
        classTrackerDetails = db.session.execute(text(classTrackerQuery)).fetchall()

        #courseDetail = Topic.query.join(Topic,subject_id==MessageDetails.msg_id).filter_by(class_val=ClassSection.class_val).all()
        courseDetailQuery = "select t1.*,  t2.description as subject from topic_detail t1, message_detail t2 "
        courseDetailQuery = courseDetailQuery + "where t1.subject_id=t2.msg_id "
        courseDetailQuery = courseDetailQuery + "and class_val= '" + str(qclass_val)+ "'"
        courseDetails= db.session.execute(text(courseDetailQuery)).fetchall()

        print(courseDetails)

        #endOfQueries

        #print(classTrackerDetails)
        return render_template('class.html', classsections=classSections, qclass_val=qclass_val, qsection=qsection, distinctClasses=distinctClasses,classTrackerDetails=classTrackerDetails, courseDetails=courseDetails,School_Name=school_name())
    else:
        return redirect(url_for('login'))    

@app.route('/classDelivery')
@login_required
def classDelivery():
    if current_user.is_authenticated:        
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
        
        qclass_val = request.args.get('class_val',1)
        qsection=request.args.get('section','A') 
        qsubject_id=request.args.get('subject_id','15')

        #db query 
            #sidebar
        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).order_by(ClassSection.class_val).all()
        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val")).fetchall()
            # end of sidebar
        currClass = ClassSection.query.filter_by(school_id=teacher.school_id, class_val=qclass_val, section = qsection).order_by(ClassSection.class_val).first()
        #for curr in currClass:
        print("This is currClass.class_sec_id: " + str(currClass.class_sec_id))
        topicTrack = TopicTracker.query.filter_by(class_sec_id=currClass.class_sec_id, subject_id=qsubject_id).first()
        #print ("this is topic Track: " + topicTrack)
        topicDet = Topic.query.filter_by(topic_id=topicTrack.next_topic).first()
        bookDet= BookDetails.query.filter_by(book_id = topicDet.book_id).first()
        
        topicTrackerQuery = "select t1.topic_id, t1.topic_name, t1.chapter_name, t1.chapter_num, " 
        topicTrackerQuery = topicTrackerQuery + " t1.unit_num, t1.book_id, t2.is_covered, t1.subject_id, t2.class_sec_id"
        topicTrackerQuery = topicTrackerQuery + " from "
        topicTrackerQuery = topicTrackerQuery + " topic_detail t1, "
        topicTrackerQuery = topicTrackerQuery + " topic_tracker t2"
        topicTrackerQuery = topicTrackerQuery + " where"
        topicTrackerQuery = topicTrackerQuery + " t1.topic_id=t2.topic_id"
        topicTrackerQuery = topicTrackerQuery + " and t2.class_sec_id = '" + str(currClass.class_sec_id) + "'"
        topicTrackerQuery = topicTrackerQuery + " and t1.subject_id= '" + str(qsubject_id ) + "'"
        topicTrackerDetails= db.session.execute(text(topicTrackerQuery)).fetchall()
        
    return render_template('classDelivery.html', classsections=classSections,qclass_val=qclass_val, qsection=qsection, distinctClasses=distinctClasses, bookDet=bookDet,topicTrackerDetails=topicTrackerDetails,School_Name=school_name())




@app.route('/feedbackCollection', methods=['GET', 'POST'])
@login_required
def feedbackCollection():
    if request.method == 'POST':
        currCoveredTopics = request.form.getlist('topicCheck')
        class_val = request.form['class_val']
        section = request.form['section']

        print("class val is = " + str(class_val))
        print("section  is = " + str(section))
#
        #sidebar queries
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    

        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).order_by(ClassSection.class_val).all()
        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val")).fetchall()
        # end of sidebarm

        questionList = QuestionDetails.query.filter(QuestionDetails.topic_id.in_(currCoveredTopics)).all()  
        questionListSize = len(questionList)



        #start of - db update to ark the checked topics as completed
        #teacherProfile = TeacherProfile.query.filter_by(user_id=current_user.id).first()
        #topicTrackerDetails = TopicTracker.query.filter_by(school_id = teacherProfile.school_id).all()
        
        #for val in currCoveredTopics:
        #    val_id=Topic.query.filter_by(topic_name=val).first()
        #    for topicRows in topicTrackerDetails:
        #        print(str(topicRows.topic_id) + " and " + str(val_id.topic_id))
        #        if topicRows.topic_id==val_id.topic_id:
        #            topicRows.is_covered = 'Y'            
        #            db.session.commit()        
        # end of  - update to mark the checked topics as completed


        return render_template('feedbackCollection.html', classSections = classSections, distinctClasses = distinctClasses, class_val = class_val, section = section, questionList = questionList, questionListSize = questionListSize,School_Name=school_name())
    else:
        return redirect(url_for('classCon'))    


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
    #print('here is the class_val '+ str(class_val))
    section=request.args.get('section')
    section = section.strip()
    #print('here is the section '+ str(section))
    if (questionListJson != None) and (class_val != None) and (section != None):

        classSecRow = ClassSection.query.filter_by(class_val=class_val, section=section).first()       
        print('here is the classSecRow.class_Sec_id: '+ str(classSecRow))
        questionDetailRow = QuestionDetails.query.filter_by(question_id=questionListJson[1]).first()
                    
        dateVal= datetime.today().strftime("%d%m%Y")

        responseSessionID = str(dateVal) + str(questionDetailRow.subject_id) + str(classSecRow.class_sec_id)
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

    return render_template('_feedbackReport.html', responseResultRow= responseResultRow,classAverage =classAverage,  responseResultRowCount = responseResultRowCount, resp_session_id = responseSessionID)


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
    return render_template('testPerformance.html')


@app.route('/classPerformance')
@login_required
def classPerformance():
    return render_template('classPerformance.html')


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
        if form1.validate_on_submit:
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
                

                Marks=ResultUpload(school_id=session.get('school_id',None),student_id=student.student_id,
                exam_date=session.get('date',None),marks_scored=marks,class_sec_id=session.get('class_sec_id',None),
                test_type=session.get('test_type_val',None),subject_id=session.get('sub_val',None),is_present=is_present.msg_id,
                uploaded_by=session.get('teacher_id',None)
                )
                db.session.add(Marks)

                i+=1
            db.session.commit()
            flash('Marks Uploaded !')
        
            
        return render_template('resultUpload.html',form=form,School_Name=school_name())



@app.route('/resultUpload/<class_val>')
def section(class_val):
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()

    sections = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).all()

    sectionArray = []

    for section in sections:
        sectionObj = {}
        sectionObj['section_id'] = section.class_sec_id
        sectionObj['section_val'] = section.section
        sectionArray.append(sectionObj)

    return jsonify({'sections' : sectionArray})



@app.route('/studentProfile')
@login_required
def studentProfile():
    return render_template('studentProfile.html',School_Name=school_name())

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
    app.run(host=os.getenv('IP', '127.0.0.1'), 
            port=int(os.getenv('PORT', 8000)))
    #app.run()

