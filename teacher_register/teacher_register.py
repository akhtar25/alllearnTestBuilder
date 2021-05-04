from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, Response,session,jsonify
from applicationDB import *
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime
from flask import g, jsonify
from sqlalchemy import func, distinct, text, update


teacher_register= Blueprint('teacher_register',__name__)

@teacher_register.route('/teacherRegistration')
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
@teacher_register.route('/teacherRegForm',methods=['GET','POST'])
def teacherRegForm():
    bankName =request.form.get('bankName')
    accountHolderName = request.form.get('accountHoldername')
    accountNo = request.form.get('accountNumber')
    IfscCode = request.form.get('ifscCode')
    selectSchool = request.form.get('selectSchool')
    selectedSchool = request.form.get('NewSchool')
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
            school_id=schoolEx.school_id, vendubmitPostor_id=vendorId,
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
