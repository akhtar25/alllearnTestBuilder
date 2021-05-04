from flask import current_app as app
from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, session,jsonify
from applicationDB import *
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime
from flask import g, jsonify
from sqlalchemy import func, distinct, text, update

course = Blueprint('course',__name__)

@course.route('/addCourse')                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
def addCourse():
    course_id = request.args.get('course_id')
    if course_id=='':
        courId = CourseDetail(course_name='Untitled Course',course_status=275,is_archived='N',last_modified_date=datetime.now())
        db.session.add(courId)
        db.session.commit()
        course_id = courId.course_id
    return redirect(url_for('editCourse',course_id=course_id))

@course.route('/editCourse')
def editCourse():
    print('inside editCourse')
    course_category = MessageDetails.query.filter_by(category='Course Category').first()
    desc = course_category.description.split(',')
    course_id=request.args.get('course_id')
    teacherIdExist = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print('userID:'+str(current_user.id))
    print('Teacher:'+str(teacherIdExist))
    reviewStatus = "select *from teacher_profile where user_id='"+str(current_user.id)+"'"
    reviewStatus = db.session.execute(text(reviewStatus)).first()
    if reviewStatus:
        print('REview status:'+str(reviewStatus.review_status))
        if reviewStatus.review_status==273:
            print('review status Inreview')
            return redirect(url_for('teacherRegistration'))
    if teacherIdExist==None:
        return redirect(url_for('teacherRegistration'))
    else:
        print('Description:'+str(desc))
        print('course_id:'+str(course_id))
        if course_id:
            courseDet = CourseDetail.query.filter_by(course_id=course_id).first()
            levelId = MessageDetails.query.filter_by(category='Difficulty Level',msg_id=courseDet.difficulty_level).first()
            courseNotes = TopicNotes.query.filter_by(course_id=course_id).first()
            # topicDet = "select count(*) as no_of_questions,td.topic_name,td.topic_id,ct.course_id from course_topics ct "
            # topicDet = topicDet + "inner join topic_detail td on ct.topic_id=td.topic_id "
            # topicDet = topicDet + "left join test_questions tq on ct.test_id = tq.test_id "
            # topicDet = topicDet + "where ct.course_id = '"+str(course_id)+"' and tq.is_archived='N' and ct.is_archived='N' group by td.topic_name,td.topic_id,ct.course_id "
            
            topicL = []
            topicsID = CourseTopics.query.filter_by(course_id=course_id,is_archived='N').all()
            for topicId in topicsID:
                topicList = []
                topic_name = Topic.query.filter_by(topic_id=topicId.topic_id).first()
                quesNo = TestQuestions.query.filter_by(test_id=topicId.test_id,is_archived='N').all()
                questionNo = len(quesNo)
                topicList.append(topic_name.topic_name)
                topicList.append(questionNo)
                topicList.append(topicId.topic_id)
                notes = TopicNotes.query.filter_by(topic_id=topicId.topic_id,is_archived='N').first()
                recording = "select *from course_topics where course_id='"+str(course_id)+"' and topic_id='"+str(topicId.topic_id)+"' and video_class_url<>'' order by topic_id asc"
                recording = db.session.execute(text(recording)).first()
                checkNotes = ''
                checkRec = ''
                if notes:
                    checkNotes = notes.notes_name
                if recording:
                    checkRec = recording.video_class_url
                topicList.append(checkNotes)
                topicList.append(checkRec)
                print(topicList)
                topicL.append(topicList)
            print(topicL)
            for topic in topicL:
                print(topic[0])
                print(topic[1])
                print(topic[2])
            # topicDet = db.session.execute(text(topicDet)).fetchall()
            idealFor = ''
            if courseDet:
                idealFor = courseDet.ideal_for
            levelId = ''
            if levelId:
                levelId = levelId.description
            print('Description:'+str(courseDet.description))
            status = 1
            return render_template('editCourse.html',status=status,levelId=levelId,idealFor=idealFor,desc=desc,courseDet=courseDet,course_id=course_id,topicDet=topicL)
        else:
            levelId = ''
            return render_template('editCourse.html',levelId=levelId,desc=desc,course_id=course_id)
    


#clip = (VideoFileClip("frozen_trailer.mp4")
#        .subclip((1,22.65),(1,23.2))
#        .resize(0.3))
#clip.write_gif("use_your_head.gif")



@course.route('/searchTopic',methods=['GET','POST'])
def searchTopic():
    topic = request.args.get('topic')
    courseId = request.args.get('courseId')
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    coursesId = CourseDetail.query.filter_by(teacher_id=teacher_id.teacher_id).all()
    topicArray = []
    for course_id in coursesId:
        if str(course_id.course_id)!=str(courseId):
            TopicIds = "select td.topic_id,td.topic_name from topic_detail td inner join course_topics ct on td.topic_id = ct.topic_id where td.topic_name like '"+str(topic)+"%'  and ct.course_id ='"+str(course_id.course_id)+"' and ct.is_archived='N'"
            TopicIds = db.session.execute(text(TopicIds)).fetchall()
            for top in TopicIds:
                print('Topic:'+str(top))
                topicArray.append(str(top.topic_id)+':'+str(top.topic_name)+':'+str(course_id.course_id))
    if topicArray:
        return jsonify([topicArray])
    else:
        return ""

@course.route('/fetchQues',methods=['GET','POST'])
def fetchQues():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacherData.school_id).first()
    print('inside fetchQues')
    courseId = request.args.get('courseId')
    print('courseId:'+str(courseId))
    topics = CourseTopics.query.filter_by(course_id=courseId,is_archived='N').order_by(CourseTopics.topic_id.desc()).all()
    topicsDet = []
    for topic in topics:
        topicName = Topic.query.filter_by(topic_id=topic.topic_id).first()
        quesIds = TestQuestions.query.filter_by(test_id=topic.test_id,is_archived='N').all()
        quesNo = len(quesIds)
        notes = TopicNotes.query.filter_by(topic_id=topic.topic_id,is_archived='N').first()
        checkNotes = ''
        checkRec = ''
        if notes:
            checkNotes = notes.notes_name
        recording = "select *from course_topics where course_id='"+str(courseId)+"' and topic_id='"+str(topic.topic_id)+"' and video_class_url<>'' order by topic_id"
        recording = db.session.execute(text(recording)).first()
        if recording:
            checkRec = recording.video_class_url
        topic = topicName.topic_name.replace(",","/")
        topicsDet.append(str(topic)+':'+str(quesNo)+':'+str(topicName.topic_id)+':'+str(checkNotes)+':'+str(checkRec))
    if topicsDet:
        return jsonify(topicsDet)
    else:
        return ""

@course.route('/fetchRecording',methods=['GET','POST'])
def fetchRecording():
    print('inside fetchRecording')
    topic_id = request.args.get('topic_id')
    courseId = request.args.get('courseId')
    record = CourseTopics.query.filter_by(course_id=courseId,topic_id=topic_id).first()
    return jsonify(record.video_class_url)

@course.route('/deleteNotes',methods=['GET','POST'])
def deleteNotes():
    notes_id = request.args.get('notes_id')
    notes = TopicNotes.query.filter_by(tn_id=notes_id).first()
    notes.is_archived = 'Y'
    db.session.commit()
    return jsonify(notes.topic_id)


@course.route('/fetchNotes',methods=['GET','POST'])
def fetchNotes():
    print('inside fetchNotes')
    topic_id = request.args.get('topic_id')
    notes = TopicNotes.query.filter_by(topic_id=topic_id,is_archived='N').all()
    notesData = []
    for note in notes:
        NewNotes = note.notes_name.replace(",","/")
        notesData.append(str(NewNotes)+'!'+str(note.notes_url)+'!'+str(note.tn_id))
    print(notesData)
    if notesData:
        return jsonify(notesData)
    else:
        return ""

@course.route('/fetchRemQues',methods=['GET','POST'])
def fetchRemQues():
    quesIdList = request.get_json()
    quesArray = []
    for qId in quesIdList:
        print('Question Id:'+str(qId))
        quesObj = {}    
        quesName = QuestionDetails.query.filter_by(question_id=qId).first()
        quesObj['quesName'] = quesName.question_description
        print('Ques:'+str(quesName.question_description))
        quesOptions = QuestionOptions.query.filter_by(question_id=qId).all()
        i=0
        opt1=''
        opt2=''
        opt3=''
        opt4=''
        for option in quesOptions:
            if i==0:
                opt1 = option.option_desc
            elif i==1:
                opt2 = option.option_desc
            elif i==2:
                opt3 = option.option_desc
            else:
                opt4 = option.option_desc
            i=i+1
            print('quesOptions:'+str(option.option_desc))
        quesArray.append(str(quesName.question_description)+':'+str(opt1)+':'+str(opt2)+':'+str(opt3)+':'+str(opt4)+':'+str(qId))
    print('quesArray:')
    print(quesArray)
    if quesArray:
        return jsonify(quesArray)
    else:
        return ""

@course.route('/topicName',methods=['GET','POST'])
def topicName():
    print('inside topicName')
    topicId = request.args.get('topic_id')
    topicName = Topic.query.filter_by(topic_id=topicId).first()
    topic_name = topicName.topic_name
    print('topic name:'+topic_name)

    return jsonify(topic_name)

@course.route('/fetchTopicQues',methods=['GET','POST'])
def fetchTopicsQues():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacherData.school_id).first()
    print('inside fetchTopics')
    topic_id = request.args.get('topic_id')
    courseId = request.args.get('courseId')
    print('topic_id:'+str(topic_id))
    topics = CourseTopics.query.filter_by(topic_id=topic_id,is_archived='N').first()
    topicName = Topic.query.filter_by(topic_id=topics.topic_id).first()
    print('Topic name:'+str(topicName.topic_name))
    quesIds = TestQuestions.query.filter_by(test_id=topics.test_id,is_archived='N').all()
    # topicNotes = TopicNotes.query.filter_by(topic_id=topics.topic_id).first()
    # NotesName = topicNotes.notes_name
    # NotesUrl = topicNotes.notes_url
    quesArray = []
    NewTopicName = ''
    if len(quesIds)==0:
        NewTopicName = topicName.topic_name.replace(",","/")
        quesArray.append(str('')+':'+str(NewTopicName)+':'+str('')+':'+str('')+':'+str('')+':'+str('')+':'+str('')+':'+str(topicName.topic_id))
    for qId in quesIds:
        quesObj = {}    
        quesName = QuestionDetails.query.filter_by(question_id=qId.question_id).first()
        quesObj['quesName'] = quesName.question_description
        quesObj['topic_name'] = topicName.topic_name
        print('Ques:'+str(quesName.question_description))
        print('topicName:'+str(topicName.topic_name))
        quesOptions = QuestionOptions.query.filter_by(question_id=qId.question_id).all()
        i=0
        opt1=''
        opt2=''
        opt3=''
        opt4=''
        for option in quesOptions:
            if i==0:
                opt1 = option.option_desc
            elif i==1:
                opt2 = option.option_desc
            elif i==2:
                opt3 = option.option_desc
            else:
                opt4 = option.option_desc
            i=i+1
            print('quesOptions:'+str(option.option_desc))
        NewTopicName = topicName.topic_name.replace(",","/")
        quesArray.append(str(quesName.question_description)+':'+str(NewTopicName)+':'+str(opt1)+':'+str(opt2)+':'+str(opt3)+':'+str(opt4)+':'+str(qId.question_id)+':'+str(topicName.topic_id))
    print('quesArray:')
    print(quesArray)
    if quesArray:
        return jsonify(quesArray)
    else:
        return ""

@course.route('/deleteTopic',methods=['GET','POST'])
def deleteTopic():
    print('inside deleteTopic')
    topicId = request.args.get('topicId')
    print('Topic id:'+str(topicId))
    course_id = request.args.get('course_id')
    courseTopic = CourseTopics.query.filter_by(topic_id=topicId,course_id=course_id,is_archived='N').first()
    courseTopic.is_archived = 'Y'
    db.session.commit()
    notes = "update topic_notes set is_archived='Y' where topic_id='"+str(topicId)+"' and is_archived='N'"
    notes = db.session.execute(text(notes))
    db.session.commit()
    return jsonify("1")

@course.route('/updateCourseTopic',methods=['GET','POST'])
def updateCourseTopic():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacherData.school_id).first()
    print('inside updateCourseTopic')
    topicId = request.args.get('topicId')
    courseId = request.args.get('courseId')
    topicName = request.args.get('topicName')
    print('Topic Id:'+str(topicId))
    print('courseId:'+str(courseId))
    quesIds = request.get_json()
    print(quesIds)
    topicDet = Topic.query.filter_by(topic_id=topicId).first()
    topicDet.topic_name = topicName
    db.session.commit()
    testId = CourseTopics.query.filter_by(course_id=courseId,topic_id=topicId).first()
    # totalQId = TestQuestions.query.filter_by(test_id=testId.test_id).all()
    deleteAll = "update test_questions set is_archived='Y' where test_id='"+str(testId.test_id)+"' "
    deleteAll = db.session.execute(text(deleteAll))
    # print('Total Question Ids:'+str(totalQId))
    print('Total not deleted Ques Ids:'+str(quesIds))
    print(quesIds)
    print('Length of Ques Ids:'+str(len(quesIds)))
    total_marks = 10*int(len(quesIds))
    print('Total marks:'+str(total_marks))
    testDet = TestDetails.query.filter_by(test_id=testId.test_id).first()
    # db.session.add(testDet)
    testDet.total_marks = total_marks
    db.session.commit()
        # testId = "select max(test_id) as test_id from test_details"
        # testId = db.session.execute(text(testId)).first()
    # courseTopic = ''
    # if courseId:
    #     courseTopic = CourseTopics(course_id=courseId,topic_id=topicDet.topic_id,test_id=testDet.test_id,is_archived='N',last_modified_date=datetime.now())
    #     db.session.add(courseTopic)
    # else:
    #     courseTopic = CourseTopics(topic_id=topicDet.topic_id,test_id=testDet.test_id,is_archived='N',last_modified_date=datetime.now())
    #     db.session.add(courseTopic)
    # db.session.commit()
    if len(quesIds)!=0:
        for quesId in quesIds:
            print('QuesID:'+str(quesId))
            if quesId!='[' or quesId!=']':
                testQues = TestQuestions(test_id=testDet.test_id,question_id=quesId,is_archived='N',last_modified_date=datetime.now())
                db.session.add(testQues)
                db.session.commit()
            # quesDet = QuestionDetails.query.filter_by(question_id=quesId).first()
            # quesDet.topic_id=topicDet.topic_id
            
    
    return jsonify("1")



@course.route('/addCourseTopic',methods=['GET','POST'])
def addCourseTopic():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacherData.school_id).first()
    print('inside addCourseTopic')
    topicName = request.args.get('topicName')
    courseId = request.args.get('courseId')
    topicId = request.args.get('topicId')
    courId = request.args.get('courId')
    print('My course ID:'+str(courseId))
    print('selected topic id:'+str(topicId))
    print('courseId of selected topic:'+str(courId))
    
    

    if courId:
        quesIds = request.get_json()
        total_marks = 10*len(quesIds)
        print('Total marks:'+str(total_marks))
        testDet = TestDetails(board_id=board.board_id,school_id=teacherData.school_id,test_type='Practice Test',total_marks=total_marks,teacher_id=teacherData.teacher_id,date_of_creation=datetime.now(),last_modified_date=datetime.now())
        db.session.add(testDet)
        db.session.commit()
        testId = "select max(test_id) as test_id from test_details"
        testId = db.session.execute(text(testId)).first()

        if courId:
            myTestId = CourseTopics.query.filter_by(course_id=courseId,topic_id=topicId,is_archived='N').first()
            testID = CourseTopics.query.filter_by(course_id=courId,topic_id=topicId).first()
            questionIds = TestQuestions.query.filter_by(test_id=testID.test_id).all()
            print(questionIds)
            for q in questionIds:
                print('Question ID:'+str(q.question_id))
                print('test id in which question stored:'+str(testId.test_id))
                Questions = TestQuestions(test_id=testId.test_id,question_id=q.question_id,is_archived='N',last_modified_date=datetime.now())
                db.session.add(Questions)
                db.session.commit()
        courseTopic = ''
        if courseId:
            courseTopic = CourseTopics(course_id=courseId,topic_id=topicId,test_id=testId.test_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(courseTopic)
        else:
            courseTopic = CourseTopics(topic_id=topicId,test_id=testId.test_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(courseTopic)
        db.session.commit()
        for quesId in quesIds:
            print('QuesID:'+str(quesId))
            testQues = TestQuestions(test_id=testId.test_id,question_id=quesId,is_archived='N',last_modified_date=datetime.now())
            db.session.add(testQues)
        
            quesDet = QuestionDetails.query.filter_by(question_id=quesId).first()
            quesDet.topic_id=topicId
            db.session.commit()
        return jsonify(topicId)
    else:
        print('Topic name:'+str(topicName))
        print('courseId:'+str(courseId))
        quesIds = request.get_json()
        print(quesIds)
        # courseId = CourseDetail.query.filter_by(course_name=courseName,teacher_id=teacherData.teacher_id,school_id=teacherData.school_id).first()
        
        # for quesId in quesIds:
        #     print(quesId)
        topicDet = Topic(topic_name=topicName,chapter_name=topicName,board_id=board.board_id,teacher_id=teacherData.teacher_id)
        db.session.add(topicDet)
        db.session.commit()
        # topicId = "select max(topic_id) as topic_id from topic_detail"
        # topicId = db.session.execute(text(topicId)).first()
        
        topicTr = TopicTracker(school_id=teacherData.school_id,topic_id=topicDet.topic_id,is_covered='N',reteach_count=0,is_archived='N',last_modified_date=datetime.now())
        db.session.add(topicTr)
        db.session.commit()
        total_marks = 10*len(quesIds)
        print('Total marks:'+str(total_marks))
        testDet = TestDetails(board_id=board.board_id,school_id=teacherData.school_id,test_type='Practice Test',total_marks=total_marks,teacher_id=teacherData.teacher_id,date_of_creation=datetime.now(),last_modified_date=datetime.now())
        db.session.add(testDet)
        db.session.commit()
        # testId = "select max(test_id) as test_id from test_details"
        # testId = db.session.execute(text(testId)).first()
        courseTopic = ''
        if courseId:
            courseTopic = CourseTopics(course_id=courseId,topic_id=topicDet.topic_id,test_id=testDet.test_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(courseTopic)
        else:
            courseTopic = CourseTopics(topic_id=topicDet.topic_id,test_id=testDet.test_id,is_archived='N',last_modified_date=datetime.now())
            db.session.add(courseTopic)
        db.session.commit()
        if quesIds:
            for quesId in quesIds:
                testQues = TestQuestions(test_id=testDet.test_id,question_id=quesId,is_archived='N',last_modified_date=datetime.now())
                db.session.add(testQues)
                
                quesDet = QuestionDetails.query.filter_by(question_id=quesId).first()
                quesDet.topic_id=topicDet.topic_id
                db.session.commit()
        return jsonify(topicDet.topic_id)
    
@course.route('/fetchTickCorrect',methods=['GET','POST'])
def fetchTickCorrect():
    print('inside fetchTickCorrect')
    correctOpt = []
    topic_id = request.args.get('topic_id')
    print('TopicId:'+str(topic_id))
    # quesIdsList = TestQuestions.query.filter_by(topic_id=topic_id).all()
    quesList  = request.get_json()
    print('Question List:')
    print(quesList)
    for quesId in quesList:
        print('Question Id:'+str(quesId))
        corr = QuestionOptions.query.filter_by(question_id=quesId,is_correct='Y').first()
        correctOpt.append(str(corr.option_desc)+':'+str(quesId))
    return jsonify(correctOpt)

@course.route('/addRecording',methods=['GET','POST'])
def addRecording():
    topic_id = request.args.get('topic_id')
    course_id = request.args.get('course_id')
    videoRec = CourseTopics.query.filter_by(topic_id=topic_id,course_id=course_id).first()
    recordingURL = request.form.get('recordingURL')
    print('recording Url:'+str(recordingURL))
    videoRecordUrl = request.form.get('videoRecordUrl')
    print('video url:'+str(videoRecordUrl))
    
    print('video recording url:'+str(videoRecordUrl))
    if recordingURL:
        videoRec.video_class_url = recordingURL
    else:
        videoRec.video_class_url = videoRecordUrl
    db.session.commit()
    return jsonify("1")

@course.route('/updateNotes',methods=['GET','POST'])
def updateNotes():
    topicId = request.args.get('topic_id')
    notesName = request.form.getlist('notesName')
    notesURL = request.form.getlist('notesURL')
    videoNotesUrl = request.form.getlist('videoNotesUrl')
    print('topicId:'+str(topicId))
    # print('Notes name:'+str(notesName))  
    existNotes = "update topic_notes set is_archived='Y' where topic_id='"+str(topicId)+"' "
    existNotes = db.session.execute(text(existNotes))
    print('Length of notes url array:'+str(len(notesURL)))
    for i in range(len(notesName)):
        print('inside for loop:'+str(i))
        print('NotesName:'+str(notesName[i]))
        print('notesUrl:'+str(notesURL[i]))
        print('videoNotesUrl:'+str(videoNotesUrl[i]))
        print('index:'+str(i))
        if i!=0:
            if notesURL[i]:
                print('url not null')
                if notesName[i]:
                    print('notes name not null')
                    if notesURL[i]:
                        courseId = CourseTopics.query.filter_by(topic_id=topicId).first()
                        addNotes = TopicNotes(topic_id=topicId,course_id=courseId.course_id,notes_name=notesName[i],notes_url=notesURL[i],notes_type=226,is_archived='N',last_modified_date=datetime.now())
                        db.session.add(addNotes)
                        db.session.commit()
                    else:
                        return ""
                else:
                    return ""
            else:
                if notesName[i]: 
                    if videoNotesUrl[i]:
                        courseId = CourseTopics.query.filter_by(topic_id=topicId).first()
                        addNotes = TopicNotes(topic_id=topicId,course_id=courseId.course_id,notes_name=notesName[i],notes_url=videoNotesUrl[i],notes_type=226,is_archived='N',last_modified_date=datetime.now())
                        db.session.add(addNotes)
                        db.session.commit()
                    else:
                        return ""
                else:
                    return ""
    return jsonify("1")

@course.route('/addNotes',methods=['GET','POST'])
def addNotes():
    topicId = request.args.get('topic_id')
    notesName = request.form.getlist('notesName')
    notesURL = request.form.getlist('notesURL')
    videoNotesUrl = request.form.getlist('videoNotesUrl')
    print('topicId:'+str(topicId))
    print('Notes name:'+str(notesName))
    for i in range(len(notesName)):
        print('inside for loop:'+str(i))
        print('NotesName:'+str(notesName[i]))
        print('notesUrl:'+str(notesURL[i]))
        print('videoNotesUrl:'+str(videoNotesUrl[i]))
        print('index:'+str(i))
        if notesURL[i]:
            print('url not null')
            if notesName[i]:
                print('notes name not null')
                if notesURL[i]:
                    courseId = CourseTopics.query.filter_by(topic_id=topicId).first()
                    addNotes = TopicNotes(topic_id=topicId,course_id=courseId.course_id,notes_name=notesName[i],notes_url=notesURL[i],notes_type=226,is_archived='N',last_modified_date=datetime.now())
                    db.session.add(addNotes)
                    db.session.commit()
                else:
                    return ""
            else:
                return ""
        else:
            if notesName[i]: 
                if videoNotesUrl[i]:
                    print('inside when notes name and file uploaded')
                    courseId = CourseTopics.query.filter_by(topic_id=topicId).first()
                    addNotes = TopicNotes(topic_id=topicId,course_id=courseId.course_id,notes_name=notesName[i],notes_url=videoNotesUrl[i],notes_type=226,is_archived='N',last_modified_date=datetime.now())
                    db.session.add(addNotes)
                    db.session.commit()
                else:
                    return ""
            # return ""
            else:
                return ""
    return jsonify("1")

@course.route('/addNewQuestion',methods=['GET','POST'])
def addNewQuestion():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board = SchoolProfile.query.filter_by(school_id=teacherData.school_id).first()
    print('inside add question')
    corr = request.args.get('corr')
    ques = request.args.get('ques')
    opt1 = request.args.get('opt1')
    opt2 = request.args.get('opt2')
    opt3 = request.args.get('opt3')
    opt4 = request.args.get('opt4')
    print('question Desc:'+str(ques))
    print('option 1:'+str(opt1))
    print('option 2:'+str(opt2))
    print('option 3:'+str(opt3))
    print('option 4:'+str(opt4))
    print('correct option:'+str(corr))
    quesCreate = QuestionDetails(board_id=board.board_id,question_description=ques,question_type='MCQ1',suggested_weightage='10',is_private='N',archive_status='N')
    db.session.add(quesCreate)
    db.session.commit()
    for i in range(4):
        op = request.args.get('opt'+str(i+1))
        correctOption = ''
        if str(corr) == str(i+1):
            correctOption = 'Y'
        else:
            correctOption = 'N'
        option = ''
        if i==0:
            option = 'A'
        elif i==1:
            option = 'B'
        elif i==2:
            option = 'C'
        else:
            option = 'D'
        # ques_det = QuestionDetails.query.filter_by(board_id=board.board_id,question_description=ques,question_type='MCQ1',suggested_weightage='10',is_private='N',archive_status='N').first()
        options = QuestionOptions(option=option,is_correct=correctOption,option_desc=op,question_id=quesCreate.question_id,weightage='10',last_modified_date=datetime.now())
        db.session.add(options)
        db.session.commit()
    return jsonify(quesCreate.question_id)
    
@course.route('/fetchQuesList',methods=['GET','POST'])
def fetchQuesList():
    print('inside fetchQuesList')
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    quesList = request.get_json()
    indic = request.args.get('indic')
    print('questionIdList:')
    print(quesList)
    for ques in quesList:
        print('Question_id:')
        print(ques)
    if indic=='1':
        for quesId in quesList:
            quesDesc = QuestionDetails.query.filter_by(question_id=quesId).first()
            print(quesDesc.question_description)
            quesOptions = QuestionOptions.query.filter_by(question_id=quesId).all()
            op1=''
            op2=''
            op3=''
            op4=''
            optionList = []
            quesDetails = []
            corrOption = ''
            for options in quesOptions:
                print('Option Desc:'+str(options.option_desc))
                optionList.append(options.option_desc)
                if options.is_correct=='Y':
                    corrOption = options.option_desc
            for i in range(len(optionList)):
                if i==0:
                    op1=optionList[i]
                elif i==1:
                    op2=optionList[i]
                elif i==2:
                    op3=optionList[i]
                elif i==3:
                    op4=optionList[i]
        print('Question:'+str(quesDesc.question_description)+'op1:'+str(op1)+'op2:'+str(op2)+'op3:'+str(op3)+'op4:'+str(op4))
        quesDetails.append(str(quesDesc.question_description)+':'+str(op1)+':'+str(op2)+':'+str(op3)+':'+str(op4)+':'+str(corrOption))
    return jsonify([quesDetails])

@course.route('/saveAndPublishedCourse',methods=['GET','POST'])
def saveAndPublishedCourse():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #print('inside saveCourse')
    course = request.form.get('course')
    courseId = request.args.get('course_id')
    description = request.form.get('description')
    imageUrl = request.form.get('imageUrl')
    video_url = request.form.get('videoUrl')
    idealfor = request.args.get('idealfor')
    level = request.form.get('level')
    private = request.form.get('private')
    #print('Course name:'+str(course))
    #print('courseId:'+str(courseId))
    #print('description name:'+str(description))
    #print('Image Url:'+str(imageUrl))
    #print('Private:'+str(private))
    course_status = request.args.get('course_status')
    #print('course status:'+str(course_status))
    #
    #print('video_url :'+str(video_url))
    print('Ideal for:'+str(idealfor))
    #print('level:'+str(level))
    updateIndex=False
    levelId = MessageDetails.query.filter_by(description=level,category='Difficulty Level').first()
    courseDet = CourseDetail.query.filter_by(course_id=courseId,description=description,summary_url=video_url,
    teacher_id=teacherData.teacher_id,school_id=teacherData.school_id,ideal_for=idealfor,difficulty_level=levelId.msg_id).first()
    if courseDet:
        course_status_id = MessageDetails.query.filter_by(category='Course Status',description=course_status).first()
        courseDet.course_status=course_status_id.msg_id
        db.session.commit()
        print('returning from first')
        if app.config["MODE"]=="PROD":
            updateIndex = updateSearchIndex("send","saveCourse")
        if updateIndex==True:
            return jsonify("1")
        else:
            return jsonify("2")
    else:
        course_status_id = MessageDetails.query.filter_by(category='Course Status',description=course_status).first()
        courseDet = CourseDetail.query.filter_by(course_id=courseId).first()
        if private:
            print('if course status is private')
            courseDet.description=description
            courseDet.summary_url=video_url
            courseDet.teacher_id=teacherData.teacher_id
            courseDet.school_id=teacherData.school_id
            if idealfor:
                courseDet.ideal_for=idealfor
            courseDet.course_status=course_status_id.msg_id
            courseDet.is_private='Y'
            courseDet.image_url = imageUrl
            courseDet.is_archived = 'N'
            courseDet.difficulty_level=levelId.msg_id
        else:
            print('if course status is public')
            courseDet.description=description
            courseDet.summary_url=video_url
            courseDet.teacher_id=teacherData.teacher_id
            courseDet.school_id=teacherData.school_id
            if idealfor:
                courseDet.ideal_for=idealfor
            courseDet.course_status=course_status_id.msg_id
            courseDet.is_private='N'
            courseDet.image_url = imageUrl
            courseDet.is_archived = 'N'
            courseDet.difficulty_level=levelId.msg_id
        db.session.commit()
        updateIndex = updateSearchIndex("send","saveCourse")
        if updateIndex==True:
            return jsonify("1")
        else:
            return jsonify("2")



@course.route('/saveCourse',methods=['GET','POST'])
def saveCourse():
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print('inside saveCourse')
    course = request.form.get('course')
    courseId = request.args.get('course_id')
    description = request.form.get('description')
    # setDate = request.form.get('setDate')
    # startTime = request.form.get('startTime')
    # endTime = request.form.get('endTime')
    # days = request.form.getlist('Days')
    imageUrl = ''
    imgUrl= request.form.get('imageUrl')
    if imgUrl!=None:
        imageUrl = imgUrl
    video_url = request.form.get('videoUrl')
    idealfor = request.args.get('idealfor')
    level = request.form.get('level')
    private = request.form.get('private')
    print('Course name:'+str(course))
    print('courseId:'+str(courseId))
    print('description name:'+str(description))
    print('Private:'+str(private))
    print('course Image:'+str(imageUrl))
    course_status = request.args.get('course_status')
    print('course status:'+str(course_status))
   
    print('video_url :'+str(video_url))
    print('Ideal for:'+str(idealfor))
    print('level:'+str(level))
    levelId = MessageDetails.query.filter_by(description=level,category='Difficulty Level').first()
    course_status_id = MessageDetails.query.filter_by(category='Course Status',description=course_status).first()
    courseDet = CourseDetail.query.filter_by(course_id=courseId).first()
    if private:
        print('if course status is private')
        courseDet.description=description
        courseDet.summary_url=video_url
        courseDet.teacher_id=teacherData.teacher_id
        courseDet.school_id=teacherData.school_id
        if idealfor:
            courseDet.ideal_for=idealfor
        courseDet.course_status=course_status_id.msg_id
        courseDet.is_private='Y'
        courseDet.image_url = imageUrl
        courseDet.is_archived = 'N'
        courseDet.difficulty_level=levelId.msg_id
    else:
        print('if course status is public')
        courseDet.description=description
        courseDet.summary_url=video_url
        courseDet.teacher_id=teacherData.teacher_id
        courseDet.school_id=teacherData.school_id
        if idealfor:
            courseDet.ideal_for=idealfor
        courseDet.course_status=course_status_id.msg_id
        courseDet.is_private='N'
        courseDet.image_url = imageUrl
        courseDet.is_archived = 'N'
        courseDet.difficulty_level=levelId.msg_id
    db.session.commit()
    print('course:'+str(course))
    print('Desc:'+str(description))
    print('url:'+str(video_url))
    print('teacher_id:'+str(teacherData.teacher_id))
    print('school_id:'+str(teacherData.school_id))
    print('idealfor:'+str(idealfor))
    print('course_status:'+str(course_status_id.msg_id))    
    return jsonify("1")

@course.route('/courseEntry',methods=['GET','POST'])
def courseEntry():
    course = request.args.get('course')
    course_id = "select max(course_id) as course_id from course_detail "
    course_id = db.session.execute(text(course_id)).first()
    courseDet = CourseDetail.query.filter_by(course_id=course_id.course_id).first()
    courseDet.course_name = course
    db.session.commit()
    # courseId = "select max(course_id) as course_id from course_detail"
    # courseId = db.session.execute(text(courseId)).first()
    return jsonify(courseDet.course_id)

    # return render_template('editCourse.html')


@course.route('/myCourses')
def myCourses():

    return render_template('myCourses.html')

@course.route('/courseHome')
def courseHome():    
    if ("school.alllearn" in str(request.url)):
        print('#######this is the request url: '+ str(request.url))
        return redirect(url_for('index')) 
    #print(str(current_user.is_anonymous))
    upcomingClassData = ""
    
    #if current_user.is_anonymous==False:
        #upcomingClassQuery = "select * from vw_course_reminder_everyday where email=" + str(current_user.email)
        #upcomingClassData = db.session.execute(upcomingClassQuery).fetchall()
    enrolledCourses = "select ce.COURSE_ID, MAX(ce.LAST_MODIFIED_DATE), cd.course_name, cd.average_rating , cd.description ,cd.image_url, cd.is_archived,cd.course_status, tp.teacher_name,tp.teacher_id from course_enrollment ce "
    enrolledCourses = enrolledCourses + "inner join course_detail cd on cd.course_id =ce.course_id "
    enrolledCourses = enrolledCourses + "inner join teacher_profile tp on tp.teacher_id =cd.teacher_id "
    enrolledCourses = enrolledCourses + "group by ce.course_id,cd.course_name,cd.average_rating , cd.description , cd.image_url,cd.course_status, cd.is_archived, cd.teacher_id, tp.teacher_name, tp.teacher_id "
    enrolledCourses = enrolledCourses + "having cd.course_status =276 and cd.is_archived ='N' order by max(ce.last_modified_date ) desc limit 8"
    enrolledCourses = db.session.execute(text(enrolledCourses)).fetchall()
    recentlyAccessed = "select cd.COURSE_ID, MAX(cd.LAST_MODIFIED_DATE), cd.course_name, cd.average_rating , cd.description ,cd.image_url, cd.is_archived,cd.course_status, tp.teacher_name,cd.teacher_id from course_detail cd "
    recentlyAccessed = recentlyAccessed + "inner join teacher_profile tp on tp.teacher_id =cd.teacher_id "
    recentlyAccessed = recentlyAccessed + "group by cd.course_id,cd.course_name,cd.average_rating , cd.description , cd.image_url,cd.course_status, cd.is_archived, cd.teacher_id, tp.teacher_name having cd.course_status =276 and cd.is_archived ='N' order by max(cd.last_modified_date ) desc limit 8"
    recentlyAccessed = db.session.execute(text(recentlyAccessed)).fetchall() 

    for rate in enrolledCourses:
        print('Rating:'+str(rate.average_rating))
        if rate.average_rating:
            print('rate:'+str(rate.average_rating))

    idealFor = CourseDetail.query.distinct(CourseDetail.ideal_for).all()
    idealList = []
    for ideal in idealFor:
        print('ideal for:'+str(ideal.ideal_for))
        if ideal.ideal_for:
            data = ideal.ideal_for.split(',')
            for d in data:
                if d not in idealList:
                    idealList.append(d)
    print('List:'+str(idealList))
    indic='DashBoard'
    return render_template('courseHome.html',indic=indic,idealList=idealList,recentlyAccessed=recentlyAccessed,enrolledCourses=enrolledCourses,home=1, upcomingClassData=upcomingClassData)

@course.route('/courseDetail')
def courseDetail():
    live_class_id = request.args.get('live_class_id')
    course_id = request.args.get('course_id')
    courseDet = CourseDetail.query.filter_by(course_id=course_id).first()
    teacher = TeacherProfile.query.filter_by(teacher_id=courseDet.teacher_id).first()
    teacherUser = User.query.filter_by(id=teacher.user_id).first()

    upcomingDate = "SELECT * FROM course_batch WHERE batch_start_date > NOW() and course_id='"+str(course_id)+"' ORDER BY batch_start_date LIMIT 1"
    upcomingDate = db.session.execute(text(upcomingDate)).first()
    checkEnrollment = ''
    if upcomingDate and current_user.is_authenticated :
        checkEnrollment = CourseEnrollment.query.filter_by(is_archived='N',course_id=course_id,student_user_id=current_user.id).first()

    idealFor = courseDet.ideal_for.split(",")
    
    levelId = courseDet.difficulty_level
    level = MessageDetails.query.filter_by(msg_id=levelId,category='Difficulty Level').first()
    #rating = CourseDetail.query.filter_by(course_id=course_id,is_archived='N').first()
    #if rating:
    #    print('Star rating:'+str(rating.average_rating))
    comments = "select u.username,cr.comment,cr.last_modified_date from course_review cr inner join public.user u on u.id=cr.user_id where cr.course_id = '"+str(course_id)+ "' and cr.comment <> ' '"
    #print(comments)
    comments = db.session.execute(text(comments)).fetchall()
    lenComment = len(comments)
    #print(comments)
    otherCourses = "select *from course_detail cd where cd.course_id <> '"+str(course_id)+"' and cd.teacher_id='"+str(teacher.teacher_id)+"' and cd.course_status =276"
    otherCourses = db.session.execute(text(otherCourses)).fetchall()


    pageTitle = courseDet.course_name
    return render_template('courseDetail.html',
        lenComment=lenComment,comments=comments,otherCourses=otherCourses,level=level,
        idealFor=idealFor,upcomingDate=upcomingDate,
        courseDet=courseDet,meta_val=pageTitle,title=pageTitle,teacherUser=teacherUser,checkEnrollment=checkEnrollment,course_id=course_id,teacher=teacher)


@course.route('/courseTopicDetail')
def courseTopicDetail():
    course_id = request.args.get('course_id')
    topicDet = "select case when count(tq.question_id) >0 then count(tq.question_id )"
    topicDet = topicDet + " else 0 end as no_of_questions , topic_name,ct.video_class_url, ct.topic_id, course_id from course_topics ct "
    topicDet = topicDet + " inner join topic_detail td on td.topic_id =ct.topic_id and ct.course_id =" + str(course_id)
    topicDet = topicDet + " left join test_questions tq on tq.test_id =ct.test_id "    
    topicDet = topicDet + " where ct.is_archived ='N' group by  topic_name, ct.topic_id, course_id,ct.video_class_url"
    topicDet = topicDet + " order by topic_id asc "
    #print(topicDet)
    topicDet = db.session.execute(text(topicDet)).fetchall()
    return render_template('_courseTopicDetail.html', topicDet=topicDet,course_id=course_id)
