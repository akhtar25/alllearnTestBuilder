from Student_TC.utils import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, session,jsonify
from applicationDB import *
from flask_login import LoginManager, current_user, logout_user, login_required
from datetime import datetime
from flask import g, jsonify


student_tc = Blueprint('student_tc',__name__)



@student_tc.route('/studTC',methods=["GET","POST"])
@login_required
def studTC():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #tcdata = TransferCerts.query.filter_by(is_archived='N', school_id=teacherData.school_id).all()
    tcDataQuery = "select sp.student_id, sp.school_adm_number, sp.first_name, sp.last_name, cs.class_val, cs.section, tc.tc_url, tc.tc_id "
    tcDataQuery = tcDataQuery + " from transfer_certs tc left join student_profile sp on tc.student_id=sp.student_id "
    tcDataQuery = tcDataQuery + " inner join class_Section cs on cs.class_Sec_id=sp.class_sec_id"
    tcDataQuery = tcDataQuery + " where tc.is_archived='N' and tc.school_id="+ str(teacherData.school_id)
    tcData = db.session.execute(tcDataQuery).fetchall()
    if request.method=="POST":
        student_id = request.form.get('student_id')
        school_adm_number = request.form.get('school_adm_number')
        teacher_id = teacherData.teacher_id
        school_id = teacherData.school_id
        tc_url =  request.form.get('pdfURL')
        #student_id = request.form.get('student_id')
        if school_adm_number:
            chkStudentData = StudentProfile.query.filter_by(school_adm_number=school_adm_number,school_id=school_id).first()
            if chkStudentData!=None:
                transferDataAdd = TransferCerts(student_id=chkStudentData.student_id, school_adm_number=school_adm_number, teacher_id=teacher_id
                    ,school_id=school_id, tc_url=tc_url,is_archived='N', last_modified_date=datetime.today())
                db.session.add(transferDataAdd)
                db.session.commit()
                flash('TC Uploaded Successfully!')
            else:
                flash(Markup('<span class="red-text"> Student ID invalid. Please try again.</span>'))
        elif student_id:
            chkStudentData = StudentProfile.query.filter_by(student_id=student_id,school_id=school_id).first()
            if chkStudentData!=None:
                transferDataAdd = TransferCerts(student_id=student_id, school_adm_number=chkStudentData.school_adm_number, teacher_id=teacher_id
                    ,school_id=school_id, tc_url=tc_url,is_archived='N', last_modified_date=datetime.today())
                db.session.add(transferDataAdd)
                db.session.commit()
                flash('TC Uploaded Successfully!')
            else:
                flash(Markup('<span class="red-text"> Student ID invalid. Please try again.</span>'))
        else:
            flash(Markup('<span class="red-text"> Please Enter Student Id or School Admission Number. Please try again.</span>'))
    indic='DashBoard'
    return render_template('studTC.html',indic=indic,tcData=tcData,title='Student TC')

@student_tc.route('/archiveTCClass',methods=["GET","POST"])
@login_required
def archiveTCClass():
    tc_id = request.args.get('tc_id')
    tcData = TransferCerts.query.filter_by(tc_id=tc_id).first()
    tcData.is_archived='Y'
    db.session.commit()
    return jsonify(['0'])

@student_tc.route('/accessStudTC')
def accessStudTC():
    school_id = request.args.get('school_id')
    if school_id!=None and school_id!="":
        schoolData = SchoolProfile.query.filter_by(school_id=str(school_id)).first()
        if schoolData!=None:
            return render_template('accessStudTC.html',schoolData=schoolData)
        else:
            return jsonify(['Invalid School Data'])
    #if ("alllearn" in str(request.url)) or  ("localhost" in str(request.url)) ("tc" in str(request.url)) or ("wix" in str(request.url)) :        
    
    #else:
    #    return jsonify(['Invalid Call'])

@student_tc.route('/fetchStudTC')
def fetchStudTC():
    # student_id = request.args.get('student_id')
    school = current_user.school_id
    print('School id:'+str(school))
    school_adm_number = request.args.get('school_adm_number')
    student = StudentProfile.query.filter_by(school_adm_number = school_adm_number,school_id=school).first()
    tcData = TransferCerts.query.filter_by(student_id=student.student_id,is_archived='N'  ).first()    
    if tcData!=None:
        if tcData.tc_url!=None and tcData.tc_url!="":
            return jsonify([tcData.tc_url])
        else:
            return jsonify(['NA'])    
    else:
        return jsonify(['NA'])    
