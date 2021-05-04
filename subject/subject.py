from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, Response,session
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
import datetime as dt
from flask import g, jsonify
from sqlalchemy import func, distinct, text, update


subject = Blueprint('subject',__name__)

@subject.route('/addTeacherClassSubject',methods=['GET','POST'])
def addTeacherClassSubject():
    subjectNames = request.get_json()
    print('Inside add Teacher class Subject')
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = request.args.get('class_sec_id')
    teacher_id = request.args.get('teacher_id')
    remdata = "update teacher_subject_class set is_archived = 'Y' where class_sec_id='"+str(class_sec_id)+"' and school_id = '"+str(teacher.school_id)+"'  and teacher_id = '"+str(teacher_id)+"'"
    remdata = db.session.execute(text(remdata))
    for subjects in subjectNames:
        print('inside for')
        print(subjects)
        subject_id = "select msg_id from message_detail where description='"+str(subjects)+"'"
        subject_id = db.session.execute(text(subject_id)).first()
        
        
        addTeacherClass = TeacherSubjectClass(teacher_id=teacher_id,class_sec_id=class_sec_id,subject_id=subject_id.msg_id,is_archived='N',school_id=teacher.school_id,last_modified_date=dt.datetime.now())
        db.session.add(addTeacherClass)
        db.session.commit()
    return ""

@subject.route('/loadSubject',methods=['GET','POST'])
def loadSubject():
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    teacher_id = request.args.get('teacher_id')
    class_sec_id = request.args.get('class_sec_id')
    class_val = ClassSection.query.filter_by(class_sec_id=class_sec_id,school_id=teacher.school_id).first()
    allSubjects = "select distinct subject_id from board_class_subject bcs where school_id = '"+str(teacher.school_id)+"' and class_val = '"+str(class_val.class_val)+"' and is_archived = 'N' and subject_id "
    allSubjects = allSubjects + "not in (select distinct subject_id from teacher_subject_class where school_id= '"+str(teacher.school_id)+"' and is_archived = 'N' and class_sec_id = '"+str(class_sec_id)+"' and teacher_id='"+str(teacher_id)+"')"
    allSubjects = db.session.execute(text(allSubjects)).fetchall()

    selSubjects = "select distinct subject_id from teacher_subject_class where school_id= '"+str(teacher.school_id)+"' and is_archived = 'N' and class_sec_id = '"+str(class_sec_id)+"' and teacher_id='"+str(teacher_id)+"'"
    selSubjects = db.session.execute(text(selSubjects)).fetchall()
    selArray = []
    for subjects in allSubjects:
        subject_name = "select description from message_detail where msg_id='"+str(subjects.subject_id)+"'"
        subject_name = db.session.execute(text(subject_name)).first()
        selArray.append(str(subject_name.description)+':'+str('false'))
    for sub in selSubjects:
        subject_name = "select description from message_detail where msg_id='"+str(sub.subject_id)+"'"
        subject_name = db.session.execute(text(subject_name)).first()
        selArray.append(str(subject_name.description)+':'+str('true'))
    if selArray:
        return jsonify([selArray])
    else:
        return ""

@subject.route('/loadClasses',methods=['GET','POST'])
def loadClasses():
    teacher_id = request.args.get('teacher_id')
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_val = ClassSection.query.filter_by(school_id=teacher.school_id).all()
    classes = []
    print(teacher.school_id)
    for clas in class_val: 
        teacher = TeacherSubjectClass.query.filter_by(teacher_id=teacher_id,class_sec_id=clas.class_sec_id).first()
        if teacher:
            classes.append(str(clas.class_val)+':'+str(clas.class_sec_id)+':'+str(clas.section)+':'+str('true'))
        else:
            classes.append(str(clas.class_val)+':'+str(clas.class_sec_id)+':'+str(clas.section)+':'+str('false'))
        
    return jsonify([classes])

@subject.route('/teacherAllocation',methods=['GET','POST'])
def teacherAllocation():
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_ids = ClassSection.query.filter_by(school_id=teacher_id.school_id).all()
    fetchTeacherNameQuery = "select distinct tp.teacher_name,tp.teacher_id from teacher_profile tp "
    fetchTeacherNameQuery = fetchTeacherNameQuery + "left join teacher_subject_class tsc on tsc.teacher_id=tp.teacher_id "
    fetchTeacherNameQuery = fetchTeacherNameQuery + "where tp.school_id='"+str(teacher_id.school_id)+"'"
    print(fetchTeacherNameQuery)
    teacherNames = db.session.execute(text(fetchTeacherNameQuery)).fetchall()
    print('Inside teacher class subject allocation')
    return render_template('_teacherAllocation.html',teacherNames=teacherNames,class_sec_ids=class_sec_ids)
