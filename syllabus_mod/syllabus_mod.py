from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, Response,session,jsonify
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime
from flask import g, jsonify
from sqlalchemy import func, distinct, text, update


syllabus_mod= Blueprint('syllabus_mod',__name__)

@syllabus_mod.route('/syllabus')
@login_required
def syllabus():
    fromSchoolRegistration = False
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
    for clas in classValues:
        print('Class value:'+str(clas.class_val))
    indic='DashBoard'
    return render_template('syllabus.html',indic=indic,title='Syllabus',generalBoard=generalBoard,boardRowsId = boardRows.msg_id , boardRows=boardRows.description,subjectValues=subjectValues,school_name=school_id.school_name,classValues=classValues,classValuesGeneral=classValuesGeneral,bookName=bookName,chapterNum=chapterNum,topicId=topicId,fromSchoolRegistration=fromSchoolRegistration,user_type_val=str(current_user.user_type))

@syllabus_mod.route('/addSyllabus',methods=['GET','POST'])
def addSyllabus():
    print('inside add syllabus')
    classes = request.get_json()
    # class_val = request.args.get('class_val')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    for class_val in classes:
        classExist = ClassSection.query.filter_by(class_val=class_val,section='A',school_id=teacher_id.school_id).first()
        if classExist == None:
            addClass = ClassSection(class_val=class_val,section='A',school_id=teacher_id.school_id,student_count=0,class_teacher=teacher_id.teacher_id,last_modified_date=datetime.now())
            db.session.add(addClass)
            db.session.commit()
    # class_sec_id = ClassSection.query.filter_by(class_val=class_val,section='A',school_id=teacher_id.school_id,student_count=0,class_teacher=teacher_id.teacher_id).first()
    # for subject in subjects:
    #     subject_id = MessageDetails.query.filter_by(description=subject,category='Subject').first()
    #     subjExist = ''
    #     subjExist = BoardClassSubject.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,school_id=teacher_id.school_id).first()
    #     print(subjExist)
    #     if subjExist == None:
    #         print('is subjExist is null')
    #         addSubject = BoardClassSubject(board_id=board_id.board_id,class_val=class_val,subject_id=subject_id.msg_id,is_archived='N',school_id=teacher_id.school_id,last_modified_date=datetime.now())
    #         db.session.add(addSubject)
    #         db.session.commit()
        # bookNames = BookDetails.query.distinct(BookDetails.book_name).filter_by(subject_id=subject_id.msg_id,class_val=class_val).all()
        print('after add subjects')
        # for book_name in bookNames:
        #     book_id = BookDetails.query.filter_by(subject_id=subject_id.msg_id,class_val=class_val,book_name=book_name.book_name).first()
        #     addBook = BoardClassSubjectBooks(school_id=teacher_id.school_id,class_val=class_val,subject_id=subject_id.msg_id,book_id=book_id.book_id,is_archived='N')
        #     db.session.add(addBook)
        #     db.session.commit()
        # insertRow = "insert into topic_tracker (subject_id, class_sec_id, is_covered, topic_id, school_id, reteach_count,is_archived, last_modified_date) (select subject_id, '"+str(class_sec_id.class_sec_id)+"', 'N', topic_id, '"+str(teacher_id.school_id)+"', 0,'N',current_date from Topic_detail where class_val="+str(class_val)+")"
        # db.session.execute(text(insertRow))
        # db.session.commit()
    return ("Syllabus added successfully")

@syllabus_mod.route('/generalSyllabusClasses')
def generalSyllabusClasses():
    board_id=request.args.get('board_id')
    classArray = []
    distinctClasses = "SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs GROUP BY class_val order by s"
    distinctClasses = db.session.execute(text(distinctClasses)).fetchall()
    for val in distinctClasses:
        classArray.append(val.class_val)
    if classArray:
        return jsonify([classArray])
    else:
        return ""

@syllabus_mod.route('/syllabusSubjects')
@login_required
def syllabusSubjects():
    board_id=request.args.get('board_id')
    class_val=request.args.get('class_val')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    distinctSubject = BoardClassSubject.query.filter_by(class_val=class_val,board_id=board_id,school_id=teacher_id.school_id,is_archived='N').all()
    sujectArray=[]
    subjects = "select distinct description,msg_id from message_detail md inner join board_class_subject bcs on md.msg_id = bcs.subject_id where bcs.class_val = '"+str(class_val)+"' and school_id='"+str(teacher_id.school_id)+"' and bcs.is_archived= 'N' order by description"
    subjects = db.session.execute(text(subjects)).fetchall()
    for val in subjects:
        # subject = MessageDetails.query.filter_by(msg_id=val.subject_id).first()
        sujectArray.append(str(val.msg_id)+":"+str(val.description))
    if sujectArray:
        return jsonify([sujectArray])   
    else:
        return ""        

@syllabus_mod.route('/syllabusClasses')
@login_required
def syllabusClasses():
    board_id=request.args.get('board_id')
    classSectionArray = []
    sectionArray = []
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    distinctClasses = "SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id = '"+str(teacher_id.school_id)+"' GROUP BY class_val order by s"
    distinctClasses = db.session.execute(text(distinctClasses)).fetchall()
    for val in distinctClasses:
        #print(val.class_val)
        sections = ClassSection.query.distinct(ClassSection.section).filter_by(school_id=teacher_id.school_id,class_val=val.class_val).all()
        # sectionsString = ''
        sectionsString = '['
        i=1
        for section in sections:
            #print(len(sections))
            if i<len(sections):
                sectionsString = sectionsString + str(section.section)+';'
            else:
                sectionsString = sectionsString + str(section.section)
            i = i + 1
        sectionsString = sectionsString + ']'
        classSectionArray.append(str(val.class_val)+':'+str(sectionsString))
    if classSectionArray:
        return jsonify([classSectionArray])
    else:
        return ""

@syllabus_mod.route('/generalSyllabusSubjects',methods=['GET','POST'])
def generalSyllabusSubjects():
    board_id=request.args.get('board_id')
    class_val=request.args.get('class_val')
    sujectArray=[]
    subjects = "select distinct description,msg_id from message_detail md inner join topic_detail td on md.msg_id = td.subject_id where td.class_val = '"+str(class_val)+"' order by description"
    subjects = db.session.execute(text(subjects)).fetchall()
    for val in subjects:
        # subject = MessageDetails.query.filter_by(msg_id=val.subject_id).first()
        sujectArray.append(str(val.msg_id)+":"+str(val.description))
    if sujectArray:
        return jsonify([sujectArray])   
    else:
        return ""

@syllabus_mod.route('/fetchSubjects',methods=['GET','POST'])
def fetchSubjects():
    class_val = request.args.get('class_val')
    board = request.args.get('board')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    distinctSubject = BoardClassSubject.query.filter_by(class_val=class_val,board_id=board,school_id=teacher_id.school_id,is_archived='N').all()
    sujectArray=[]
    subjects = "select distinct description,msg_id from message_detail md inner join board_class_subject bcs on md.msg_id = bcs.subject_id where bcs.class_val = '"+str(class_val)+"' and school_id='"+str(teacher_id.school_id)+"' and bcs.is_archived= 'N' order by description"
    subjects = db.session.execute(text(subjects)).fetchall()
    for val in subjects:
        # subject = MessageDetails.query.filter_by(msg_id=val.subject_id).first()
        sujectArray.append(str(val.msg_id)+":"+str(val.description))
    if sujectArray:
        return jsonify([sujectArray])   
    else:
        return "" 

@syllabus_mod.route('/fetchRemSubjects',methods=['GET','POST'])
def fetchRemSubjects():
    print('inside fetchRemSubjects')
    class_val = request.args.get('class_val')
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher.school_id).first()
    distinctSubject = BoardClassSubject.query.filter_by(class_val=class_val,board_id=board_id.board_id,school_id=teacher.school_id,is_archived='Y').all()
    subjectArray=[]
    generalSubjects = "select distinct msg_id,description from topic_detail td inner join message_detail md on md.msg_id=td.subject_id "
    generalSubjects = generalSubjects + "where md.msg_id not in (select distinct msg_id from message_detail md "
    generalSubjects = generalSubjects + "inner join board_class_subject bcs on md.msg_id = bcs.subject_id where bcs.class_val = '"+str(class_val)+"' and school_id='"+str(teacher.school_id)+"' "
    generalSubjects = generalSubjects + ")  order by description"
    print('Query: '+str(generalSubjects))
    generalSubjects = db.session.execute(text(generalSubjects)).fetchall()
    subjects = "select distinct description,msg_id from message_detail md inner join board_class_subject bcs on md.msg_id = bcs.subject_id where bcs.class_val = '"+str(class_val)+"' and school_id='"+str(teacher.school_id)+"' and bcs.is_archived= 'Y' order by description"
    print(subjects)
    subjects = db.session.execute(text(subjects)).fetchall()
    for val in subjects:
        # subject = MessageDetails.query.filter_by(msg_id=val.subject_id).first()
        subjectArray.append(str(val.msg_id)+":"+str(val.description))
    for val in generalSubjects:
        subjectArray.append(str(val.msg_id)+":"+str(val.description))
    if subjectArray:
        return jsonify([subjectArray])   
    else:
        return ""

@syllabus_mod.route('/addSubject',methods=['GET','POST'])
def addSubject():
    subject_id = request.args.get('subject')
    board_id=request.args.get('board')
    class_val=request.args.get('class_val')
    print('Subject:'+str(subject_id))
    # subject_id = MessageDetails.query.filter_by(description=subjectVal,category='Subject').first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    subjExist = BoardClassSubject.query.filter_by(class_val=class_val,board_id=board_id,subject_id=subject_id,school_id=teacher_id.school_id).first()
    if subjExist==None:
        addSubject = BoardClassSubject(class_val=class_val,subject_id=subject_id,school_id=teacher_id.school_id,board_id=board_id,is_archived='N')
        db.session.add(addSubject)
        db.session.commit()
    else:
        insertSubject = BoardClassSubject.query.filter_by(class_val=class_val,subject_id=subject_id,school_id=teacher_id.school_id,board_id=board_id,is_archived='Y').first()
        insertSubject.is_archived = 'N'
        db.session.add(insertSubject)
        db.session.commit()
    return ('update data successfully')

@syllabus_mod.route('/addChapter',methods=['GET','POST'])
def addChapter():
    topics=request.get_json()
    print('inside add Chapter')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    chapterName = request.args.get('chapterName')
    
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    chapter_num = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,chapter_name=chapterName).first()
    print(topics)
    print('School id:'+str(teacher_id.school_id))
    for topic in topics:
        print('inside for')
        print(topic)
        # topic_id = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,topic_name=topic).first()
        existInTT = TopicTracker.query.filter_by(topic_id=topic,school_id=teacher_id.school_id,class_sec_id=class_sec_id.class_sec_id,subject_id=subject_id.msg_id).first()
        
        if existInTT:
            updateTT = "update topic_tracker set is_archived='N' where school_id='"+str(teacher_id.school_id)+"' and subject_id='"+str(subject_id.msg_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and topic_id='"+str(topic)+"'"
            print(updateTT)
            updateTT = db.session.execute(text(updateTT))
        else:
            insertTT = TopicTracker(subject_id=subject_id.msg_id,class_sec_id=class_sec_id.class_sec_id,is_covered='N',topic_id=topic,school_id=teacher_id.school_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(insertTT)
        db.session.commit()
    return ("data updated successfully")

@syllabus_mod.route('/addBook',methods=['GET','POST'])
def addBook():
    book_id = request.args.get('book')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    print("class_val"+str(class_val))
    print("subject id"+str(subject_id.msg_id))
    print("book id"+str(book_id))
    book = BookDetails.query.filter_by(book_id=book_id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id).all()
    
    for book_id in bookIds:
        updateBCSB = BoardClassSubjectBooks.query.filter_by(school_id=teacher_id.school_id,class_val=class_val,
        subject_id=subject_id.msg_id,book_id=book_id.book_id).first()
        if updateBCSB:
            updateBCSB.is_archived = 'N'
        else:
            addBook = BoardClassSubjectBooks(school_id=teacher_id.school_id,class_val=class_val,subject_id=subject_id.msg_id,book_id=book_id.book_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(addBook)
        db.session.commit()
    return ("data updated successfully")



@syllabus_mod.route('/addNewSubject',methods=['GET','POST'])
def addNewSubject():
    subject = request.args.get('subject')
    subject = subject.title()
    class_val = request.args.get('class_val')
    board = request.args.get('board')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    insertSubject = MessageDetails(category='Subject',description=subject)
    db.session.add(insertSubject)
    db.session.commit()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    insertBCS = BoardClassSubject(class_val=class_val,subject_id=subject_id.msg_id,school_id=teacher_id.school_id,board_id=board,is_archived='N')
    db.session.add(insertBCS)
    db.session.commit()
    return ('New Subject added successfully')

@syllabus_mod.route('/addNewBook',methods=['GET','POST'])
def addNewBook():
    bookName = request.args.get('book')
    bookLink = request.args.get('bookLink')
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    bookName = bookName.strip()
    for x in bookName.lower(): 
        if x in punctuations: 
            bookName = bookName.replace(x, "") 
            print(bookName)
        else:
            break
    if bookName==None or bookName=='':
        return "NA"
    bookName = bookName.strip()
    bookLink = bookLink.strip()
    for x in bookLink.lower(): 
        if x in punctuations: 
            bookLink = bookLink.replace(x, "") 
            print(bookLink)
        else:
            break
    bookLink = bookLink.strip()
    book = bookName.title()
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    print('class in addNewBook:'+str(class_val))
    subject_id= MessageDetails.query.filter_by(description=subject).first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    bookExist = BookDetails.query.filter_by(board_id=board_id.board_id,book_name=bookName,class_val=class_val,subject_id=subject_id.msg_id).first()
    if bookExist==None:
        if bookLink:
            insertBook = BookDetails(board_id=board_id.board_id,book_name=book,class_val=class_val,subject_id=subject_id.msg_id,teacher_id=teacher_id.teacher_id,book_link=bookLink,last_modified_date=datetime.now())
        else:
            insertBook = BookDetails(board_id=board_id.board_id,book_name=book,class_val=class_val,subject_id=subject_id.msg_id,teacher_id=teacher_id.teacher_id,last_modified_date=datetime.now())
        db.session.add(insertBook)
        db.session.commit()
        book_id = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_name=book).first()
        insertInBCSB = BoardClassSubjectBooks(school_id=teacher_id.school_id,class_val=class_val,subject_id=subject_id.msg_id,
        book_id=book_id.book_id,is_archived='N',last_modified_date=datetime.now())
        db.session.add(insertInBCSB)
        db.session.commit()
    return ('New Book added successfully')

@syllabus_mod.route('/checkForChapter',methods=['GET','POST'])
def checkForChapter():
    print('inside checkForChapter')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    chapterNum = request.args.get('chapter_num')
    bookId = request.args.get('bookId')
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    for x in chapterNum: 
        if x in punctuations: 
            chapterNum = chapterNum.replace(x, "") 
            print(chapterNum)
            return "NA"
        else:
            break
    chapterName = request.args.get('chapter_name')
    for x in chapterName.lower(): 
        if x in punctuations: 
            chapterName = chapterName.replace(x, "") 
            print(chapterName)
            return "NA"
        else:
            break
    subject_id= MessageDetails.query.filter_by(description=subject).first()
    print('Book Id:'+str(bookId))
    book = BookDetails.query.filter_by(book_id=bookId).first()
    bookIds = BookDetails.query.filter_by(class_val=class_val,book_name=book.book_name,subject_id=subject_id.msg_id).all()
    print('class_val:'+str(class_val)+'subject:'+str(subject_id.msg_id)+'Book name:'+str(book.book_name))
    # bookIds = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_name=book.book_name).all()
    k = 0
    print(book.book_name)
    for book_id in bookIds:
        print(str(class_val)+' '+str(subject_id.msg_id)+' '+str(chapterNum)+' '+str(book_id.book_id))
        topic1 = "select chapter_name,topic_name from topic_detail td inner join topic_tracker tt on td.topic_id = tt.topic_id where td.class_val='"+str(class_val)+"' and td.subject_id='"+str(subject_id.msg_id)+"' and td.book_id='"+str(book_id.book_id)+"' and tt.is_archived='N' and td.chapter_num='"+str(chapterNum)+"' "
        topic1 = db.session.execute(text(topic1)).first()
        topic2 = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,chapter_name=chapterName,book_id=book_id.book_id).first()
        print('inside for')
        print(book_id.book_id)
        print(topic1)
        if topic1 or topic2:
            k = 1
    print(k)
    if k==1:
        return ""
    else:
        return "1"

@syllabus_mod.route('/addClassSection',methods=['POST'])
def addClassSection():
    print('inside addClassSection')
    sections=request.get_json()
    class_val = request.args.get('class_val')
    print('class values:'+str(class_val))
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    for section in sections:
        # class_section = class_section.split(':')
        # class_val = class_section[0]
        # section = class_section[1]
        checkClass = ClassSection.query.filter_by(class_val=str(class_val),section=section.upper(),school_id=teacher_id.school_id).first()
        if checkClass:
            return ""
    for section in sections:
        # print(section)
        # class_section = class_section.split(':')
        # class_val = class_section[0]
        # section = class_section[1]
        
        print('Class:'+str(class_val)+' Section:'+str(section))
        class_data=ClassSection(class_val=str(class_val),section=str(section).upper(),student_count=0,school_id=teacher_id.school_id,last_modified_date=datetime.now())
        db.session.add(class_data)
        db.session.commit()
    
    for section in sections:
        # class_section = class_section.split(':')
        # class_val = class_section[0]
        # section = class_section[1]
        class_id = ClassSection.query.filter_by(class_val=str(class_val),section=section.upper(),school_id=teacher_id.school_id).first()
        topic_tracker = TopicTracker.query.filter_by(class_sec_id=class_id.class_sec_id,school_id=teacher_id.school_id).first()
        if topic_tracker:
            print('data already present')
        else:
            print('insert data into topic tracker')
            insertRow = "insert into topic_tracker (subject_id, class_sec_id, is_covered, topic_id, school_id, reteach_count, last_modified_date) (select subject_id, '"+str(class_id.class_sec_id)+"', 'N', topic_id, '"+str(teacher_id.school_id)+"', 0,current_date from Topic_detail where class_val='"+str(class_val)+"')"
            db.session.execute(text(insertRow))
        db.session.commit()   

    return "success"

@syllabus_mod.route('/checkForBook',methods=['GET','POST'])
def checkForBook():
    book = request.args.get('book')
    book = book.title()
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    bookName = book.strip()
    for x in bookName.lower(): 
        if x in punctuations: 
            bookName = bookName.replace(x, "") 
            print(bookName)
        else:
            break
    if bookName==None or bookName=='':
        return "NA"
    subject_id = MessageDetails.query.filter_by(category='Subject',description=subject).first()
    checkBook = BookDetails.query.filter_by(book_name=bookName,class_val=class_val,subject_id=subject_id.msg_id).first()
    if checkBook:
        return (book)
    else:
        return ""

@syllabus_mod.route('/checkForSubject',methods=['GET','POST'])
def checkForSubject():
    subject = request.args.get('subject')
    subject = subject.title()
    print('inside check for subject:'+str(subject))
    class_val = request.args.get('class_val')
    board = request.args.get('board')
    checkSubject = MessageDetails.query.filter_by(category='Subject',description=subject).first()
    if checkSubject:
        return (subject)
    else:
        return ""

@syllabus_mod.route('/checkforClassSection',methods=['GET','POST'])
def checkforClassSection():
    sections=request.get_json()
    class_val = request.args.get('class_val')
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print('inside checkforClassSection')
    print(sections)
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    class_val = class_val.strip()
    print('before remove punc class:'+str(class_val))
    if class_val==None or class_val=='':
        print('if clas_val is none')
        return "NB"
    
    for x in class_val: 
        if x in punctuations: 
            class_val = class_val.replace(x, "") 
            print('after remove punc class:'+str(class_val))
            return "NA"
        else:
            break
    for section in sections:
        # class_section = class_section.split(':')
        # class_val = class_section[0]
        # section = class_section[1]
        punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
        section = section.strip()
        for x in section.lower(): 
            if x in punctuations: 
                section = section.replace(x, "") 
                print(section)
                return "NA"
            else:
                break
        if section==None or section=='':
            print('if section is none')
            return "NB"
        print('class_val:'+class_val)
        print('section:'+section.upper())
        checkClass = ClassSection.query.filter_by(class_val=str(class_val),section=section.upper(),school_id=teacher_id.school_id).first()
        if checkClass:
            return str(class_val)+':'+str(section.upper())
    return ""


@syllabus_mod.route('/addNewTopic',methods=['GET','POST'])
def addNewTopic():
    print('inside add new topic')
    topics=request.get_json()
    book_id = request.args.get('book_id')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    chapter = request.args.get('chapter')
    chapter_num = request.args.get('chapter_num')
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    subject_id = MessageDetails.query.filter_by(description = subject).first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    book = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_id=book_id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    bookId = "select distinct bd.book_id from book_details bd inner join topic_detail td on td.book_id = bd.book_id where td.subject_id = '"+str(subject_id.msg_id)+"' and td.class_val  = '"+str(class_val)+"' and chapter_num = '"+str(chapter_num)+"' and bd.book_name = '"+str(book.book_name)+"'"
    bookId = db.session.execute(text(bookId)).first()
    print(topics)
    print('Book ID:'+str(bookId.book_id))
    for topic in topics:
        print(topic)
        topic = topic.strip()
        for x in topic: 
            if x in punctuations: 
                topic = topic.replace(x, "") 
                print(topic)
            else:
                break
        topic = topic.strip()
        topic = topic.capitalize()
        if bookId:
            insertTopic = Topic(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=chapter_num,class_val=class_val,book_id=bookId.book_id,teacher_id=teacher_id.teacher_id)
        db.session.add(insertTopic)
        db.session.commit()
        if bookId:
            topic_id = Topic.query.filter_by(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=chapter_num,class_val=class_val,book_id=bookId.book_id).first()
        insertTopicTracker = TopicTracker(subject_id=subject_id.msg_id,class_sec_id=class_sec_id.class_sec_id,is_covered='N',topic_id=topic_id.topic_id,school_id=teacher_id.school_id,is_archived='N',last_modified_date=datetime.now())
        db.session.add(insertTopicTracker)
        db.session.commit()
    return ("Add new Topic")
  
@syllabus_mod.route('/addNewChapter',methods=['GET','POST'])
def addNewChapter():
    print('inside add new chapter')
    topics=request.get_json()
    book_id = request.args.get('book_id')
    print('book_id'+str(book_id))
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    chapter = request.args.get('chapter')
    chapter = chapter.strip()
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_|`=+~'''
    for x in chapter.lower(): 
        if x in punctuations: 
            chapter = chapter.replace(x, "") 
            print(chapter)
        else:
            break
    chapter = chapter.strip()
    chapter = chapter.capitalize() 
    chapter_num = request.args.get('chapter_num')
    chapter_num = chapter_num.strip()
    for x in chapter_num: 
        if x in punctuations: 
            chapter_num = chapter_num.replace(x, "") 
            print(chapter_num)
        else:
            break
    chapter_num = chapter_num.strip()
    subject_id = MessageDetails.query.filter_by(description = subject).first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    # bookId = "select distinct bd.book_id from book_details bd inner join topic_detail td on td.book_id = bd.book_id where td.subject_id = '"+str(subject_id.msg_id)+"' and td.class_val  = '"+str(class_val)+"' and chapter_num = '"+str(chapter_num)+"'"
    # bookId = db.session.execute(text(bookId)).first()
    print(topics)
    # print('Book ID:'+str(bookId))
    maxChapterNum = "select max(chapter_num) from topic_detail td"
    maxChapterNum = db.session.execute(text(maxChapterNum)).first()
    print('Max chapter no')
    print(maxChapterNum[0])
    maxChapterNum = int(maxChapterNum[0]) + 1
    for topic in topics:
        print(topic)
        topic = topic.strip()
        for x in topic: 
            if x in punctuations: 
                topic = topic.replace(x, "") 
                print(topic)
            else:
                break
        topic = topic.strip()
        topic = topic.capitalize()
        if chapter_num:
            insertTopic = Topic(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=chapter_num,class_val=class_val,book_id=book_id,teacher_id=teacher_id.teacher_id)
        else:
            insertTopic = Topic(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=maxChapterNum,class_val=class_val,book_id=book_id,teacher_id=teacher_id.teacher_id)
        db.session.add(insertTopic)
        db.session.commit()
        if chapter_num:
            topic_id = Topic.query.filter_by(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=chapter_num,class_val=class_val,book_id=book_id).first()
        else:
            topic_id = Topic.query.filter_by(topic_name=topic,chapter_name=chapter,subject_id=subject_id.msg_id,board_id=board_id.board_id,chapter_num=maxChapterNum,class_val=class_val,book_id=book_id).first()
        insertTopicTracker = TopicTracker(subject_id=subject_id.msg_id,class_sec_id=class_sec_id.class_sec_id,is_covered='N',topic_id=topic_id.topic_id,school_id=teacher_id.school_id,is_archived='N',last_modified_date=datetime.now())
        db.session.add(insertTopicTracker)
        db.session.commit()
    return ("Add new Chapter")


@syllabus_mod.route('/spellCheckBook',methods=['GET','POST'])
def spellCheckBook():
    print('inside spellCheckBox')
    bookText = request.args.get('bookText')
    return ""
    #if bookText=='':
    #    return ""
    #spell = SpellChecker()
    #correct = spell.correction(bookText)
    #print('correct word:'+str(correct))
    #if bookText==correct:
    #    return ""
    #else:
    #    print('inside if')
    #    print(bookText)
    #    print(correct)
    #    return correct

@syllabus_mod.route('/deleteSubject',methods=['GET','POST'])
def deleteSubject():
    subject_id = request.args.get('subjectId')
    class_val = request.args.get('class_val')
    board = request.args.get('board')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    deleteSubject = BoardClassSubject.query.filter_by(class_val=class_val,school_id=teacher_id.school_id,subject_id=subject_id,board_id=board).first()
    deleteSubject.is_archived = 'Y'
    db.session.commit()
    return ("delete subject successfully")

@syllabus_mod.route('/deleteBook',methods=['GET','POST'])
def deleteBook():
    subject = request.args.get('subject')
    class_val = request.args.get('class_val')
    bookId = request.args.get('bookId')
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    book = BookDetails.query.filter_by(book_id=bookId,subject_id=subject_id.msg_id,class_val= class_val).first()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id).all()
    print('book name:'+str(book.book_name))
    for book_id in bookIds:
        print(book_id.book_id)
        updateBook = BoardClassSubjectBooks.query.filter_by(book_id=book_id.book_id,school_id=teacher_id.school_id,class_val=class_val,subject_id=subject_id.msg_id).first()
        print(updateBook)
        updateBook.is_archived = 'Y'
        db.session.commit()
    return ("delete book successfully")

@syllabus_mod.route('/deleteTopics',methods=['GET','POST'])
def deleteTopics():
    subject = request.args.get('subject')
    class_val = request.args.get('class_val')
    bookId = request.args.get('bookId')
    chapter_num = request.args.get('chapter_num')
    topic_id = request.args.get('topic_id')
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    updateTT = "update topic_tracker set is_archived='Y' where school_id='"+str(teacher_id.school_id)+"' and subject_id='"+str(subject_id.msg_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and topic_id='"+str(topic_id)+"'"
    print(updateTT)
    updateTT = db.session.execute(text(updateTT))
    db.session.commit()
    return ("delete topic successfully")

@syllabus_mod.route('/deleteChapters',methods=['GET','POST'])
def deleteChapters():
    subject = request.args.get('subject')
    bookId = request.args.get('bookId')
    class_val = request.args.get('class_val')
    chapter_num = request.args.get('chapter_num')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    book  = BookDetails.query.filter_by(book_id=bookId,class_val=class_val,subject_id=subject_id.msg_id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id).all()
    book_id = Topic.query.filter_by(subject_id=subject_id.msg_id,class_val=class_val,chapter_num=chapter_num).first()
    # for book_id in bookIds:
    #     print('inside for of deleteChapters')
    print('subID:'+str(subject_id.msg_id)+' class_val:'+str(class_val)+' chapter num:'+str(chapter_num)+' bookName:'+str(book.book_name))
    topic_ids = "select topic_id from topic_detail td where td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id.msg_id)+"' and chapter_num = '"+str(chapter_num)+"' "
    topic_ids = topic_ids + "and td.book_id in (select book_id from book_details bd2 where book_name = '"+str(book.book_name)+"' and class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id.msg_id)+"')"
    topic_ids = db.session.execute(text(topic_ids)).fetchall()
    for topic_id in topic_ids:
        print('Topic id:'+str(topic_id.topic_id))
        # updateTT = TopicTracker.query.filter_by(school_id=teacher_id.school_id,subject_id=subject_id.msg_id,class_sec_id=class_sec_id.class_sec_id,topic_id=topic_id.topic_id).all()
        updateTT = "update topic_tracker set is_archived='Y' where school_id='"+str(teacher_id.school_id)+"' and subject_id='"+str(subject_id.msg_id)+"' and class_sec_id in (select class_sec_id from class_section where class_val='"+str(class_val)+"' and school_id='"+str(teacher_id.school_id)+"') and topic_id='"+str(topic_id.topic_id)+"'"
        print(updateTT)
        updateTT = db.session.execute(text(updateTT))
        db.session.commit()
    return ("delete chapter successfully")

@syllabus_mod.route('/generalSyllabusBooks')
def generalSyllabusBooks():
    subject_name=request.args.get('subject_name')
    class_val=request.args.get('class_val')
    board_id = request.args.get('board_id')
    subject_id = MessageDetails.query.filter_by(description=subject_name).first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    distinctBooks = "select distinct bd.book_name from book_details bd inner join topic_detail td on "
    distinctBooks = distinctBooks + "bd.book_id = td.book_id where bd.subject_id='"+str(subject_id.msg_id)+"' and td.class_val = '"+str(class_val)+"' order by bd.book_name"
    distinctBooks = db.session.execute(text(distinctBooks)).fetchall()
    bookArray=[]
    for val in distinctBooks:
        print(val.book_name)
        book_id = BookDetails.query.filter_by(book_name=val.book_name).first()
        bookArray.append(str(book_id.book_id)+':'+str(val.book_name))
    if bookArray:
        return jsonify([bookArray])  
    else:
        return ""

@syllabus_mod.route('/syllabusBooks')
@login_required
def syllabusBooks():
    subject_name=request.args.get('subject_name')
    class_val=request.args.get('class_val')
    board_id = request.args.get('board_id')
    subject_id = MessageDetails.query.filter_by(description=subject_name).first()
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    distinctBooks = "select distinct bd.book_name from book_details bd inner join board_class_subject_books bcsb on "
    distinctBooks = distinctBooks + "bd.book_id = bcsb.book_id where bcsb.school_id='"+str(teacher_id.school_id)+"' and bcsb.subject_id='"+str(subject_id.msg_id)+"' and bcsb.class_val = '"+str(class_val)+"' and bcsb.is_archived = 'N' order by bd.book_name"
    print(distinctBooks)
    distinctBooks = db.session.execute(text(distinctBooks)).fetchall()
    bookArray=[]
    for val in distinctBooks:
        book_id = BookDetails.query.filter_by(book_name=val.book_name,class_val=class_val).first()
        print(str(book_id.book_id)+':'+str(val.book_name))
        bookArray.append(str(book_id.book_id)+':'+str(val.book_name))
    if bookArray:
        return jsonify([bookArray])  
    else:
        return ""

@syllabus_mod.route('/fetchRemBooks',methods=['GET','POST'])
def fetchRemBooks():
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    
    distinctBooks = ''
    distinctBooks = "select distinct book_name from book_details bd where class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id.msg_id)+"' and "
    distinctBooks = distinctBooks + "book_name not in (select distinct book_name from book_details bd inner join board_class_subject_books bcsb on bd.book_id = bcsb.book_id "
    distinctBooks = distinctBooks + "where bd.class_val = '"+str(class_val)+"' and bd.subject_id = '"+str(subject_id.msg_id)+"' and bcsb.school_id = '"+str(teacher_id.school_id)+"')"
    distinctBooks = db.session.execute(text(distinctBooks)).fetchall()
    distinctBooksInBCSB = "select distinct bd.book_name from book_details bd inner join board_class_subject_books bcsb on "
    distinctBooksInBCSB = distinctBooksInBCSB + "bd.book_id = bcsb.book_id where bcsb.subject_id='"+str(subject_id.msg_id)+"' and bcsb.class_val = '"+str(class_val)+"' and bcsb.school_id='"+str(teacher_id.school_id)+"' and bcsb.is_archived = 'Y' order by bd.book_name"
    distinctBooksInBCSB = db.session.execute(text(distinctBooksInBCSB)).fetchall()
    bookArray=[]
    for val in distinctBooks:
        print(val.book_name)
        book_id = BookDetails.query.filter_by(book_name=val.book_name).first()
        bookArray.append(str(book_id.book_id)+':'+str(val.book_name))
    for value in distinctBooksInBCSB:
        book_id = BookDetails.query.filter_by(book_name=value.book_name).first()
        bookArray.append(str(book_id.book_id)+':'+str(value.book_name))
    if bookArray:
        return jsonify([bookArray])
    else:
        return "" 

@syllabus_mod.route('/selectedChapter',methods=['GET','POST'])
def selectedChapter():
    chapterNum = request.args.get('chapterNum')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    book_id = request.args.get('bookId')
    print('inside selected chapter')
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    book = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_id=book_id).first()
    # chapter = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,chapter_num=chapterNum,book_id=book_id).first()
    chapter = "select chapter_num,chapter_name from topic_detail td inner join book_details bd on td.book_id = bd.book_id where "
    chapter = chapter + "td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id.msg_id)+"' and chapter_num = '"+str(chapterNum)+"' and book_name  = '"+str(book.book_name)+"'"
    print(chapter)
    chapter = db.session.execute(text(chapter)).first()
    # chapter = "select chapter_name,chapter_num from topic_detail td inner join book_details bd on "
    # chapter = chapter + "td.book_id = bd.book_id where td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id.msg_id)+"' and chapter_num = '"+str(chapterNum)+"' and book_name ='"+str(book.book_name)+"'"
    # chapter = db.session.execute(text(chapter)).fetchall()
    selectedChapterArray = []
    # for chapt in chapter:
    selectedChapterArray.append(str(chapter.chapter_name)+':'+str(chapter.chapter_num))
    return jsonify([selectedChapterArray])


@syllabus_mod.route('/fetchRemChapters',methods=['GET','POST'])
def fetchRemChapters():
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    bookId = request.args.get('bookId')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val).first()
    book = BookDetails.query.filter_by(book_id=bookId).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id).all()
    
    chapterArray=[]
    print('Book:'+str(book.book_name)+' class:'+str(class_val)+' subId:'+str(subject_id.msg_id))
    
    queryChapters = "select distinct chapter_name,chapter_num from topic_detail td where td.subject_id = '"+str(subject_id.msg_id)+"' and td.class_val = '"+str(class_val)+"'  and book_id in (select book_id from book_details bd where book_name = '"+str(book.book_name)+"' and subject_id = '"+str(subject_id.msg_id)+"' and class_val = '"+str(class_val)+"') "
    queryChapters = queryChapters + "and td.topic_id not in (select td.topic_id from topic_detail td inner join topic_tracker tt on "
    queryChapters = queryChapters + "td.topic_id = tt.topic_id where td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id.msg_id)+"' and tt.school_id = '"+str(teacher_id.school_id)+"') order by chapter_num"
    print('print chapters from general')
    print(queryChapters)
    queryChapters = db.session.execute(text(queryChapters)).fetchall()
    
            # chapterArray.append(str(chapter.chapter_num)+":"+str(chapter.chapter_name))
    queryBookDetails = "select distinct chapter_name,chapter_num from topic_detail td inner join topic_tracker tt on "
    queryBookDetails = queryBookDetails + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id.msg_id)+"' and tt.school_id='"+str(teacher_id.school_id)+"' and td.class_val = '"+str(class_val)+"' and tt.is_archived = 'Y' and td.book_id in "
    queryBookDetails = queryBookDetails + "(select book_id from book_details bd where class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id.msg_id)+"' and book_name='"+str(book.book_name)+"') order by chapter_num"
    print('deleted chapters')
    print(queryBookDetails)
    queryBookDetails = db.session.execute(text(queryBookDetails)).fetchall()
    j=1
    for chapter in queryChapters:
        chapters = chapter.chapter_name
        chapters = chapters.replace("'","\'")
        num = chapter.chapter_num
        if len(queryChapters)>1:
            if j==1:
                chapters = chapters + "/"
                print(chapters)
            elif j==len(queryChapters):
                if len(queryBookDetails)>0:
                    num = "/"+str(num)
                    chapters = chapters+"/"
                else:
                    num = "/"+str(num)
                    print(chapters)
            else:
                num = "/"+str(num)
                chapters = chapters+"/"
                print(chapters)
            j=j+1
        else:
            if len(queryBookDetails)>0:
                chapters = chapters+"/"
        chapterArray.append(str(num)+":"+str(chapters))
    i=1
    for book in queryBookDetails:
        print('inside for queryBookDetails'+str(len(queryChapters)))
        chapter = book.chapter_name
        chapter = chapter.replace("'","\'")
        num = book.chapter_num
        if len(queryBookDetails)>1:
            if i==1:
                if len(queryChapters)>0:
                    print('if queryChapters is not null')
                    num = "/"+str(num)
                    chapter = chapter + "/"
                else:
                    chapter = chapter + "/"
                    print(chapter)
            elif i==len(queryBookDetails):
                num = "/"+str(num)
                print(chapter)
            else:
                num = "/"+str(num)
                chapter = chapter+"/"
                print(chapter)
            i=i+1
        else:
            if len(queryChapters)>0:
                num = "/"+str(num)
        print(chapter)
        chapterArray.append(str(num)+":"+str(chapter))
    for ch in chapterArray:
        print(ch)
    if chapterArray:
        return jsonify([chapterArray]) 
    else:
        return ""


@syllabus_mod.route('/fetchBooks',methods=['GET','POST'])
def fetchBooks():
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    distinctBooks = "select distinct bd.book_name from book_details bd inner join board_class_subject_books bcsb on "
    distinctBooks = distinctBooks + "bd.book_id = bcsb.book_id where bcsb.school_id='"+str(teacher_id.school_id)+"' and bcsb.subject_id='"+str(subject_id.msg_id)+"' and bcsb.class_val = '"+str(class_val)+"' and bcsb.is_archived = 'N' order by bd.book_name"
    print(distinctBooks)
    distinctBooks = db.session.execute(text(distinctBooks)).fetchall()
    bookArray=[]
    for val in distinctBooks:
        print(val.book_name)
        book_id = BookDetails.query.filter_by(book_name=val.book_name).first()
        bookArray.append(str(book_id.book_id)+':'+str(val.book_name))
    if bookArray:
        return jsonify([bookArray])
    else:
        return ""

@syllabus_mod.route('/generalSyllabusChapters')
def generalSyllabusChapters():
    book_id=request.args.get('book_id')
    class_val=request.args.get('class_val')
    board_id=request.args.get('board_id')
    subject_id=request.args.get('subject_id')
    print('Book id:'+str(book_id))
    class_sec_id = ClassSection.query.filter_by(class_val=class_val).first()
    book = BookDetails.query.filter_by(book_id=book_id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id,board_id=board_id).all()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    chapterArray=[]
    # print('Book:'+str(book.book_name)+' class:'+str(class_val)+' subId:'+str(subject_id)+' boardId:'+str(board_id))
    queryBookDetails = "select distinct chapter_name,chapter_num from topic_detail td where td.subject_id = '"+str(subject_id)+"' and td.class_val = '"+str(class_val)+"' and td.board_id='"+str(board_id)+"' and td.book_id in "
    queryBookDetails = queryBookDetails + "(select book_id from book_details bd where class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id)+"' and book_name='"+str(book.book_name)+"') order by chapter_num"
    print('inside general syllabus chapter:')
    print(queryBookDetails)
    queryBookDetails = db.session.execute(text(queryBookDetails)).fetchall()
    i=1
    for book in queryBookDetails:
        chapter = book.chapter_name
        chapter = chapter.replace("'","\'")
        num = book.chapter_num
        if len(queryBookDetails)>1:
            if i==1:
                chapter = chapter + "/"
                print(chapter)
            elif i==len(queryBookDetails):
                num = "/"+str(num)
                print(chapter)
            else:
                num = "/"+str(num)
                chapter = chapter+"/"
                print(chapter)
            i=i+1
        chapterArray.append(str(num)+":"+str(chapter))
    if chapterArray:
        return jsonify([chapterArray]) 
    else:
        return ""

@syllabus_mod.route('/syllabusChapters') 
@login_required
def syllabusChapters():
    book_id=request.args.get('book_id')
    class_val=request.args.get('class_val')
    board_id=request.args.get('board_id')
    subject_id=request.args.get('subject_id')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    book = BookDetails.query.filter_by(book_id=book_id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id,board_id=board_id).all()
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    chapterArray=[]
    print('Book:'+str(book.book_name)+' class:'+str(class_val)+' subId:'+str(subject_id)+' boardId:'+str(board_id))
    queryBookDetails = "select distinct chapter_name,chapter_num from topic_detail td inner join topic_tracker tt on "
    queryBookDetails = queryBookDetails + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id)+"' and tt.school_id='"+str(teacher_id.school_id)+"' and td.class_val = '"+str(class_val)+"' and tt.is_archived = 'N' and td.book_id in "
    queryBookDetails = queryBookDetails + "(select book_id from book_details bd where class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id)+"' and book_name='"+str(book.book_name)+"') order by chapter_num"
    # queryBookDetails = queryBookDetails + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id)+"' and tt.school_id='"+str(teacher_id.school_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' "
    # queryBookDetails = queryBookDetails + "order by chapter_num"
    print(queryBookDetails)
    queryBookDetails = db.session.execute(text(queryBookDetails)).fetchall()
    i=1
    for book in queryBookDetails:
        chapter = book.chapter_name
        chapter = chapter.replace("'","\'")
        num = book.chapter_num
        book = Topic.query.filter_by(chapter_name=book.chapter_name,chapter_num=book.chapter_num).first()
        bookId = book.book_id
        if len(queryBookDetails)>1:
            if i==1:
                bookId = str(bookId) + "/"
                print(chapter)
            elif i==len(queryBookDetails):
                num = "/"+str(num)
                print(chapter)
            else:
                num = "/"+str(num)
                bookId = str(bookId) + "/"
                print(chapter)
            i=i+1
        chapterArray.append(str(num)+":"+str(chapter)+';'+str(book.book_id))
    for chapters in chapterArray:
        print(chapters)
    if chapterArray:
        return jsonify([chapterArray]) 
    else:
        return ""

@syllabus_mod.route('/chapterTopic',methods=['GET','POST'])
def chapterTopic():
    print('inside chapterTopic')
    class_val = request.args.get('class_val')
    subject = request.args.get('subject')
    chapter_num = request.args.get('chapter_num')
    book_id = request.args.get('book_id')
    print('Book id:'+str(book_id))
    print('class value:'+str(class_val))
    try:
        subject_id = MessageDetails.query.filter_by(description=subject).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
        book = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_id=book_id).first()
        print('class:'+str(class_val)+' subject_id:'+str(subject_id.msg_id)+' book_id:'+str(book_id))
        remTopics = "select distinct topic_name ,topic_id from topic_detail td where class_val = '"+str(class_val)+"' and subject_id  = '"+str(subject_id.msg_id)+"' and chapter_num = '"+str(chapter_num)+"' and topic_id not in "
        remTopics = remTopics + "(select distinct td.topic_id from topic_detail td inner join topic_tracker tt on "
        remTopics = remTopics + "td.topic_id = tt.topic_id where td.class_val = '"+str(class_val)+"' and "
        remTopics = remTopics + "td.subject_id = '"+str(subject_id.msg_id)+"' and td.chapter_num = '"+str(chapter_num)+"' and tt.school_id = '"+str(teacher_id.school_id)+"') and book_id in (select book_id from book_details bd where book_name = '"+str(book.book_name)+"' and class_val='"+str(class_val)+"' and subject_id='"+str(subject_id.msg_id)+"') order by topic_id"
        print('inside Rem topics')
        print('Rem Topics:'+str(remTopics))
        remTopics = db.session.execute(text(remTopics)).fetchall()
        topics = "select distinct td.topic_id,td.topic_name from topic_detail td inner join topic_tracker tt on "
        topics = topics + "td.topic_id = tt.topic_id where td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id.msg_id)+"' and td.chapter_num = '"+str(chapter_num)+"' and tt.is_archived = 'Y' and tt.school_id = '"+str(teacher_id.school_id)+"' and td.book_id in (select book_id from book_details bd where book_name = '"+str(book.book_name)+"') order by td.topic_id"
        topics = db.session.execute(text(topics)).fetchall()
    except:
        return ""
    topicArray = []
    i=1
    for topic in topics:
        print('for topic list')
        print(topic.topic_name)
        print(len(remTopics))
        topic_name = topic.topic_name
        topic_name = topic_name.replace("'","\'")
        topic_id = topic.topic_id
        if len(topics)>1:
            if i==1:
                topic_name = topic_name + "/"
            elif i==len(topics):
                if len(remTopics)>0:
                    topic_id = "/"+str(topic_id)
                    topic_name = topic_name + "/"
                else:
                    topic_id = "/"+str(topic_id)
            else:
                topic_id = "/"+str(topic_id)
                topic_name = topic_name+"/"
            i=i+1
        else:
            if len(remTopics)>0:
                topic_name = topic_name+"/"
        topicArray.append(str(topic_id)+":"+str(topic_name))
        # topicArray.append(str(topic.topic_id)+':'+str(topic.topic_name))
    j=1
    for remTopic in remTopics:
        print('rem list')
        print(remTopic.topic_name)
        topic_name = remTopic.topic_name
        topic_name = remTopic.topic_name.replace("'","\'")
        topic_id = remTopic.topic_id
        if len(remTopics)>1:
            if j==1:
                if len(topics)>0:
                    topic_id = "/"+str(topic_id)
                    topic_name = topic_name + "/"
                else:
                    topic_name = topic_name + "/"
            elif j==len(remTopics):
                topic_id = "/"+str(topic_id)
            else:
                topic_id = "/"+str(topic_id)
                topic_name = topic_name+"/"
            j=j+1
        else:
            if len(topics)>0:
                topic_id = "/"+str(topic_id)
        topicArray.append(str(topic_id)+":"+str(topic_name))
        # topicArray.append(str(remTopic.topic_id)+':'+str(remTopic.topic_name))
    for top in topicArray:
        print(top)
    if topicArray:
        return jsonify([topicArray])
    else:
        return ""

@syllabus_mod.route('/fetchChapters',methods=['GET','POST'])
def fetchChapters():
    book_id=request.args.get('bookId')
    print('inside fetchChapters')
    print('Book Id:'+str(book_id))
    class_val=request.args.get('class_val')
    # board_id=request.args.get('board_id')
    subject=request.args.get('subject')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    book = BookDetails.query.filter_by(book_id=book_id).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id).all()
    
    chapterArray=[]
    print('Book:'+str(book.book_name)+' class:'+str(class_val)+' subId:'+str(subject_id.msg_id))
    queryBookDetails = "select distinct chapter_name,chapter_num from topic_detail td inner join topic_tracker tt on "
    queryBookDetails = queryBookDetails + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id.msg_id)+"' and tt.school_id='"+str(teacher_id.school_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' and td.book_id in "
    queryBookDetails = queryBookDetails + "(select book_id from book_details bd where class_val = '"+str(class_val)+"' and subject_id = '"+str(subject_id.msg_id)+"' and book_name='"+str(book.book_name)+"') order by chapter_num"
    # queryBookDetails = queryBookDetails + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id.msg_id)+"' and tt.school_id='"+str(teacher_id.school_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' "
    # queryBookDetails = queryBookDetails + "order by chapter_num"
    print(queryBookDetails)
    queryBookDetails = db.session.execute(text(queryBookDetails)).fetchall()
    i=1
    for book in queryBookDetails:
        chapter = book.chapter_name
        chapter = chapter.replace("'","\'")
        num = book.chapter_num
        book = Topic.query.filter_by(chapter_name=book.chapter_name,chapter_num=book.chapter_num).first()
        bookId = book.book_id
        if len(queryBookDetails)>1:
            if i==1:
                bookId = str(bookId) + "/"
                print(chapter)
            elif i==len(queryBookDetails):
                num = "/"+str(num)
                print(chapter)
            else:
                num = "/"+str(num)
                bookId = str(bookId) + "/"
                print(chapter)
            i=i+1
        chapterArray.append(str(num)+":"+str(chapter)+';'+str(book.book_id))
    if chapterArray:
        return jsonify([chapterArray]) 
    else:
        return ""

@syllabus_mod.route('/fetchTopics',methods=['GET','POST'])
def fetchTopics():
    subject=request.args.get('subject')
    chapter_num=request.args.get('chapter_num')
    
    class_val = request.args.get('class_val')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    subject_id = MessageDetails.query.filter_by(description=subject).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    bookId = request.args.get('bookId')
    # chapter_name = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,chapter_num=chapter_num).first()
    book = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,book_id=bookId).first()
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id.msg_id,board_id=board_id.board_id).all()
    # topicArray=[]
    # chapter_name = Topic.query.filter_by(class_val=class_val,subject_id=subject_id.msg_id,chapter_num=chapter_num).first()
    # queryTopics = "select distinct td.topic_id ,td.topic_name from topic_detail td inner join topic_tracker tt on "
    # queryTopics = queryTopics + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id.msg_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' and tt.school_id = '"+str(teacher_id.school_id)+"' and td.topic_id in "
    # queryTopics = queryTopics + "(select topic_id from topic_detail td where subject_id = '"+str(subject_id.msg_id)+"' and class_val = '"+str(class_val)+"' and chapter_name = '"+str(chapter_name.chapter_name)+"') order by td.topic_id"
    # queryTopics = db.session.execute(text(queryTopics)).fetchall()
    # for topic in queryTopics:
    #     topicArray.append(str(topic.topic_id)+":"+str(topic.topic_name))
    # if topicArray:
    #     return jsonify([topicArray]) 
    # else:
    #     return ""
    topicArray=[]
    chapter_name = "select chapter_name,td.book_id from topic_detail td inner join book_details bd on td.book_id = bd.book_id where "
    chapter_name = chapter_name + "td.subject_id = '"+str(subject_id.msg_id)+"' and td.class_val = '"+str(class_val)+"' and td.chapter_num = '"+str(chapter_num)+"' and bd.book_name = '"+str(book.book_name)+"'"
    chapter_name = db.session.execute(text(chapter_name)).first()
    chapterName = chapter_name.chapter_name.replace("'","''")
    queryTopics = "select distinct td.topic_id ,td.topic_name from topic_detail td inner join topic_tracker tt on "
    queryTopics = queryTopics + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id.msg_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' and tt.school_id = '"+str(teacher_id.school_id)+"' and td.topic_id in "
    queryTopics = queryTopics + "(select topic_id from topic_detail td where subject_id = '"+str(subject_id.msg_id)+"' and class_val = '"+str(class_val)+"' and chapter_name = '"+str(chapterName)+"') order by td.topic_id"
    print('fetch Topic Query:'+str(queryTopics))
    queryTopics = db.session.execute(text(queryTopics)).fetchall()
    i=1
    for topic in queryTopics:
        topic_name = topic.topic_name
        topic_name = topic_name.replace("'","\'")
        topic_id = topic.topic_id
        if len(queryTopics)>1:
            if i==1:
                topic_name = topic_name + "/"
                print(topic_name)
            elif i==len(queryTopics):
                topic_id = "/"+str(topic_id)
            else:
                topic_id = "/"+str(topic_id)
                topic_name = topic_name+"/"
                print(topic_name)
            i=i+1
        topicArray.append(str(topic_id)+":"+str(topic_name))
        # topicArray.append(str(topic.topic_id)+":"+str(topic.topic_name))
    if topicArray:
        return jsonify([topicArray]) 
    else:
        return ""

@syllabus_mod.route('/generalSyllabusTopics',methods=['GET','POST'])
def generalSyllabusTopics():
    subject_id=request.args.get('subject_id')
    board_id=request.args.get('board_id')
    chapter_num=request.args.get('chapter_num')
    bookId = request.args.get('selectedBookId')
    class_val = request.args.get('class_val')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val).first()
    
    print('BookID:'+str(bookId))
    book = BookDetails.query.filter_by(book_id=bookId).first()
    print('book name:')
    print(book.book_name)
    bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id,board_id=board_id).all()
    topicArray=[]
    chapter_name = "select chapter_name,td.book_id from topic_detail td inner join book_details bd on td.book_id = bd.book_id where "
    chapter_name = chapter_name + "td.subject_id = '"+str(subject_id)+"' and td.class_val = '"+str(class_val)+"' and td.chapter_num = '"+str(chapter_num)+"' and bd.book_name = '"+str(book.book_name)+"'"
    chapter_name = db.session.execute(text(chapter_name)).first()
    # queryTopics = "select distinct td.topic_id ,td.topic_name from topic_detail td inner join topic_tracker tt on "
    # queryTopics = queryTopics + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and td.topic_id in "
    # queryTopics = queryTopics + "(select topic_id from topic_detail td where subject_id = '"+str(subject_id)+"' and class_val = '"+str(class_val)+"' and chapter_name = '"+str(chapter_name.chapter_name)+"') order by td.topic_id"
    chapterName = chapter_name.chapter_name.replace("'","''")
    queryTopics = "select distinct topic_id, topic_name from topic_detail td where class_val = '"+str(class_val)+"' and board_id = '"+str(board_id)+"' and subject_id = '"+str(subject_id)+"' and chapter_name ='"+str(chapterName)+"' order by topic_id"
    print('inside generalsyllabustopics')
    print(queryTopics)
    queryTopics = db.session.execute(text(queryTopics)).fetchall()
    i=1
    for topic in queryTopics:
        topic_name = topic.topic_name
        topic_name = topic_name.replace("'","\'")
        topic_id = topic.topic_id
        if len(queryTopics)>1:
            if i==1:
                topic_name = topic_name + "/"
                print(topic_name)
            elif i==len(queryTopics):
                topic_id = "/"+str(topic_id)
            else:
                topic_id = "/"+str(topic_id)
                topic_name = topic_name+"/"
                print(topic_name)
            i=i+1
        topicArray.append(str(topic_id)+":"+str(topic_name))
    if topicArray:
        return jsonify([topicArray]) 
    else:
        return ""

@syllabus_mod.route('/syllabusTopics')
@login_required
def syllabusTopics():
    subject_id=request.args.get('subject_id')
    board_id=request.args.get('board_id')
    chapter_num=request.args.get('chapter_num')
    bookId = request.args.get('selectedBookId')
    class_val = request.args.get('class_val')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,school_id=teacher_id.school_id).first()
    print('BookID:'+str(bookId))
    book = BookDetails.query.filter_by(class_val=class_val,subject_id=subject_id,book_id=bookId).first()
    # bookIds = BookDetails.query.filter_by(book_name=book.book_name,class_val=class_val,subject_id=subject_id,board_id=board_id).all()
    topicArray=[]
    chapter_name = "select chapter_name,td.book_id from topic_detail td inner join book_details bd on td.book_id = bd.book_id where "
    chapter_name = chapter_name + "td.subject_id = '"+str(subject_id)+"' and td.class_val = '"+str(class_val)+"' and td.chapter_num = '"+str(chapter_num)+"' and bd.book_name = '"+str(book.book_name)+"'"
    chapter_name = db.session.execute(text(chapter_name)).first()
    chapterName = chapter_name.chapter_name.replace("'","''")
    queryTopics = "select distinct td.topic_id ,td.topic_name from topic_detail td inner join topic_tracker tt on "
    queryTopics = queryTopics + "td.topic_id = tt.topic_id where tt.subject_id = '"+str(subject_id)+"' and tt.class_sec_id = '"+str(class_sec_id.class_sec_id)+"' and tt.is_archived = 'N' and tt.school_id = '"+str(teacher_id.school_id)+"' and td.topic_id in "
    queryTopics = queryTopics + "(select topic_id from topic_detail td where subject_id = '"+str(subject_id)+"' and class_val = '"+str(class_val)+"' and chapter_name = '"+str(chapterName)+"') order by td.topic_id"
    print(queryTopics)
    queryTopics = db.session.execute(text(queryTopics)).fetchall()
    i=1
    print(len(queryTopics))
    for topic in queryTopics:
        topic_name = topic.topic_name
        topic_name = topic_name.replace("'","\'")
        topic_id = topic.topic_id
        if len(queryTopics)>1:
            if i==1:
                topic_name = topic_name + "/"
                print(topic_name)
            elif i==len(queryTopics):
                topic_id = "/"+str(topic_id)
            else:
                topic_id = "/"+str(topic_id)
                topic_name = topic_name+"/"
                print(topic_name)
            i=i+1
        topicArray.append(str(topic_id)+":"+str(topic_name))
    if topicArray:
        return jsonify([topicArray]) 
    else:
        return ""

@syllabus_mod.route('/syllabusQuestionsDetails',methods=['GET','POST'])
def syllabusQuestionsDetails():
    class_val = request.args.get('class_val')
    subject_id = request.args.get('subject_id')
    topic_id = request.args.get('topic_id')
    chapter_num=request.args.get('chapter_num')
    print('inside syllabusQuestionsDetails')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
    boardName = MessageDetails.query.filter_by(msg_id=board.board_id).first()
    # questions = QuestionDetails.query.filter_by(subject_id=subject_id,class_val=class_val,topic_id=topic_id).all()
    topic_name = Topic.query.filter_by(topic_id=topic_id,subject_id=subject_id,class_val=class_val).first()
    chapter_name = Topic.query.filter_by(subject_id=subject_id,class_val=class_val,chapter_num=chapter_num).first()
    subQuestion = "select count(*) from question_details qd where subject_id = '"+str(subject_id)+"' and class_val = '"+str(class_val)+"' and topic_id = '"+str(topic_id)+"' and archive_status = 'N' and question_type = 'Subjective'"
    subQuestion = db.session.execute(text(subQuestion)).first()
    objQuestion = "select count(*) from question_details qd where subject_id = '"+str(subject_id)+"' and class_val = '"+str(class_val)+"' and topic_id = '"+str(topic_id)+"' and archive_status = 'N' and question_type = 'MCQ1'"
    objQuestion = db.session.execute(text(objQuestion)).first()
    refContent = "select count(*) from content_detail cd where class_val = '"+str(class_val)+"' and archive_status = 'N' and subject_id = '"+str(subject_id)+"' and topic_id = '"+str(topic_id)+"'"
    refContent = db.session.execute(text(refContent)).first()
    questionDetailsArray = []
    print('subQuestion:'+str(subQuestion[0])+' objQuestion:'+str(objQuestion[0])+' refContent:'+str(refContent[0]))
    # for question in questions:
    #     questionArray.append(question.question_description)
    questionDetailsArray.append(str(topic_name.topic_name)+':'+str(subQuestion[0])+':'+str(objQuestion[0])+':'+str(refContent[0])+':'+str(boardName.description)+':'+str(chapter_name.chapter_name))
    if questionDetailsArray:
        return jsonify([questionDetailsArray])
    else:
        return ""
