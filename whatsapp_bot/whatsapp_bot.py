from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, url_for, session,jsonify
from datetime import datetime
from pytz import timezone
from tzlocal import get_localzone
from flask import g, jsonify
from sqlalchemy import func, distinct, text
from random import randint
import json


whatsapp_bot = Blueprint('whatsapp_bot',__name__)

@whatsapp_bot.route('/checkContact',methods=['POST','GET'])
def checkContact():
    if request.method == 'POST':
        print('inside checkContact')
        jsonExamData = request.json
        a = json.dumps(jsonExamData)
        z = json.loads(a)
        conList = []
        for con in z['results'].values():
            conList.append(con)
        contactNo = conList[0]
        print(contactNo)
        msg = ''
        checkContact = User.query.filter_by(phone=contactNo).first()
        print(checkContact)
        if checkContact:
            msg = 'Exist'
            print('Exist')
            return jsonify({'msg':msg})
        else:
            msg = 'New'
            print('New')
            return jsonify({'msg':msg})

@whatsapp_bot.route('/checkQuesNo',methods=['GET','POST'])
def checkQuesNo():
    if request.method == 'POST':
        print('inside checkQuesNo')
        jsonData = request.json
        print('jsonData:')
        print(jsonData)
        
        userData = json.dumps(jsonData)
        user = json.loads(userData)   
        paramList = []
        for con in user['results'].values():
            paramList.append(con)     
        quesCount = paramList[0]
        if int(quesCount) > 15:
            print('question count greater then 18')
            return jsonify({'msg':'Greater'})
        else:
            print('question count less then 18')
            return jsonify({'msg':'Less'})    

@whatsapp_bot.route('/registerUser',methods=['POST','GET'])
def registerUser():
    if request.method == 'POST':
        print('inside register user')
        jsonData = request.json
        # jsonData = {'contact': {'fields': {'age_group': {'inserted_at': '2021-01-25T06:36:45.002400Z', 'label': 'Age Group', 'type': 'string', 'value': '19 or above'}, 'name': {'inserted_at': '2021-01-25T06:35:49.876654Z', 'label': 'Name', 'type': 'string', 'value': 'hi'}}, 'name': 'Zaheen', 'phone': '918802362259'}, 'results': {}, 'custom_key': 'custom_value'}
        print('jsonData:')
        print(jsonData)
        
        userData = json.dumps(jsonData)
        user = json.loads(userData)
        conList = []
        for con in user['contact'].values():
            conList.append(con)
        print(conList)
        contactNo = conList[2][-10:]
        print(contactNo)
        userId = User.query.filter_by(phone=contactNo).first()
        teacher = ''
        if userId:
            teacher_id = TeacherProfile.query.filter_by(user_id=userId.id).first()
            student_id = StudentProfile.query.filter_by(user_id=userId.id).first()
            if userId.user_type == 71:
                teacher = 'Teacher'
                print('User is Teacher')
                if teacher_id.school_id:
                    schoolDet = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
                else:
                    return jsonify({'user':'Unregistered'})
                if schoolDet.is_verified == 'N':
                    return jsonify({'user':'Parent'})
                lastName = ''
                if userId.last_name:
                    lastName = userId.last_name
                return jsonify({'user':teacher,'firstName':str(userId.first_name)+str(' ')+str(lastName)})
                
            elif userId.user_type == 134:
                student = 'Student'
                print('user is student')
                if student_id.school_id:
                    schoolDet = SchoolProfile.query.filter_by(school_id=student_id.school_id).first()
                else:
                    return jsonify({'user':'Unregistered'})
                if schoolDet.is_verified == 'N':
                    return jsonify({'user':'Parent'})
                lastName = ''
                if userId.last_name:
                    lastName = userId.last_name
                return jsonify({'user':student,'firstName':str(userId.first_name)+str(' ')+str(lastName),'studentId':student_id.student_id})
            else:
                parent = 'Parent'
                print('user is parent outside if')
                if userId.user_type==72:
                    print('user is parent inside if')
                    guardianDet = GuardianProfile.query.filter_by(user_id=userId.id).first()
                    print('guardianDet:')
                    print(guardianDet)
                    studentDet = StudentProfile.query.filter_by(student_id=guardianDet.student_id).first()
                    print('studentDet:')
                    print(studentDet)
                    lastName = ''
                    if userId.last_name:
                        lastName = userId.last_name
                    return jsonify({'user':parent,'firstName':str(userId.first_name)+str(' ')+str(lastName),'studentName':studentDet.full_name,'studentId':studentDet.student_id})
        print('not registered user')
        return jsonify({'user':'null'})

@whatsapp_bot.route('/accessSchool',methods=['GET','POST'])
def accessSchool():
    if request.method == 'POST':
        print('inside accessSchool')
        jsonStudentData = request.json
        newData = json.dumps(jsonStudentData)
        data = json.loads(newData)
        paramList = []
        conList = []
        print(data)
        for values in data['results'].values():
            paramList.append(values)    
        for con in data['contact'].values():
            conList.append(con)
        contactNo = conList[2][-10:]
        print(contactNo)      
        schoolDet = SchoolProfile.query.filter_by(school_id=paramList[0]).first()
        if schoolDet:
            userDet = User.query.filter_by(phone=contactNo).first()
            userDet.school_id =  schoolDet.school_id
            db.session.commit()
            teacherDet = TeacherProfile.query.filter_by(phone=contactNo).first()
            studentDet = StudentProfile.query.filter_by(phone=contactNo).first()
            if teacherDet:
                teacherDet.school_id = schoolDet.school_id
            if studentDet:
                studentDet.school_id = schoolDet.school_id
            db.session.commit()
            statement = 'Access request sent to the school admin.'
            return jsonify({'statement':statement})   
        else:
            statement = "School id does not exist."
            return jsonify({'statement':statement})

@whatsapp_bot.route('/checkMailId',methods=['GET','POST'])
def checkMailId():
    if request.method == 'POST':
        print('inside checkMailID')
        jsonStudentData = request.json
        newData = json.dumps(jsonStudentData)
        data = json.loads(newData)
        paramList = []
        for values in data['results'].values():
            paramList.append(values) 
        email = paramList[0]
        checkUser = User.query.filter_by(email=email).first()
        statement = ''
        if checkUser:
            statement = 'Exist'
            return jsonify({'statement':statement})
        else:
            statement = 'No'
        return jsonify({'statement':statement})  


@whatsapp_bot.route('/checkSchoolList',methods=['GET','POST'])
def checkSchoolList():
    if request.method == 'POST':
        print('inside schoolList')
        jsonStudentData = request.json
        newData = json.dumps(jsonStudentData)
        data = json.loads(newData)
        paramList = []
        conList = []
        print(data)
        for values in data['results'].values():
            paramList.append(values)    
        for con in data['contact'].values():
            conList.append(con)
        contactNo = conList[2][-10:]
        print(contactNo)
        for param in paramList:
            print(param)
        print(paramList[1])
        schoolNam = paramList[3].upper()
        schoolDetQuery = "select school_id,school_name from school_profile where INITCAP(school_name) like initcap('%"+str(schoolNam)+"%')"
        print(schoolDetQuery)
        schoolDet = db.session.execute(text(schoolDetQuery)).fetchall()
        data = ''
        i=1
        if len(schoolDet) != 0:
            data = 'Exist'
        else:
            data = 'None'
        # data = data + '\n If your school is not in this list, please type 00'
        print(data)
        return jsonify({'isSchoolList':data})         

@whatsapp_bot.route('/checkClass',methods=['GET','POST'])
def checkClass():
    if request.method == 'POST':
        print('inside checkClass')
        jsonStudentData = request.json
        newData = json.dumps(jsonStudentData)
        data = json.loads(newData)
        paramList = []  
        for values in data['results'].values():
            paramList.append(values) 
        clas = paramList[0].split('-')[0]
        section = paramList[0].split('-')[1]
        print('Class'+str(clas))
        print('Section'+str(section))
        classSecId = ClassSection.query.filter_by(class_val=clas,section=section,school_id=userDet.school_id).first()
        if classSecId == '' or classSecId == None:
            statement = 'Class does not exist.'
            return jsonify({'statement':statement})  
        statement = "What's your school's name?"    
        return jsonify({'statement':statement})

@whatsapp_bot.route('/studentSubjectList',methods=['GET','POST'])
def studentSubjectList():
    if request.method == 'POST':
        print('inside studentSubjectList')
        jsonStudentData = request.json
        newData = json.dumps(jsonStudentData)
        data = json.loads(newData)
        paramList = []
        conList = []
        print(data)
        for values in data['results'].values():
            paramList.append(values) 
        for con in data['contact'].values():
            conList.append(con)
        contactNo = conList[2][-10:]
        print(contactNo)
        studentDet = StudentProfile.query.filter_by(phone=contactNo).first()
        clasDet = ClassSection.query.filter_by(class_sec_id=studentDet.class_sec_id).first()
        subQuery = "select md.description as subject from board_class_subject bcs inner join message_detail md on bcs.subject_id = md.msg_id where school_id='"+str(studentDet.school_id)+"' and class_val = '"+str(clasDet.class_val)+"'"
        print(subQuery)
        subjectData = db.session.execute(text(subQuery)).fetchall()
        print(subjectData)
        subjectList = []
        k=1
        for subj in subjectData:
            if k==1:
                sub = str('Which Subject?\n')+str(k)+str('-')+str(subj.subject)+str("\n")
            else:
                sub = str(k)+str('-')+str(subj.subject)+str("\n")
            subjectList.append(sub)
            k=k+1      
        msg = 'no subjects available'
        if subjectList:
            return jsonify({'subject_list':subjectList,'class_val':clasDet.class_val}) 
        else:
            return jsonify({'subject_list':msg})   

@whatsapp_bot.route('/classSectionCheck',methods=['GET','POST'])
def classSectionCheck():
    if request.method == 'POST':
        print('inside classSectionCheck')
        jsonStudentData = request.json
        newData = json.dumps(jsonStudentData)
        data = json.loads(newData)
        paramList = []
        conList = []
        for values in data['results'].values():
            paramList.append(values)    
        for con in data['contact'].values():
            conList.append(con)
        contactNo = conList[2][-10:]
        print(paramList)
        print(paramList[0])   
        subString = '-'
        if subString in paramList[0]:
            print('Y')
            return jsonify({'msg':'Y'})
        else:
            print('N')
            return jsonify({'msg':'N'})


@whatsapp_bot.route('/unregisterSchoolRegistered',methods=['GET','POST'])
def unregisterSchoolRegistered():
    if request.method == 'POST':
        print('inside unregisterSchoolRegistered')
        jsonStudentData = request.json
        newData = json.dumps(jsonStudentData)
        data = json.loads(newData)
        paramList = []
        conList = []
        print(data)
        for values in data['results'].values():
            paramList.append(values)    
        for con in data['contact'].values():
            conList.append(con)
        contactNo = conList[2][-10:]
        print(contactNo)
        latitude = paramList[9]
        longitude = paramList[10]
        print('latitude:'+str(latitude))
        print('longitude:'+str(longitude))
        substring = '.latitude'
        if substring in latitude:
            createAddress = Address(address_1=paramList[3],city=paramList[4],state=paramList[5],country='india')
            db.session.add(createAddress)
            db.session.commit()
        else:
            createAddress = Address(latitude=latitude,longitude=longitude)
            db.session.add(createAddress)
            db.session.commit()
        boardId = ''
        schoolType = ''
        if paramList[7] == '1':
            boardId = 1001
        elif paramList[7] == '2':
            boardId = 1002
        elif paramList[7] == '3':
            boardId = 1005
        else:
            boardId = 1003
        if paramList[6] == '1':
            schoolType = 'Affordable private school'
        elif paramList[6] == '2':
            schoolType = 'NGO School'
        elif paramList[6] == '3':
            schoolType = 'Elite private school'
        else: 
            schoolType = 'Other'
        createTeacher = TeacherProfile.query.filter_by(phone=contactNo).first()
        createStudent = StudentProfile.query.filter_by(phone=contactNo).first()
        createUser = User.query.filter_by(phone=contactNo).first()
        createSchool = SchoolProfile(school_name=paramList[2],registered_date=datetime.now(),last_modified_date=datetime.now(),address_id=createAddress.address_id,board_id=boardId,school_admin=createTeacher.teacher_id,sub_id=2,is_verified='N',school_type=schoolType)
        db.session.add(createSchool)
        db.session.commit()
        print(createSchool.school_id)
        createUser.school_id = createSchool.school_id
        db.session.commit()
        if createTeacher:
            print('user is teacher School id: '+str(createSchool.school_id))
            print('school id in teacher table before update:'+str(createTeacher.school_id))
            createTeacher.school_id = createSchool.school_id
            db.session.commit()
            print('school id in teacher table after update:'+str(createTeacher.school_id))
        if createStudent:
            print('user is student')
            createStudent.school_id = createSchool.school_id
            db.session.commit()
        db.session.commit()
        return jsonify({'success':'success'})        

@whatsapp_bot.route('/getStudentEnteredTopicList',methods=['POST','GET'])
def getStudentEnteredTopicList():
    if request.method == 'POST':
        print('inside getStudentEnteredTopicList')
        jsonExamData = request.json
        # jsonExamData = {"results": {"weightage": "10","topics": "1","subject": "1","question_count": "10","class_val": "3","uploadStatus":"Y","duration":"0","resultStatus":"Y","instructions":"","advance":"Y","negativeMarking":"0","test_type":"Class Feedback"},"custom_key": "custom_value","contact": {"phone": "9008262739"}}
        
        a = json.dumps(jsonExamData)
      
        z = json.loads(a)
        
        paramList = []
        conList = []
        print('data:')
        # print(z['result'].class_val)
        # print(z['result'])
        for data in z['results'].values():
            
            paramList.append(data)
        for con in z['contact'].values():
            conList.append(con)
        print(paramList)
        print(conList[2])
        
        print('Data Contact')
        # print(conList[2])
        contactNo = conList[2][-10:]
        print(contactNo)
        studentData = StudentProfile.query.filter_by(phone=contactNo).first()
        teacher_id = TeacherProfile.query.filter_by(user_id=studentData.user_id).first()
        classesListData = ClassSection.query.filter_by(class_sec_id=studentData.class_sec_id).first()
        print('class')
        selClass = paramList[12]
        selClass = selClass.strip()
        print(selClass)

        print('Subject:')
        selSubject = paramList[13]
        selSubject = selSubject.strip()
        # Start for topic
        subQuery = MessageDetails.query.filter_by(description=selSubject).first()
        subId = subQuery.msg_id
        print(selSubject)
        print('SubId:'+str(subId))
        topics = paramList[1].strip()
        topicList = topics.split(',')
        print(topicList[0])
        topic = topicList[0].capitalize()
        print('Topic:'+str(topic))
        dateVal= datetime.today().strftime("%d%m%Y%H%M%S")
        p =1
        for topic in topicList:
            fetchQuesIdsQuery = "select td.board_id,qd.suggested_weightage,qd.question_type,qd.question_id,qd.question_description,td.subject_id,td.topic_id "
            fetchQuesIdsQuery = fetchQuesIdsQuery + "from question_details qd inner join topic_detail td on qd.topic_id = td.topic_id inner join message_detail md on md.msg_id = td.subject_id "
            fetchQuesIdsQuery = fetchQuesIdsQuery + "where initcap(td.topic_name) like initcap('%"+str(topic.capitalize())+"%') and td.class_val='"+str(selClass)+"' and md.description ='"+str(selSubject)+"' limit 5"
            if p<len(topicList):
                fetchQuesIdsQuery = fetchQuesIdsQuery + "union "
            p=p+1
        print('fetchQuesIds Query:'+str(fetchQuesIdsQuery))
        fetchQuesIds = db.session.execute(fetchQuesIdsQuery).fetchall()
        Msg = 'no questions available'
        if len(fetchQuesIds)==0:
            return jsonify({'onlineTestLink':Msg})
        listLength = len(fetchQuesIds)
        count_marks = int(paramList[0]) * int(listLength)
        
        subjId = ''
        topicID = ''
        boardID = ''
        for det in fetchQuesIds:
            subjId = det.subject_id
            topicID = det.topic_id
            boardID = det.board_id
            break
        print('subjId:'+str(subjId))
        print(fetchQuesIds)
        # currClassSecRow=ClassSection.query.filter_by(school_id=str(teacher_id.school_id),class_val=str(selClass).strip()).first()
        resp_session_id = str(subId).strip()+ str(dateVal).strip() + str(randint(10,99)).strip()
        format = "%Y-%m-%d %H:%M:%S"
        now_utc = datetime.now(timezone('UTC'))
        now_local = now_utc.astimezone(get_localzone())
        print('Date of test creation:'+str(now_local.strftime(format)))

        # clasVal = selClass.replace('_','@')
        # testType = paramList[11].replace('_','@')
        # linkForTeacher=url_for('testLinkWhatsappBot',testType=paramList[11],totalMarks=count_marks,respsessionid=resp_session_id,fetchQuesIds=fetchQuesIds,weightage=10,negativeMarking=paramList[10],uploadStatus=paramList[5],resultStatus=paramList[7],advance=paramList[9],instructions=paramList[8],duration=paramList[6],classVal=clasVal,section=currClassSecRow.section,subjectId=subjId,phone=contactNo, _external=True)
        # key = '265e29e3968fc62f68da76a373e5af775fa60'
        # url = urllib.parse.quote(linkForTeacher)
        # name  = ''
        # r = rq.get('http://cutt.ly/api/api.php?key={}&short={}&name={}'.format(key, url, name))
        # print('New Link')
        # print(r.text)
        # print(type(r.text))
        # linkList = []
        # jsonLink = json.dumps(r.text)
        # newData = json.loads(r.text)
        # print(type(newData))
        # for linkData in newData['url'].values():
        #     linkList.append(linkData)
        # finalLink = linkList[3]
        # newLink = str('Here is the link to the online test:\n')+finalLink+str('\nDo you want to download the question paper?\n1 - Yes\n2 - No')
        # print('newLink'+str(newLink))
        test_type=paramList[11]
        count = paramList[3]
        weightage = paramList[0]
        total_marks = int(count) * int(weightage)
        class_sec_id = classesListData.class_sec_id
        print('selected chapter')
        print(paramList[1])
        # file_name_val = url_for('question_paper',limit=paramList[3],chapter=paramList[1],schoolName=paramList[18],class_val=selClass,test_type=paramList[11],subject=selSubject,total_marks=count_marks,today=datetime.today().strftime("%d%m%Y%H%M%S"),_external=True)
        file_name_val = url_for('downloadPaper',test_id='123')
        return jsonify({'fileName':file_name_val,'selChapter':paramList[1],'boardID':boardID,'resp_session_id':resp_session_id})      

@whatsapp_bot.route('/addStudentEnteredTopicTestDet',methods=['GET','POST'])
def addStudentEnteredTopicTestDet():
    if request.method == 'POST':
        print('inside addStudentEnteredTopicTestDet')
        print('insert addEnteredTopicTestDet')
        jsonExamData = request.json
        a = json.dumps(jsonExamData)
        z = json.loads(a)
        paramList = []
        conList = []
        print('data:')
        print(z)
        for data in z['results'].values():
                
            paramList.append(data)
            print('data:'+str(data))
        for con in z['contact'].values():
            conList.append(con)
        print(paramList)

        print(conList[2])
        print('Testing for topic')
        # print(type(paramList[1]))
        # print(int(paramList[1]))
            # 
        print('Data Contact')
        contactNo = conList[2][-10:]
        print(contactNo)
        studentData = StudentProfile.query.filter_by(phone=contactNo).first()
        userId = paramList[14]
        teacher_id = paramList[15]
            
        selClass = paramList[12]
            
        selSubject = paramList[13]
        subId = paramList[16]
        print(selSubject)
        print('SubId:'+str(subId))
        topics = paramList[1].strip()
        topicList = topics.split(',')
        print(topicList[0])
        topic = topicList[0].capitalize()
        print('Topic:'+str(topic))
        dateVal= datetime.today().strftime("%d%m%Y%H%M%S")
        p =1
        for topic in topicList:
            fetchQuesIdsQuery = "select td.board_id,qd.suggested_weightage,qd.question_type,qd.question_id,qd.question_description,td.subject_id,td.topic_id "
            fetchQuesIdsQuery = fetchQuesIdsQuery + "from question_details qd inner join topic_detail td on qd.topic_id = td.topic_id inner join message_detail md on md.msg_id = td.subject_id "
            fetchQuesIdsQuery = fetchQuesIdsQuery + "where initcap(td.topic_name) like initcap('%"+str(topic.capitalize())+"%') and qd.archive_status='N' and qd.question_type='MCQ1' and td.class_val='"+str(selClass)+"' and md.description ='"+str(selSubject)+"' limit 5"
            if p<len(topicList):
                fetchQuesIdsQuery = fetchQuesIdsQuery + "union "
            p=p+1
        print('fetchQuesIds Query:'+str(fetchQuesIdsQuery))
        fetchQuesIds = db.session.execute(fetchQuesIdsQuery).fetchall()
        msg = 'No questions available'
        if len(fetchQuesIds)==0 or fetchQuesIds=='':
            return jsonify({'testId':msg})
        listLength = len(fetchQuesIds)
        total_marks = int(paramList[0]) * int(listLength)
        boardID = paramList[20]
        test_type = paramList[11]
        subjId = paramList[16]
        class_val = paramList[4]
        file_name_val = paramList[21]
        school_id = paramList[17]
        teacher_id = paramList[15]
        resp_session_id = paramList[22]
        format = "%Y-%m-%d %H:%M:%S"
        now_utc = datetime.now(timezone('UTC'))
        now_local = now_utc.astimezone(get_localzone())
        print('Date of test creation:'+str(now_local.strftime(format)))
        classDet = ClassSection.query.filter_by(class_val=selClass,school_id=studentData.school_id).first()
        class_sec_id = classDet.class_sec_id
        testDetailsUpd = TestDetails(test_type=str(test_type), total_marks=str(total_marks),last_modified_date= datetime.now(),
            board_id=str(boardID), subject_id=int(subjId),class_val=str(selClass),date_of_creation=now_local.strftime(format),
            date_of_test=datetime.now(), school_id=studentData.school_id, teacher_id=teacher_id)
        db.session.add(testDetailsUpd)
        db.session.commit()
        file_name_val = url_for('downloadPaper',test_id=testDetailsUpd.test_id,_external=True)
        testDet = TestDetails.query.filter_by(test_id=testDetailsUpd.test_id).first()
        testDet.test_paper_link = file_name_val
        db.session.commit()
        sessionDetailRowInsert=SessionDetail(resp_session_id=resp_session_id,session_status='80',teacher_id= teacher_id,
            test_id=str(testDetailsUpd.test_id).strip(),class_sec_id=class_sec_id,correct_marks=10,incorrect_marks=0, test_time=0,total_marks=total_marks, last_modified_date = str(now_local.strftime(format)))
        db.session.add(sessionDetailRowInsert)
        for questionVal in fetchQuesIds:
            testQuestionInsert= TestQuestions(test_id=testDetailsUpd.test_id, question_id=questionVal.question_id, last_modified_date=datetime.now(),is_archived='N')
            db.session.add(testQuestionInsert)
        db.session.commit()
        testId = testDetailsUpd.test_id 
        return jsonify({'testId':testId,'section':classDet.section,'total_marks':total_marks})   

@whatsapp_bot.route('/addEnteredTopicTestDet',methods=['GET','POST'])
def addEnteredTopicTestDet():
    if request.method == 'POST':
        print('insert addEnteredTopicTestDet')
        jsonExamData = request.json
        a = json.dumps(jsonExamData)
        z = json.loads(a)
        paramList = []
        conList = []
        print('data:')
        print(z)
        for data in z['results'].values():
                
            paramList.append(data)
            print('data:'+str(data))
        for con in z['contact'].values():
            conList.append(con)
        print(paramList)

        print(conList[2])
        print('Testing for topic')
        # print(type(paramList[1]))
        # print(int(paramList[1]))
            # 
        print('Data Contact')
        contactNo = conList[2][-10:]
        print(contactNo)
        # studentData = StudentProfile.query.filter_by(phone=contactNo).first()
        userId = paramList[14]
        teacher_id = paramList[15]
            
        selClass = paramList[12]
            
        selSubject = paramList[13]
        subId = paramList[16]
        print(selSubject)
        print('SubId:'+str(subId))
        topics = paramList[1].strip()
        topicList = topics.split(',')
        print(topicList[0])
        topic = topicList[0].capitalize()
        print('Topic:'+str(topic))
        dateVal= datetime.today().strftime("%d%m%Y%H%M%S")
        p =1
        for topic in topicList:
            fetchQuesIdsQuery = "select td.board_id,qd.suggested_weightage,qd.question_type,qd.question_id,qd.question_description,td.subject_id,td.topic_id "
            fetchQuesIdsQuery = fetchQuesIdsQuery + "from question_details qd inner join topic_detail td on qd.topic_id = td.topic_id inner join message_detail md on md.msg_id = td.subject_id "
            fetchQuesIdsQuery = fetchQuesIdsQuery + "where initcap(td.topic_name) like initcap('%"+str(topic.capitalize())+"%') and qd.archive_status='N' and qd.question_type='MCQ1' and td.class_val='"+str(selClass)+"' and md.description ='"+str(selSubject)+"' limit 5"
            if p<len(topicList):
                fetchQuesIdsQuery = fetchQuesIdsQuery + "union "
            p=p+1
        print('fetchQuesIds Query:'+str(fetchQuesIdsQuery))
        fetchQuesIds = db.session.execute(fetchQuesIdsQuery).fetchall()
        msg = 'No questions available'
        if len(fetchQuesIds)==0 or fetchQuesIds=='':
            return jsonify({'testId':msg})
        listLength = len(fetchQuesIds)
        total_marks = int(paramList[0]) * int(listLength)
        boardID = paramList[20]
        test_type = paramList[11]
        subjId = paramList[16]
        class_val = paramList[4]
        file_name_val = paramList[21]
        school_id = paramList[17]
        teacher_id = paramList[15]
        resp_session_id = paramList[22]
        format = "%Y-%m-%d %H:%M:%S"
        now_utc = datetime.now(timezone('UTC'))
        now_local = now_utc.astimezone(get_localzone())
        print('Date of test creation:'+str(now_local.strftime(format)))
        classDet = ClassSection.query.filter_by(class_val=selClass,school_id=school_id).first()
        class_sec_id = classDet.class_sec_id
        testDetailsUpd = TestDetails(test_type=str(test_type), total_marks=str(total_marks),last_modified_date= datetime.now(),
            board_id=str(boardID), subject_id=int(subjId),class_val=str(selClass),date_of_creation=now_local.strftime(format),
            date_of_test=datetime.now(), school_id=school_id, teacher_id=teacher_id)
        db.session.add(testDetailsUpd)
        db.session.commit()
        file_name_val = url_for('downloadPaper',test_id=testDetailsUpd.test_id,_external=True)
        testDet = TestDetails.query.filter_by(test_id=testDetailsUpd.test_id).first()
        testDet.test_paper_link = file_name_val
        db.session.commit()
        sessionDetailRowInsert=SessionDetail(resp_session_id=resp_session_id,session_status='80',teacher_id= teacher_id,
            test_id=str(testDetailsUpd.test_id).strip(),class_sec_id=class_sec_id,correct_marks=10,incorrect_marks=0, test_time=0,total_marks=total_marks, last_modified_date = str(now_local.strftime(format)))
        db.session.add(sessionDetailRowInsert)
        for questionVal in fetchQuesIds:
            testQuestionInsert= TestQuestions(test_id=testDetailsUpd.test_id, question_id=questionVal.question_id, last_modified_date=datetime.now(),is_archived='N')
            db.session.add(testQuestionInsert)
        db.session.commit()
        testId = testDetailsUpd.test_id 
        return jsonify({'testId':testId,'section':classDet.section,'total_marks':total_marks})   

@whatsapp_bot.route('/addStudentTestDet',methods=['GET','POST'])
def addStudentTestDet():
    if request.method == 'POST':
        print('inside addStudentTestDet')        
        jsonExamData = request.json
            # jsonExamData = {"results": {"weightage": "10","topics": "1","subject": "1","question_count": "10","class_val": "3","uploadStatus":"Y","duration":"0","resultStatus":"Y","instructions":"","advance":"Y","negativeMarking":"0","test_type":"Class Feedback"},"custom_key": "custom_value","contact": {"phone": "9008262739"}}
        a = json.dumps(jsonExamData)
        z = json.loads(a)
        paramList = []
        conList = []
        print('data:')
        print(z)
        for data in z['results'].values():
                
            paramList.append(data)
            print('data:'+str(data))
        for con in z['contact'].values():
            conList.append(con)
        print(paramList)

        print(conList[2])
        print('Testing for topic')
        # print(type(paramList[1]))
        # print(int(paramList[1]))
            # 
        print('Data Contact')
        contactNo = conList[2][-10:]
        print(contactNo)
        studentData = StudentProfile.query.filter_by(phone=contactNo).first()
        teacherData = TeacherProfile.query.filter_by(user_id=studentData.user_id).first()
        schoolData = SchoolProfile.query.filter_by(school_id=teacherData.school_id).first()
        teacher_id = teacherData.teacher_id
        classData = ClassSection.query.filter_by(class_sec_id=studentData.class_sec_id).first()
        selClass = classData.class_val
        selSubject = paramList[13]
        subId = paramList[16]
        selChapter = paramList[19]
        print('Chapter'+str(selChapter))
        dateVal= datetime.today().strftime("%d%m%Y%H%M%S")
        fetchQuesIdsQuery = "select td.board_id,qd.suggested_weightage,qd.question_type,qd.question_id,qd.question_description,td.subject_id,td.topic_id from question_details qd "
        fetchQuesIdsQuery = fetchQuesIdsQuery + "inner join topic_detail td on qd.topic_id = td.topic_id "
        fetchQuesIdsQuery = fetchQuesIdsQuery + "inner join message_detail md on md.msg_id = td.subject_id "
        fetchQuesIdsQuery = fetchQuesIdsQuery + "where td.chapter_name like '%"+str(selChapter)+"%' and qd.archive_status='N' and qd.question_type='MCQ1' and md.description = '"+str(selSubject)+"' and td.class_val = '"+str(selClass)+"' limit '"+str(paramList[3])+"'"
        print('fetchQuesIds Query:'+str(fetchQuesIdsQuery))
        fetchQuesIds = db.session.execute(fetchQuesIdsQuery).fetchall()
        msg = 'No questions available'
        if len(fetchQuesIds)==0 or fetchQuesIds=='':
            return jsonify({'testId':msg})
        listLength = len(fetchQuesIds)
        total_marks = int(paramList[0]) * int(listLength)
        boardID = schoolData.board_id
        test_type = paramList[11]
        subjId = paramList[16]                
        file_name_val = paramList[21]
        school_id = paramList[17]
        teacher_id = paramList[15]
        resp_session_id = paramList[22]        
        format = "%Y-%m-%d %H:%M:%S"
        now_utc = datetime.now(timezone('UTC'))
        now_local = now_utc.astimezone(get_localzone())
        print('Date of test creation:'+str(now_local.strftime(format)))
        # classDet = ClassSection.query.filter_by(class_val=class_val,school_id=school_id).first()
        # class_sec_id = classDet.class_sec_id
        testDetailsUpd = TestDetails(test_type=str(test_type), total_marks=str(total_marks),last_modified_date= datetime.now(),
            board_id=str(boardID), subject_id=int(subjId),class_val=str(selClass),date_of_creation=now_local.strftime(format),
            date_of_test=datetime.now(), school_id=teacherData.school_id, teacher_id=teacher_id)
        db.session.add(testDetailsUpd)
        db.session.commit()
        file_name_val = url_for('downloadPaper',test_id=testDetailsUpd.test_id,_external=True)
        testDet = TestDetails.query.filter_by(test_id=testDetailsUpd.test_id).first()
        testDet.test_paper_link = file_name_val
        db.session.commit()
        sessionDetailRowInsert=SessionDetail(resp_session_id=resp_session_id,session_status='80',teacher_id= teacher_id,
            test_id=str(testDetailsUpd.test_id).strip(),class_sec_id=classData.class_sec_id,correct_marks=10,incorrect_marks=0, test_time=0,total_marks=total_marks, last_modified_date = str(now_local.strftime(format)))
        db.session.add(sessionDetailRowInsert)
        for questionVal in fetchQuesIds:
            testQuestionInsert= TestQuestions(test_id=testDetailsUpd.test_id, question_id=questionVal.question_id, last_modified_date=datetime.now(),is_archived='N')
            db.session.add(testQuestionInsert)
        db.session.commit()
        testId = testDetailsUpd.test_id 
        return jsonify({'testId':testId,'section':classData.section,'total_marks':total_marks})   
