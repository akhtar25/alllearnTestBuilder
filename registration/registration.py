from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, session,jsonify
from send_email import send_password_reset_email, user_access_request_email,user_school_access_request_email, access_granted_email, new_school_reg_email, performance_report_email,test_report_email,notificationEmail
from applicationDB import *
from forms import LoginForm, RegistrationForm,ContentManager,LeaderBoardQueryForm, EditProfileForm, ResetPasswordRequestForm, \
    ResultQueryForm,MarksForm, TestBuilderQueryForm,SchoolRegistrationForm, PaymentDetailsForm, addEventForm, \
    SingleStudentRegistration, SchoolTeacherForm, feedbackReportForm, studentPerformanceForm, QuestionBankQueryForm,studentDirectoryForm, promoteStudentForm
from forms import createSubscriptionForm,ClassRegisterForm, AddLiveClassForm
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
import os
import datetime as dt
from datetime import datetime
from flask import g, jsonify
import json, boto3
from sqlalchemy import func, distinct, text, update
import pandas as pd
import numpy as np


registration= Blueprint('registration',__name__)

@registration.route('/teacherRegistration')
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
@registration.route('/teacherRegForm',methods=['GET','POST'])
def teacherRegForm():
    bankName =request.form.get('bankName')
    accountHolderName = request.form.get('accountHoldername')
    accountNo = request.form.get('accountNumber')
    IfscCode = request.form.get('ifscCode')
    selectSchool = request.form.get('selectSchool')
    selectedSchool = request.form.get('NewSchool')
    if selectSchool==None:
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



@registration.route('/bulkStudReg')
def bulkStudReg():
    return render_template('_bulkStudReg.html')

@registration.route('/singleStudReg')
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



@registration.route('/studentRegistration', methods=['GET','POST'])
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

@registration.route('/classRegistration', methods=['GET','POST'])
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




@registration.route('/schoolRegistration', methods=['GET','POST'])
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
