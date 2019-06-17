from flask import Flask, render_template, request, flash, redirect, url_for, Response,session
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
    

@app.route("/account/")
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
def submit_form():
    teacherProfile = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    teacherProfile.teacher_name = request.form["full-name"]
    teacherProfile.profile_picture = request.form["avatar-url"]
    db.session.commit()
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

@app.route('/decodes', methods=['GET', 'POST'])
def decodeAjax():
    if request.method == 'POST':
        decodedData = barCode.decode(request.form['imgBase64'])
        if decodedData:
            json_data = json.dumps(decodedData)
            print(json_data)
            return jsonify(json_data)
        return jsonify(['NO BarCode Found'])


@app.route('/ScanBooks',methods=['GET', 'POST'])
def ScanBooks():
    print ("We're here!")
    return render_template('ScanBook.html',title='Scan Page')


@app.route('/feedbackReport')
def feedbackReport():
    return render_template('feedbackReport.html',title='Feedback Report')

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
        'edit_profile.html', title='Edit Profile', form=form)


@app.route('/')
@app.route('/index')
def index():
    return render_template('dashboard.html',title='Home Page')


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
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()    
    print(user.id)
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc())
    return render_template('user.html', user=user, posts=posts)


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
def feeManagement():
    return render_template('feeManagement.html')

@app.route('/tests')
def tests():
    return render_template('tests.html')

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/schoolPerformanceRanking')
def schoolPerformanceRanking():
    return render_template('schoolPerformanceRanking.html')

@app.route('/recommendations')
def recommendations():
    return render_template('recommendations.html')



@app.route('/feedbackCollection')
def feedbackCollection():
    #if db.session.query(Survivor).filter(Survivor.sur_email == email).count() == 0:
    #        #Raw sql example  - db.engine.execute(text("<sql here>")).execution_options(autocommit=True))
    #        # possibly db.session.execute(text("<sql here>")).execution_options(autocommit=True))
    #        survivor = Survivor(email, name)
    #        db.session.add(survivor)
    #        db.session.commit()
    #        print(email,name)
    #        newsletterEmail(email, name)
    #        return render_template('newsletterSuccess.html')
    #    else:
    #        return render_template('index.html',text='Error: Email already used.')
    return render_template('feedbackCollection.html')


@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

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
        return render_template('class.html', classsections=classSections, qclass_val=qclass_val, qsection=qsection, distinctClasses=distinctClasses,classTrackerDetails=classTrackerDetails, courseDetails=courseDetails)
    else:
        return redirect(url_for('login'))    

@app.route('/classDelivery')
def classDelivery():
    if current_user.is_authenticated:        
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
        
        qclass_val = request.args.get('class_val',1)
        qsection=request.args.get('section','A') 

        #db query
        classSections=ClassSection.query.filter_by(school_id=teacher.school_id).order_by(ClassSection.class_val).all()
        distinctClasses = db.session.execute(text("select distinct class_val, count(class_val) from class_section where school_id="+ str(teacher.school_id)+" group by class_val")).fetchall()

    return render_template('classDelivery.html', classsections=classSections,qclass_val=qclass_val, qsection=qsection, distinctClasses=distinctClasses)


@app.route('/performance')
def performance():
    return render_template('performance.html')


@app.route('/resultUpload',methods=['POST','GET'])
def resultUpload():
    form = ResultQueryForm()
    form1=MarksForm()
    

    if not form1.upload.data:
        if form.validate_on_submit():
            if current_user.is_authenticated:
                date=request.form['testdate']
                sub_name=form.subject_name.data
                test_type=form.test_type.data
        
                class_val=MessageDetails.query.filter_by(description=form.class_name.data).first_or_404()
                sec_val=MessageDetails.query.filter_by(description=form.class_section.data).first_or_404()
                sub_val=MessageDetails.query.filter_by(description=form.subject_name.data).first_or_404()
                test_type_val=MessageDetails.query.filter_by(description=form.test_type.data).first_or_404()

                class_room_id=ClassSection.query.filter_by(class_val=int(class_val.description),section=sec_val.description).first_or_404()

                schl_id=TeacherProfile.query.filter_by(user_id=current_user.id).first_or_404()

                student_list=StudentProfile.query.filter_by(class_sec_id=class_room_id.class_sec_id,school_id=schl_id.school_id).all()

           

                if student_list:
                    session['class_sec_id']=class_room_id.class_sec_id
                    session['school_id']=schl_id.school_id
                    session['date']=date
                    session['sub_val']=sub_val.msg_id
                    session['test_type_val']=test_type_val.msg_id
                
                    result_check=ResultUpload.query.filter_by(exam_date=session.get('date',None),
                    class_sec_id=session.get('class_sec_id',None),subject_id=session.get('sub_val',None)).first()

                    if result_check:
                        flash('Result already uploaded !')
                        return render_template('resultUpload.html', form=form)

                    else:
                        return render_template('resultUpload.html',form=form,form1=form1,student_list=student_list,totalmarks=100,test_type=test_type,test_date=date,sub_name=sub_name)

                else:
                    flash('No Records')
                   
                    return render_template('resultUpload.html', form=form)
        
                
            else:
                flash('Login required !')
                return render_template('resultUpload.html', form=form)

        else:
            return render_template('resultUpload.html', form=form)
    else:
        if form1.validate_on_submit:
            marks_list=request.form.getlist('marks')
            i=0
            flash('Marks Uploaded !')
            student_list=StudentProfile.query.filter_by(class_sec_id=session.get('class_sec_id',None),school_id=session.get('school_id',None)).all()
            for student in student_list:

                if marks_list[i]=='-1':
                    marks=0
                    is_present=MessageDetails.query.filter_by(description='Not Present').first_or_404()
                else:
                    marks=marks_list[i]
                    is_present=MessageDetails.query.filter_by(description='Present').first_or_404()
                

                Marks=ResultUpload(school_id=session.get('school_id',None),student_id=student.student_id,
                exam_date=session.get('date',None),marks_scored=marks,class_sec_id=session.get('class_sec_id',None),
                test_type=session.get('test_type_val',None),subject_id=session.get('sub_val',None),is_present=is_present.msg_id
                )
                db.session.add(Marks)

                i+=1
            db.session.commit()
        
            
        return render_template('resultUpload.html',form=form)



@app.route('/studentProfile')
def studentProfile():
    return render_template('studentProfile.html')

@app.route('/help')
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


#if __name__=='__main__':
#    app.debug=True
#    app.run()



if __name__=="__main__":
    app.debug=True
    app.run(host=os.getenv('IP', '127.0.0.1'), 
            port=int(os.getenv('PORT', 8000)))
    #app.run()

