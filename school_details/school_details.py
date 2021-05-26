from applicationDB import *
from flask import Flask, Blueprint, render_template, request, redirect, url_for, Response,session
from applicationDB import *
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from sqlalchemy import func, text, update


school_details= Blueprint('school_details',__name__)

@school_details.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@school_details.route('/schoolPerformanceRanking')
@login_required
def schoolPerformanceRanking():
    return render_template('schoolPerformanceRanking.html')

@school_details.route('/recommendations')
@login_required
def recommendations():
    return render_template('recommendations.html')


@school_details.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html')

@school_details.route('/inReviewSchool')
def inReviewSchool():
    print('In review school:'+str(current_user.user_type))
    return render_template('inReviewSchool.html', disconn = 1)

@school_details.route('/schoolProfile')
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
