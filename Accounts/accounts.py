from Accounts.utils import *
from applicationDB import *
from flask import Blueprint, render_template, request, flash, redirect, url_for, session,jsonify, Flask
from flask_login import current_user, login_user, logout_user, login_required
from forms import LoginForm, RegistrationForm, ResetPasswordRequestForm
from send_email import welcome_email, send_password_reset_email,user_access_request_email
from sqlalchemy import text
from werkzeug.urls import url_parse
from flask_cors import CORS
import datetime
import jwt
import os


accounts = Blueprint('accounts',__name__)
CORS(accounts)

@accounts.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
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
        print("Abdullah--")
        return redirect(url_for('accounts.login'))
    return render_template('register.html', title='Register', form=form)

@accounts.route('/userAPI',methods=['GET','POST'])
def userAPI():
    print('inside userAPI')
    data = request.headers.get('Authorization')
    print(data)
    # headers = Flask.request.headers
    
    if  data=='null':
        print('if data=="null" token not empty')
        decode  = jwt.decode(data,'you-will-never-guess')
        print(decode['user'])
        userData = {}
        user = User.query.filter_by(email=decode['user']).first()
        userData['id'] = user.id
        userData['userType'] = user.user_type
        userData['email'] = user.email
        userData['school_id'] = user.school_id
        userData['user_name'] = str(user.first_name)+' '+str(user.last_name)
        return jsonify({'decode':userData})
    else:
        print('if token is empty')
        return jsonify({'decode':{}})


@accounts.route('/registerAPI',methods=['GET','POST'])
def registerAPI():
    print('inside registerAPI')
    first_name=request.args.get('first_name')
    last_name=request.args.get('last_name')
    email=request.args.get('email')
    password=request.args.get('password')
    reset_password = request.args.get('confirm_password')
    phone=request.args.get('phone')
    print(first_name)
    print(last_name)
    print(email)
    print(password)
    print(reset_password)
    print(phone)
    # if form.validate_on_submit():
    #     print('Validated form submit')
    # if check(email)=='N':
    #     return "Invalid Email",401
    if len(password) < 7:
        print(len(password))
        return jsonify({'message':"Weak password: password length should be greater then 7",'error':'Invalid password'}),401
    try:
        user = User(username=email, email=email, user_type='140', access_status='145', phone=phone,
        first_name = first_name,school_id=1,last_name= last_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    except:
        return jsonify({'message':"Mail Id already exist",'error':'Invalid Mail Id'}),401
    checkTeacherProf = TeacherProfile.query.filter_by(email=email).first()
    checkStudentProf = StudentProfile.query.filter_by(email=email).first()

    if checkTeacherProf!=None:
        checkTeacherProf.user_id=user.id
        db.session.commit()        
    elif checkStudentProf!=None:
        checkStudentProf.user_id=user.id
        db.session.commit()
    else:
        pass

    full_name = str(first_name)+ ' '+str(last_name)
    #     flash('Congratulations '+full_name+', you are now a registered user!')
    welcome_email(str(email), full_name)
    print("Abdullah--")
    
    #     return redirect(url_for('accounts.login'))
    token = jwt.encode({
        'user':email,
        'exp':datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    },
    'you-will-never-guess')    
    return jsonify({'email':email,'id':user.id,'phone':phone,'name':str(first_name)+' '+str(last_name),'tokenId':str(token.decode('utf-8'))})
    
@accounts.route('/login', methods=['GET', 'POST'])
def login():
    print('Inside login')    
    if current_user.is_authenticated:  
        print(request.url)    
        if current_user.user_type=='161':
            return redirect(url_for('app.openJobs'))
        else:
            return redirect(url_for('dashboard.index'))

    #new section for google login
    glogin = request.args.get('glogin')
    gemail = request.args.get('gemail')
    ##end of new section
    
    form = LoginForm()
    print('Validation')
    print(form.validate_on_submit())
    session['isGooglelogin'] = ''
    if form.validate_on_submit() or glogin=="True":
        if glogin=="True":
            print("###glogin val"+ str(glogin))
            print("###email received from page"+ str(gemail))
            user=User.query.filter_by(email=gemail).first()   
            if user is None:
                flash("Email not registered")
                print('Email not registered')
                return redirect(url_for('accounts.login'))
        else: 
            print('Input data:'+str(form.email.data))
            checkEmailValidation = check(form.email.data)
            user = ''
            if checkEmailValidation == 'Y':
                user=User.query.filter_by(email=form.email.data).first() 
            else:
                Input = form.email.data
                print('Type:'+str(type(Input)))
                In = Input.upper()
                string = 'stud_'
                strg = string.upper()
                print('Type:'+str(type(strg))+'String:'+str(strg))
                if In.find(strg) == 0:
                    print('this is student id')
                    studentId = Input[5:]
                    print('studentId:'+str(studentId))
                    studData = StudentProfile.query.filter_by(student_id=studentId).first()
                    email = studData.email
                    user=User.query.filter_by(email=email).first() 
                else:
                    print('phone no')
                    user=User.query.filter_by(phone=Input).first()

            try:             
                if user is None or not user.check_password(form.password.data):        
                    flash("Invalid email or password")
                    return redirect(url_for('accounts.login'))
            except:
                flash("Invalid email or password")
                return redirect(url_for('accounts.login'))

        #logging in the user with flask login
        try:
            login_user(user,remember=form.remember_me.data)
        except:
            flash("Invalid email or password")
            return redirect(url_for('accounts.login'))

        next_page = request.args.get('next')
        print('next_page',next_page)
        if not next_page or url_parse(next_page).netloc != '':
            print('if next_page is not empty',next_page)
            next_page = url_for('dashboard.index')
        
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
        print('school_pro:'+str(school_pro))
        session['isGooglelogin'] = ''
        if school_pro:
            session['school_logo'] = school_pro.school_logo
            session['schoolPicture'] = school_pro.school_picture
            session['schoolName'] = school_pro.school_name
            session['font'] = school_pro.font
            print('session[font]:'+str(session['font']))
            session['primary_color'] = school_pro.primary_color
            session['isGooglelogin'] = school_pro.google_login
            print('session[isGooglelogin]:'+str(session['isGooglelogin']))
            print('school_pro.google_login:'+str(school_pro.google_login))
            session['show_school_name'] = school_pro.show_school_name
            teacherData = TeacherProfile.query.filter_by(teacher_id=school_pro.school_admin).first()
            userData = User.query.filter_by(id=teacherData.user_id).first()
            session['phone'] = userData.phone
            session['email'] = userData.email
        print(session['primary_color'])
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
        #return redirect(url_for('dashboard.index'))
    # schoolDataQuery = "select *from school_profile"
    # schoolData = db.session.execute(text(schoolDataQuery)).fetchall()
    schoolName = ''
    schoolLogo = ''
    primaryColor = '' 
    phone = ''
    email = ''
    print('Url:'+str(request.url))
    subDom = request.url
    newDom = 'accounts.login'
    print('login:'+str(newDom))
    newSubDom = subDom.partition(newDom)
    newSub = newSubDom[0] + newSubDom[1]
    print('newSubDom:'+str(newSub))
    schoolDataQuery = "select *from school_profile where sub_domain like '"+str(newSub)+"%'"
    schoolData = db.session.execute(text(schoolDataQuery)).fetchall()   
    print(subDom)
    font=''
    for row in schoolData:
        print(row)
        if row:
            schoolName = row.school_name
            schoolLogo = row.school_logo
            primaryColor = row.primary_color
            font = row.font
            print('font:'+str(font))
            print('primaryColor:'+str(primaryColor))
            teacherData = TeacherProfile.query.filter_by(teacher_id=row.school_admin).first()
            userData = User.query.filter_by(id=teacherData.user_id).first()
            phone = userData.phone
            email = userData.email
    print('phone:'+str(phone))
    print('email:'+str(email))
    return render_template('login.html',font=font,phone=phone,email=email,primaryColor=primaryColor,schoolName=schoolName,schoolLogo=schoolLogo, title='Sign In', form=form)

@accounts.route('/logoutAPI',methods=['GET','POST'])
def logoutAPI():
    data = request.headers.get('Authorization')
    print(data)
    if data is None:
        return jsonify({'email':'','id':'','phone':'','name':'','tokenId':'','status':'logout successfully!'})
    else:
        return jsonify({})

@accounts.route('/loginAPI', methods=['GET', 'POST'])
def loginAPI():
    print('Inside login') 
    email=request.args.get('email')  
    password=request.args.get('password')
    print('Email:'+email)
    print('Password:'+password) 
    user = User.query.filter_by(email=email).first()
    
    token = jwt.encode({
        'user':email,
        'exp':datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    },
    'you-will-never-guess')
    print('Token'+str(token))
    if user:
        print(user.check_password(password))
        if user.check_password(password):
            print('user exist')
            return jsonify({'email':user.email,'id':user.id,'phone':user.phone,'name':str(user.first_name)+' '+str(user.last_name),'tokenId':token.decode('utf-8'),'status':'success'})
        else:
            print('user not exist')
            return jsonify({'message':"Invalid email or password",'error':'Authentication failed','status':'error'})

    else:
        print('user not exist')
        return jsonify({'message':"Invalid email or password",'error':'Authentication failed','status':'error'})
    # if current_user.is_authenticated:  
    #     print(request.url)    
    #     if current_user.user_type=='161':
    #         return redirect(url_for('app.openJobs'))
    #     else:
    #         return redirect(url_for('dashboard.index'))

    # form = LoginForm()
    # print('Validation')
    # print(form.validate_on_submit())
    # session['isGooglelogin'] = ''
    # if form.validate_on_submit() or glogin=="True":
    #     if glogin=="True":
    #         print("###glogin val"+ str(glogin))
    #         print("###email received from page"+ str(gemail))
    #         user=User.query.filter_by(email=gemail).first()   
    #         if user is None:
    #             flash("Email not registered")
    #             print('Email not registered')
    #             return redirect(url_for('accounts.login'))
    #     else: 
    #         print('Input data:'+str(form.email.data))
    #         checkEmailValidation = check(form.email.data)
    #         user = ''
    #         if checkEmailValidation == 'Y':
    #             user=User.query.filter_by(email=form.email.data).first() 
    #         else:
    #             Input = form.email.data
    #             print('Type:'+str(type(Input)))
    #             In = Input.upper()
    #             string = 'stud_'
    #             strg = string.upper()
    #             print('Type:'+str(type(strg))+'String:'+str(strg))
    #             if In.find(strg) == 0:
    #                 print('this is student id')
    #                 studentId = Input[5:]
    #                 print('studentId:'+str(studentId))
    #                 studData = StudentProfile.query.filter_by(student_id=studentId).first()
    #                 email = studData.email
    #                 user=User.query.filter_by(email=email).first() 
    #             else:
    #                 print('phone no')
    #                 user=User.query.filter_by(phone=Input).first()

    #         try:             
    #             if user is None or not user.check_password(form.password.data):        
    #                 flash("Invalid email or password")
    #                 return redirect(url_for('accounts.login'))
    #         except:
    #             flash("Invalid email or password")
    #             return redirect(url_for('accounts.login'))

    #     try:
    #         login_user(user,remember=form.remember_me.data)
    #     except:
    #         flash("Invalid email or password")
    #         return redirect(url_for('accounts.login'))

    #     next_page = request.args.get('next')
    #     print('next_page',next_page)
    #     if not next_page or url_parse(next_page).netloc != '':
    #         print('if next_page is not empty',next_page)
    #         next_page = url_for('dashboard.index')
        
    #     session['classSecVal'] = classSecCheck()
    #     session['schoolName'] = schoolNameVal()
        
    #     print('user name')
    #     school_id = ''
    #     print('user type')
    #     session['studentId'] = ''
    #     if current_user.user_type==253:
    #         school_id=1
    #     elif current_user.user_type==71:
    #         userProfileData = User.query.filter_by(id=current_user.id).first()
    #         school_id = userProfileData.school_id
    #     elif current_user.user_type==134:
    #         studentProfileData = StudentProfile.query.filter_by(user_id=current_user.id).first()
    #         school_id = studentProfileData.school_id            
    #         session['studentId'] = studentProfileData.student_id
    #     else:
    #         userData = User.query.filter_by(id=current_user.id).first()
    #         school_id = userData.school_id

    #     school_pro = SchoolProfile.query.filter_by(school_id=school_id).first()
    #     session['school_logo'] = ''
    #     print('school_pro:'+str(school_pro))
    #     session['isGooglelogin'] = ''
    #     if school_pro:
    #         session['school_logo'] = school_pro.school_logo
    #         session['schoolPicture'] = school_pro.school_picture
    #         session['schoolName'] = school_pro.school_name
    #         session['font'] = school_pro.font
    #         print('session[font]:'+str(session['font']))
    #         session['primary_color'] = school_pro.primary_color
    #         session['isGooglelogin'] = school_pro.google_login
    #         print('session[isGooglelogin]:'+str(session['isGooglelogin']))
    #         print('school_pro.google_login:'+str(school_pro.google_login))
    #         session['show_school_name'] = school_pro.show_school_name
    #         teacherData = TeacherProfile.query.filter_by(teacher_id=school_pro.school_admin).first()
    #         userData = User.query.filter_by(id=teacherData.user_id).first()
    #         session['phone'] = userData.phone
    #         session['email'] = userData.email
    #     print(session['primary_color'])
    #     query = "select user_type,md.module_name,description, module_url, module_type from module_detail md inner join module_access ma on md.module_id = ma.module_id where user_type = '"+str(current_user.user_type)+"' and ma.is_archived = 'N' and md.is_archived = 'N' order by module_type"
    #     print(query)
    #     print('Modules')
    #     moduleDetRow = db.session.execute(query).fetchall()
    #     print('School profile')

    #     session['moduleDet'] = []
    #     detList = session['moduleDet']
        
    #     for det in moduleDetRow:
    #         eachList = []

    #         eachList.append(det.module_name)
    #         eachList.append(det.module_url)
    #         eachList.append(det.module_type)
    #         detList.append(eachList)
    #     session['moduleDet'] = detList


    #     return redirect(next_page)        
    # schoolName = ''
    # schoolLogo = ''
    # primaryColor = '' 
    # phone = ''
    # email = ''
    # print('Url:'+str(request.url))
    # subDom = request.url
    # newDom = 'accounts.login'
    # print('login:'+str(newDom))
    # newSubDom = subDom.partition(newDom)
    # newSub = newSubDom[0] + newSubDom[1]
    # print('newSubDom:'+str(newSub))
    # schoolDataQuery = "select *from school_profile where sub_domain like '"+str(newSub)+"%'"
    # schoolData = db.session.execute(text(schoolDataQuery)).fetchall()   
    # print(subDom)
    # font=''
    # for row in schoolData:
    #     print(row)
    #     if row:
    #         schoolName = row.school_name
    #         schoolLogo = row.school_logo
    #         primaryColor = row.primary_color
    #         font = row.font
    #         print('font:'+str(font))
    #         print('primaryColor:'+str(primaryColor))
    #         teacherData = TeacherProfile.query.filter_by(teacher_id=row.school_admin).first()
    #         userData = User.query.filter_by(id=teacherData.user_id).first()
    #         phone = userData.phone
    #         email = userData.email
    # print('phone:'+str(phone))
    # print('email:'+str(email))
    # return render_template('login.html',font=font,phone=phone,email=email,primaryColor=primaryColor,schoolName=schoolName,schoolLogo=schoolLogo, title='Sign In', form=form)

    # if current_user.is_authenticated:
    #     return redirect(url_for('dashboard.index'))

    # form = RegistrationForm() 
    # if form.validate_on_submit():
    #     print('Validated form submit')
    #     user = User(username=form.email.data, email=form.email.data, user_type='140', access_status='145', phone=form.phone.data,
    #         first_name = form.first_name.data,school_id=1,last_name= form.last_name.data)
    #     user.set_password(form.password.data)
    #     db.session.add(user)
    #     db.session.commit()
    #     checkTeacherProf = TeacherProfile.query.filter_by(email=form.email.data).first()
    #     checkStudentProf = StudentProfile.query.filter_by(email=form.email.data).first()

    #     if checkTeacherProf!=None:
    #         checkTeacherProf.user_id=user.id
    #         db.session.commit()        
    #     elif checkStudentProf!=None:
    #         checkStudentProf.user_id=user.id
    #         db.session.commit()
    #     else:
    #         pass

    #     full_name = str(form.first_name.data)+ ' '+str(form.last_name.data)
    #     flash('Congratulations '+full_name+', you are now a registered user!')
    #     welcome_email(str(form.email.data), full_name)
    #     print("Abdullah--")
    #     return redirect(url_for('accounts.login'))
    return jsonify({'message':'Invalid credentials'})


@accounts.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('dashboard.index'))

@accounts.route("/account/")
@login_required
def account():
    return render_template('account.html')

@accounts.route("/submit_form/", methods = ["POST"])
@login_required
def submit_form():
    #teacherProfile = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #teacherProfile.teacher_name = request.form["full-name"]
    #teacherProfile.profile_picture = request.form["avatar-url"]
    #db.session.commit()
    #flash('DB values updated')
    return redirect(url_for('accounts.account'))

@accounts.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('accounts.login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)    

@accounts.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('dashboard.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('accounts.login'))
    return render_template('reset_password_page.html', form=form)  

@accounts.route('/setGoogleLogin',methods=['POST','GET'])
def setGoogleLogin():
    isgoogleLogin = request.args.get('isGoogleLogin')
    school_id = request.args.get('school_id')
    schoolData = SchoolProfile.query.filter_by(school_id=school_id).first()
    print(isgoogleLogin)
    schoolData.google_login = isgoogleLogin
    db.session.commit()
    session['isGooglelogin'] = isgoogleLogin
    return jsonify([0])
