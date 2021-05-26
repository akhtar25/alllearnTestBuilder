from flask import current_app as app
from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, redirect, url_for, session,jsonify
from applicationDB import *
import csv
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
import os
from datetime import datetime
from flask import g, jsonify
import json, boto3
from sqlalchemy import func, distinct, text
attendance = Blueprint('attendance',__name__)

@attendance.route('/attendanceReport',methods=["GET","POST"])
def attendanceReport():
    class_sec_id = request.args.get('class_sec_id')
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first() 
    attendanceData = "select full_name, is_present from attendance a inner join student_profile sp on a.class_sec_id = sp.class_sec_id where "
    attendanceData = attendanceData + "sp.school_id = '"+str(teacherDataRow.school_id)+"' and sp.class_sec_id = '"+str(class_sec_id)+"'"
    attendanceData = db.session.execute(text(attendanceData)).fetchall()
    file_name='Attendance'+str(class_sec_id)+str(teacherDataRow.school_id)+'.csv'
    file_name = file_name.replace(" ", "")
    if not os.path.exists('tempdocx'):
        os.mkdir('tempdocx')
    # document.save('tempdocx/'+file_name)
    with open('tempdocx/'+file_name, 'w', newline='') as file:
    #uploading to s3 bucket
        
        # with open(filePath, 'w', newline='') as file:
            
        print('file')
            
        file.write('Introduction \n')
        writer = csv.writer(file)
        writer.writerow(["Student Name ", "Present"])
        for data in attendanceData:
            writer.writerow([data.full_name,data.is_present])
    client = boto3.client('s3', region_name='ap-south-1')
    client.upload_file('tempdocx/'+file_name , os.environ.get('S3_BUCKET_NAME'), 'attendance_report/{}'.format(file_name),ExtraArgs={'ACL':'public-read'})
        #deleting file from temporary location after upload to s3
    os.remove('tempdocx/'+file_name)
    filePath = 'https://'+str(os.environ.get('S3_BUCKET_NAME'))+'.s3.ap-south-1.amazonaws.com/attendance_report/'+str(file_name)
    print(filePath)
    return jsonify([filePath])


@attendance.route('/addAttendence',methods=["GET","POST"])
def addAttendence():
    class_sec_id = request.args.get('class_sec_id')
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first() 
    students = StudentProfile.query.filter_by(class_sec_id=class_sec_id,school_id=teacherDataRow.school_id).all()
    print('class_Sec_id:'+str(class_sec_id))
    print('school_id'+str(teacherDataRow.school_id))
    student_ids = request.get_json()
    print(students)
    print(student_ids)
    data = Attendance.query.filter_by(class_sec_id=class_sec_id,school_id=teacherDataRow.school_id).first()
    if data:
        for student_id in students:
            sel = 0
            
            for selected in student_ids:
                if str(student_id.student_id) == str(selected):
                    print('if student id is selected:'+str(student_id.student_id))
                    sel =1
                    break
            if sel==1:
                print('set Y for selected ')
                update = Attendance.query.filter_by(class_sec_id=class_sec_id,school_id=teacherDataRow.school_id,student_id=student_id.student_id).first()
                update.is_present = 'Y'
            else:
                update = Attendance.query.filter_by(class_sec_id=class_sec_id,school_id=teacherDataRow.school_id,student_id=student_id.student_id).first()
                update.is_present = 'N'
            db.session.commit()    
    else:
        for student_id in students:
            sel = 0
            
            for selected in student_ids:
                if str(student_id.student_id) == str(selected):
                    print('if student id is selected:'+str(student_id.student_id))
                    sel =1
                    break
            if sel==1:
                print('set Y for selected ')
                addData = Attendance(school_id=teacherDataRow.school_id,teacher_id=teacherDataRow.teacher_id,attendance_date=datetime.today(),last_modified_date=datetime.today(),
                is_present='Y',class_sec_id=class_sec_id,student_id=student_id.student_id)
            else:
                addData = Attendance(school_id=teacherDataRow.school_id,teacher_id=teacherDataRow.teacher_id,attendance_date=datetime.today(),last_modified_date=datetime.today(),
                is_present='N',class_sec_id=class_sec_id,student_id=student_id.student_id)
            db.session.add(addData)
            db.session.commit()
    return jsonify(['1'])


@attendance.route('/fetchAttendenceList',methods=["GET","POST"])
def fetchAttendenceList():
    class_sec_id = request.args.get('class_sec_id')
    date = request.args.get('date')
    print('Date:'+str(date))
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first() 
    if date:
        fetchData = "select sd.student_id,full_name,sd.profile_picture,a.is_present "
        fetchData = fetchData + "from attendance a right join student_profile sd on a.student_id=sd.student_id "
        fetchData = fetchData + "where sd.class_sec_id="+str(class_sec_id)+" and sd.school_id='"+str(teacherDataRow.school_id)+"' and date(attendance_date)='"+str(date)+"' order by full_name "
    else:
        fetchData = "select sd.student_id,full_name,sd.profile_picture,a.is_present "
        fetchData = fetchData + "from attendance a right join student_profile sd on a.student_id=sd.student_id "
        fetchData = fetchData + "where sd.class_sec_id="+str(class_sec_id)+" and sd.school_id='"+str(teacherDataRow.school_id)+"' order by full_name "
    print('Query:'+str(fetchData))
    studAttendeceList = db.session.execute(fetchData).fetchall()
    print('class_sec_id:'+str(class_sec_id))
    for row in studAttendeceList:
        print('Fetch Data:'+str(row.is_present))
    return render_template('_attendanceTable.html',studAttendeceList=studAttendeceList)

@attendance.route('/addStudentRemarks',methods = ["GET","POST"])
def addStudentRemarks():
    remark_desc=request.form.get('remark')
    student_id = request.form.get('student_id')
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()        
    try:
        studentRemarkAdd = StudentRemarks(student_id=student_id, remark_desc=remark_desc, teacher_id=teacherDataRow.teacher_id,
            is_archived = 'N', last_modified_date = datetime.today())
        db.session.add(studentRemarkAdd)
        db.session.commit()
        return jsonify(['0'])
    except:
        return jsonify(['1'])

def classChecker(available_class):
    class_list = []
    for k in available_class:
        if k.class_val == '99':
            class_list.append((str('LKG')+"-"+str(k.section),str('LKG')+"-"+str(k.section)))
            print('inside available classes')
        elif k.class_val == '100':
            class_list.append((str('UKG')+"-"+str(k.section),str('UKG')+"-"+str(k.section)))
        else:
            class_list.append((str(k.class_val)+"-"+str(k.section),str(k.class_val)+"-"+str(k.section)))
    return class_list
