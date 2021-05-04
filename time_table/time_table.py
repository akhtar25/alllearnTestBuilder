from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, Response,session,jsonify
import csv
from flask_login import current_user, login_user, logout_user, login_required
import os
import datetime as dt
from flask import g, jsonify
import json, boto3
from sqlalchemy import func, distinct, text, update
from random import randint


time_table= Blueprint('time_table',__name__)

@time_table.route('/updateSchedule',methods=['POST','GET'])
def updateSchedule():
    slots = request.form.get('slots')
    class_value = request.args.get('class_val')
    print('No of slots:'+str(slots))
    print('Class_val:'+str(class_value))
    # start = request.form.getlist('start')
    # end = request.form.getlist('end')
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    sections = ClassSection.query.filter_by(school_id=teacher.school_id,class_val=class_value).all()
    batches = len(sections)
    slotTime = []
    # for (s,e) in itertools.zip_longest(start,end):
    #     slotTime.append(s+'-'+e)
    print('inside schedule')
    # nDays = request.form.get('nDays')
    noTeachers = request.form.get('noTeachers')
    nameTeacher = request.form.getlist('nameTeacher')
    nameSubject = request.form.getlist('nameSubject')
    subject = request.form.getlist('subject')
    time = request.form.getlist('time')
    day = request.form.getlist('day')
        # batches = request.form.get('batches')
    print('No of Days:'+str(len(day)))
    nDays = len(day)
    totalTime = 0
    for ti in time:
            # print('Time:'+str(ti))
        if ti:
            totalTime = totalTime + int(ti)
    totalSlots = int(nDays)*int(slots)
        # print('Total slots:'+str(totalSlots))
        # print('Total Time:'+str(totalTime))
    perSlots = []
    for s in range(int(slots)):
                
        perSlots.append(s+1)
    slotsoutput = cal(perSlots)

        # for slot in range(len(slotsoutput)):
            # print('slot'+str(slot))
            # print(slotsoutput[slot])
    finalSlot = []
    indexSlot = []
        # print('outside while loop')
    p=0
        # print('length of slots output')
        # print(len(slotsoutput))
    while p<len(slotsoutput):
            # print('inside while loop')
        r = randint(0,len(slotsoutput)-1)
        if r not in indexSlot:
            p=p+1
            indexSlot.append(r)
        # print(indexSlot)
    for index in indexSlot:
        finalSlot.append(slotsoutput[index])
        # print(finalSlot)
        

        # print('slot output print')
        # print(slotsoutput)
    t=1
    z=0
    class_sec_ids = ClassSection.query.filter_by(class_val = class_value, school_id = teacher.school_id).all() 
    for class_sec_id in class_sec_ids:
        updateTable = "update schedule_detail set is_archived = 'Y' where class_sec_id='"+str(class_sec_id.class_sec_id)+"' and school_id='"+str(teacher.school_id)+"'"
        updateTable = db.session.execute(text(updateTable))
    for l in subject:
            # print(l)
        if(l):
            z=z+1
        # print('No of Subjects:'+str(z))
    if totalSlots>=totalTime:

        for arr1 in finalSlot:
            if t<=int(batches):    
                            
                    
                for i in range(0,z):

                    for j in range(0,int(time[i])):
                            
                        class_sec_id = "select class_sec_id from class_section where class_val='"+str(class_value)+"' and section='"+chr(ord('@')+t)+"' and school_id='"+str(teacher.school_id)+"'"
                            
                        class_sec_id = db.session.execute(text(class_sec_id)).first()
                        subject_id = "select msg_id from message_detail where description='"+str(subject[i])+"'"
                        subject_id = db.session.execute(text(subject_id)).first()
                        teacher_id = TeacherSubjectClass.query.filter_by(class_sec_id=class_sec_id.class_sec_id,subject_id=subject_id.msg_id,school_id=teacher.school_id,is_archived='N').first()
                           
                        if teacher_id:
                            insertData = ScheduleDetail(class_sec_id=class_sec_id.class_sec_id ,school_id=teacher.school_id, days_name=day[j] ,subject_id=subject_id.msg_id , teacher_id=teacher_id.teacher_id ,slot_no=arr1[i] , last_modified_date=dt.datetime.now(), is_archived= 'N')
                        else:
                            insertData = ScheduleDetail(class_sec_id=class_sec_id.class_sec_id ,school_id=teacher.school_id, days_name=day[j] ,subject_id=subject_id.msg_id  ,slot_no=arr1[i] , last_modified_date=dt.datetime.now(), is_archived= 'N')
                        db.session.add(insertData)
            t=t+1
    else:
        return jsonify(['1'])
    db.session.commit()
    print('Data is Submitted') 
    return jsonify(['0'])

@time_table.route('/schedule')
def schedule():
    # slots = request.form.get('slots')
    # print('inside schedule function')
    # print(slots)
    qclass_val = request.args.get("class_val")
    qsection = request.args.get("section")
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    classSections=ClassSection.query.filter_by(school_id=teacher.school_id).all()
    available_class_section = "select distinct class_val,section from class_section where school_id='"+str(teacher.school_id)+"'"
    available_class_section = db.session.execute(text(available_class_section)).fetchall()
    distinctClasses = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacher.school_id)+" GROUP BY class_val order by s")).fetchall()  
    if qclass_val==None and qsection == None:
        qclass_val = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacher.school_id)+" GROUP BY class_val order by s")).first()  
        qclass_val = qclass_val.class_val
        qsection = ClassSection.query.filter_by(school_id=teacher.school_id).first()
        qsection = qsection.section
    indic='DashBoard'
    return render_template('schedule.html',indic=indic,classsections=classSections,distinctClasses=distinctClasses,available_class_section=available_class_section,qclass_val=qclass_val,qsection=qsection)
    
@time_table.route('/fetchTimeTable',methods=['GET','POST'])
def fetchTimeTable():
    class_val = request.args.get('class_value')
    section = request.args.get('section')
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print(class_val)
    print(section)
    print(teacher.school_id)
    class_section = ClassSection.query.filter_by(class_val=str(class_val),section = section, school_id= teacher.school_id).first()

    query = "select *from fn_time_table("+str(teacher.school_id)+","+str(class_section.class_sec_id)+")"
    print(query)
    timeTableData = db.session.execute(text(query)).fetchall()
    print(timeTableData)
    for data in timeTableData:
        print(data)
    fetchTeacher = "select *from fn_teacher_allocation("+str(teacher.school_id)+","+str(class_section.class_sec_id)+")"
    print(fetchTeacher)
    fetchTeacher = db.session.execute(text(fetchTeacher)).fetchall()
    print(fetchTeacher)
    return render_template('_timeTable.html',timeTableData=timeTableData,fetchTeacher=fetchTeacher)

@time_table.route('/downloadTimeTable',methods=['GET','POST'])
def downloadTimeTable():
    print('inside download time table')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    # fetchTeacher = "select *from fn_teacher_allocation("+str(teacher_id.school_id)+","+str(class_section.class_sec_id)+")"
    # print(fetchTeacher)
    # fetchTeacher = db.session.execute(text(fetchTeacher)).fetchall()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    class_sec_ids = ClassSection.query.filter_by(school_id=teacher_id.school_id).all()
    # filepath = 'static/images/'+str(teacher_id.school_id)+str(dt.datetime.now())+'TimeTable.csv'
    file_name = 'Timetable'+str(teacher_id.school_id)+'.csv'
    with open('tempdocx/'+file_name, 'w', newline='') as file:
        
    
        
        print('file')
        
        file.write('Introduction \n')
        writer = csv.writer(file)
        for class_sec_id in class_sec_ids:
            fetchTeacher = "select *from fn_teacher_allocation("+str(teacher_id.school_id)+","+str(class_sec_id.class_sec_id)+")"
            print(fetchTeacher)
            
            fetchTeacher = db.session.execute(text(fetchTeacher)).fetchall()
            writer.writerow(["Subject Name", "Teacher Name"])
            # writer.writerow(["", "Name", "Contribution"])
            for teacher in fetchTeacher:
                print(teacher.subject_name)
                print(teacher.teacher_name)
                writer.writerow([teacher.subject_name,teacher.teacher_name])
                # os.remove(filepath)
                print('File path')
            query = "select *from fn_time_table("+str(teacher_id.school_id)+","+str(class_sec_id.class_sec_id)+")"
            print(query)
            timeTableData = db.session.execute(text(query)).fetchall()
            writer.writerow(["Periods", "Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"])
            
            for table in timeTableData:
                writer.writerow([table.period_no,table.monday,table.tuesday,table.wednesday,table.thursday,table.friday,table.saturday])
            writer.writerow(["","","","","","",""])
    client = boto3.client('s3', region_name='ap-south-1')
    client.upload_file('tempdocx/'+file_name , os.environ.get('S3_BUCKET_NAME'), 'time_table/{}'.format(file_name),ExtraArgs={'ACL':'public-read'})
    os.remove('tempdocx/'+file_name)
    filepath ='https://'+os.environ.get('S3_BUCKET_NAME')+'.s3.ap-south-1.amazonaws.com/time_table/'+file_name
    print('filepath:'+str(filepath))
    return jsonify([filepath])

@time_table.route('/allSubjects',methods=['GET','POST'])
def allSubjects():
    print('inside all Subjects')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    school_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    class_val = request.args.get('class_value') 
    print(class_val)
    print(teacher_id.school_id)
    subjects = BoardClassSubject.query.filter_by(class_val = str(class_val),school_id=teacher_id.school_id,is_archived='N').all()
    subjectList = []
    for subject in subjects:
        subject_name = "select description from message_detail where msg_id='"+str(subject.subject_id)+"'"
        subject_name = db.session.execute(text(subject_name)).first()
        
        subjectList.append(str(subject_name.description))
    return jsonify([subjectList])
