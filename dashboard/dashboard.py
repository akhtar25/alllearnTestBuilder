from flask import current_app as app
from dashboard.utils import *
from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, Response,session,jsonify
from applicationDB import *
from forms import LoginForm, RegistrationForm,ContentManager,LeaderBoardQueryForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm,ResultQueryForm,MarksForm, TestBuilderQueryForm,SchoolRegistrationForm, PaymentDetailsForm, addEventForm,QuestionBuilderQueryForm, SingleStudentRegistration, SchoolTeacherForm, feedbackReportForm, testPerformanceForm, studentPerformanceForm, QuestionUpdaterQueryForm,  QuestionBankQueryForm,studentDirectoryForm, promoteStudentForm
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime
from flask import g, jsonify
from sqlalchemy import distinct, text, update
from flask_cors import CORS
import pandas as pd
import plotly
import json


dashboard = Blueprint('dashboard',__name__)
CORS(dashboard)

@dashboard.route('/',methods=["GET","POST"])
@dashboard.route('/index')
@dashboard.route('/dashboard')
@login_required 
def index():
    print('Inside index')
    print("########This is the request url: "+str(request.url))
    print('current_user.id:'+str(current_user.id))
    teacherData = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    schoolData = ''
    if teacherData:
        schoolData = SchoolProfile.query.filter_by(school_admin=teacherData.teacher_id).first()
    if schoolData:
        if schoolData.is_verified == 'N':
            return redirect(url_for('school_details.inReviewSchool'))
    checkUser = User.query.filter_by(id=current_user.id).first()
    if checkUser:
        if checkUser.access_status == 143:
            return redirect(url_for('disconnectedAccount'))
    user = User.query.filter_by(username=current_user.username).first_or_404()        
    school_name_val = schoolNameVal()
    #print('User Type Value:'+str(user.user_type))
    teacher_id = TeacherProfile.query.filter_by(user_id=user.id).first() 
    
    school_id = SchoolProfile.query.filter_by(school_name=school_name_val).first()
    print('school_name_val:',school_name_val)
    if user.user_type==71:
        classExist = ClassSection.query.filter_by(school_id=school_id.school_id).first()
        #print('Insert new school')
        #print(classExist)
        if classExist==None:
            fromSchoolRegistration = True
       
            subjectValues = MessageDetails.query.filter_by(category='Subject').all()
            board = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
            boardRows = MessageDetails.query.filter_by(msg_id=board.board_id).first()
            school_id = SchoolProfile.query.filter_by(school_id=teacher_id.school_id).first()
            classValues = "SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id = '"+str(teacher_id.school_id)+"' GROUP BY class_val order by s"
            classValues = db.session.execute(text(classValues)).fetchall()
            classValuesGeneral = "SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs GROUP BY class_val order by s"
            classValuesGeneral = db.session.execute(text(classValuesGeneral)).fetchall()
            subjectValues = MessageDetails.query.filter_by(category='Subject').all()
            bookName = BookDetails.query.all()
            chapterNum = Topic.query.distinct().all()
            topicId = Topic.query.all()
            generalBoardId = SchoolProfile.query.filter_by(school_id = teacher_id.school_id).first()
            #print('teacher and board ids')
            #print(teacher_id.school_id)
            #print(generalBoardId.board_id)
            generalBoard = MessageDetails.query.filter_by(msg_id=generalBoardId.board_id).first()
            fromSchoolRegistration = True
            return render_template('syllabus.html',title='Syllabus',generalBoard=generalBoard,boardRowsId = boardRows.msg_id , boardRows=boardRows.description,subjectValues=subjectValues,school_name=school_id.school_name,classValues=classValues,classValuesGeneral=classValuesGeneral,bookName=bookName,chapterNum=chapterNum,topicId=topicId,fromSchoolRegistration=fromSchoolRegistration)
    #if user.user_type==135:
    #    return redirect(url_for('admin'))
    if user.user_type==234:
    #or ("prep.alllearn" in str(request.url)) or ("alllearnprep" in str(request.url))
        return redirect(url_for('practiceTest'))
    if user.user_type==253:
        return redirect(url_for('course.courseHome'))
    if user.user_type==72:
        #print('Inside guardian')
        return redirect(url_for('disconnectedAccount'))
    if user.user_type=='161':
        return redirect(url_for('job_post.openJobs'))
    if user.user_type==134 and user.access_status==145:        
        return redirect(url_for('disconnectedAccount'))

    teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    
    classSecCheckVal = classSecCheck()

    if school_name_val ==None:
        #print('did we reach here')
        return redirect(url_for('disconnectedAccount'))
    else:
    #####Fetch school perf graph information##########
        performanceQuery = "select * from fn_class_performance("+str(teacher.school_id)+") order by perf_date"
        performanceRows = db.session.execute(text(performanceQuery)).fetchall()
        if len(performanceRows)>0:
            df = pd.DataFrame( [[ij for ij in i] for i in performanceRows])
            df.rename(columns={0: 'Date', 1: 'Class_1', 2: 'Class_2', 3: 'Class_3', 4:'Class_4',
                5:'Class_5', 6:'Class_6', 7:'Class_7', 8:'Class_8', 9:'Class_9', 10:'Class_10'}, inplace=True)
            #print(df)
            dateRange = list(df['Date'])
            class1Data= list(df['Class_1'])
            class2Data= list(df['Class_2'])
            class3Data= list(df['Class_3'])
            class4Data= list(df['Class_4'])
            class5Data= list(df['Class_5'])
            class6Data= list(df['Class_6'])
            class7Data= list(df['Class_7'])
            class8Data= list(df['Class_8'])
            class9Data= list(df['Class_9'])
            class10Data= list(df['Class_10'])
            #print(dateRange)
            ##Class 1
            graphData = [dict(
                data1=[dict(y=class1Data,x=dateRange,type='scatter', name='Class 1')],
                data2=[dict(y=class2Data,x=dateRange,type='scatter', name='Class 2')],
                data3=[dict(y=class3Data,x=dateRange,type='scatter', name='Class 3')],
                data4=[dict(y=class4Data,x=dateRange,type='scatter', name='Class 4')],
                data5=[dict(y=class5Data,x=dateRange,type='scatter', name='Class 5')],
                data6=[dict(y=class6Data,x=dateRange,type='scatter', name='Class 6')],
                data7=[dict(y=class7Data,x=dateRange,type='scatter', name='Class 7')],
                data8=[dict(y=class8Data,x=dateRange,type='scatter', name='Class 8')],
                data9=[dict(y=class9Data,x=dateRange,type='scatter', name='Class 9')],
                data10=[dict(y=class10Data,x=dateRange,type='scatter', name='Class 10')]
                )]        
            #print(graphData)

            graphJSON = json.dumps(graphData, cls=plotly.utils.PlotlyJSONEncoder)
        else:
            graphJSON="1"
    #####Fetch Top Students infor##########        
        # topStudentsQuery = "select *from fn_monthly_top_students("+str(teacher.school_id)+",8)"
        qclass_val = 'dashboard'
        topStudentsRows = ''
        leaderBoardData = leaderboardContent(qclass_val)
        # print('leaderBoard Data:'+str(leaderBoardData))
        # Convert dataframe to a list
        data = []
        #print(type(leaderBoardData))
        column_names = ["a", "b", "c"] 
        datafr = pd.DataFrame(columns = column_names)
        if type(leaderBoardData)==type(datafr):
            #print('if data is not empty')
            df1 = leaderBoardData[['studentid','profile_pic','student_name','class_val','section','total_marks%','total_tests']]
            df2 = leaderBoardData.drop(['profile_pic', 'student_name','class_val','section','total_marks%','total_tests'], axis=1)
            leaderBoard = pd.merge(df1,df2,on=('studentid'))
                
            d = leaderBoard[['studentid','profile_pic','student_name','class_val','section','total_marks%','total_tests']]
            df3 = leaderBoard.drop(['studentid'],axis=1)
            
            df1.rename(columns = {'profile_pic':'Profile Picture'}, inplace = True)
            df1.rename(columns = {'student_name':'Student'}, inplace = True)
            df1.rename(columns = {'class_val':'Class'}, inplace = True)
            df1.rename(columns = {'section':'Section'}, inplace = True)
            df1.rename(columns = {'total_marks%':'Total Marks'}, inplace = True)
            df1.rename(columns = {'total_tests':'Total Tests'}, inplace = True)
            header = [df1.columns.values.tolist()]
            headerAll = [df3.columns.values.tolist()]
            colAll = ''
            subjHeader = [df2.columns.values.tolist()]
            columnNames = ''
            col = ''
            subColumn = ''
            for subhead in subjHeader:
                subColumn = subhead
            for h in header:
                columnNames = h
            for headAll in headerAll: 
                colAll = headAll
            n= int(len(subColumn)/2)
            ndf = df2.drop(['studentid'],axis=1)
            newDF = ndf.iloc[:,0:n]
            new1DF = ndf.iloc[:,n:]
                
            df5 = pd.concat([newDF, new1DF], axis=1)
            DFW = df5[list(sum(zip(newDF.columns, new1DF.columns), ()))]
            
            
            dat = pd.concat([d,DFW], axis=1)
                
            dat = dat.sort_values('total_marks%',ascending=False)  
            
            subHeader = ''
            i=1
            for row in dat.values.tolist():
                if i<9:
                    data.append(row)
                i=i+1
        form  = promoteStudentForm() 
        available_class=ClassSection.query.with_entities(ClassSection.class_val,ClassSection.section).distinct().order_by(ClassSection.class_val,ClassSection.section).filter_by(school_id=teacher.school_id).all()
        class_list=[(str(i.class_val)+"-"+str(i.section),str(i.class_val)+"-"+str(i.section)) for i in available_class]
        
        form.class_section1.choices = class_list 
        form.class_section2.choices = class_list 
        
        EventDetailRows = EventDetail.query.filter_by(school_id=teacher.school_id).all()
    #####Fetch Course Completion infor##########    
        topicToCoverQuery = "select *from fn_topic_tracker_overall("+str(teacher.school_id)+") order by class, section"
        topicToCoverDetails = db.session.execute(text(topicToCoverQuery)).fetchall()
        #print(topicToCoverDetails)

    ##################Fetch Job post details################################
        jobPosts = JobDetail.query.filter_by(school_id=teacher.school_id).order_by(JobDetail.posted_on.desc()).all()
        teacherCount = "select count(*) from teacher_profile tp where school_id = '"+str(teacher.school_id)+"'"
        teacherCount = db.session.execute(teacherCount).first()
        studentCount = "select count(*) from student_profile sp where school_id = '"+str(teacher.school_id)+"'"
        studentCount = db.session.execute(studentCount).first()
        testCount = "select (select count(distinct upload_id) from result_upload ru where school_id = '"+str(teacher.school_id)+"') + "
        testCount = testCount + "(select count(distinct resp_session_id) from response_capture rc2 where school_id = '"+str(teacher.school_id)+"') as SumCount"
        #print(testCount)
        testCount = db.session.execute(testCount).first()
        lastWeekTestCount = "select (select count(distinct upload_id) from result_upload ru where school_id = '"+str(teacher.school_id)+"' and last_modified_date >=current_date - 7) + "
        lastWeekTestCount = lastWeekTestCount + "(select count(distinct resp_session_id) from response_capture rc2 where school_id = '"+str(teacher.school_id)+"' and last_modified_date >=current_date - 7) as SumCount "
        #print(lastWeekTestCount)
        lastWeekTestCount = db.session.execute(lastWeekTestCount).first()
        #print('user type value')
        #print(session['moduleDet'])
        query = "select user_type,md.module_name,description, module_url from module_detail md inner join module_access ma on md.module_id = ma.module_id where user_type = '"+str(current_user.user_type)+"'"
        moduleDetRow = db.session.execute(query).fetchall()
        return render_template('dashboard.html',form=form,title='Home Page',school_id=teacher.school_id, jobPosts=jobPosts,
            graphJSON=graphJSON, classSecCheckVal=classSecCheckVal,topicToCoverDetails = topicToCoverDetails, EventDetailRows = EventDetailRows, topStudentsRows = data,teacherCount=teacherCount,studentCount=studentCount,testCount=testCount,lastWeekTestCount=lastWeekTestCount)


@dashboard.route('/applicationTracking',methods=['GET','POST'])
def applicationTracking():
    data = request.headers.get('Authorization')
    print(data)
    decode  = jwt.decode(data,'you-will-never-guess')
    print(decode['user'])
    user = User.query.filter_by(email=decode['user']).first()
    jobPosts = JobDetail.query.filter_by(school_id=user.school_id).order_by(JobDetail.posted_on.desc()).all()
    jobPostDataList = []
    for jobPostRow in jobPosts:
        jobPost = {}
        jobPost['posted_on'] = jobPostRow.posted_on
        jobPost['subject'] = jobPostRow.subject
        jobPost['classes'] = jobPostRow.classes
        jobPost['category'] = jobPostRow.category
        jobPost['status'] = jobPostRow.status
        jobPost['term'] = jobPostRow.term
        jobPost['school_id'] = jobPostRow.school_id
        jobPost['job_id'] = jobPostRow.job_id
        jobPostDataList.append(jobPost)
    return jsonify({'jobTracking':jobPostDataList})

@dashboard.route('/performanceChart',methods=['GET','POST'])
def performanceChart():
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    query = "Select * from fn_overall_performance_summary('"+str(teacher_id.school_id)+"') where class='All'and section='All' and subject='All'"
    
    resultSet = db.session.execute(text(query)).fetchall()
    
    resultArray = []
    if resultSet:
        for result in resultSet:
            Array = {}
            Array['avg_score'] = str(round(result.avg_score,2))
            Array['highest_mark'] = str(result.highest_mark)
            Array['lowest_mark'] = str(result.lowest_mark)
            Array['no_of_students_above_90'] = str(result.no_of_students_above_90)
            Array['no_of_students_80_90'] = str(result.no_of_students_80_90)
            Array['no_of_students_70_80'] = str(result.no_of_students_70_80)
            Array['no_of_students_50_70'] = str(result.no_of_students_50_70)
            Array['no_of_students_below_50'] = str(result.no_of_students_below_50)
            Array['no_of_students_cross_50'] = str(result.no_of_students_cross_50)
            resultArray.append(Array)
        return {'result' : resultArray} 
    else:
        return jsonify(["NA"])

@dashboard.route('/performanceBarChart',methods=['GET','POST'])
def performanceBarChart():
    teacher_id = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_v = request.args.get('class_val')
    section = request.args.get('section')
    classSection = ClassSection.query.with_entities(ClassSection.class_sec_id).filter_by(class_val=class_v,section=section,school_id=str(teacher_id.school_id)).first()
    subject = "select distinct subject_id from topic_detail where class_val= '"+str(class_v)+"'"
    totalStudent = "select count(*) from student_profile where class_sec_id='"+str(classSection.class_sec_id)+"' and school_id='"+str(teacher_id.school_id)+"'"
    #print(totalStudent)
    totalStudent = db.session.execute(totalStudent).first()
    subject_id = db.session.execute(subject).fetchall()
    performance_array = []
    for sub in subject_id:
        pass_count = "select count(*) from student_profile sp where student_id in (select studentid from fn_performance_leaderboard_detail_v1('"+str(teacher_id.school_id)+"') pd where class ='"+str(class_v)+"' and section='"+str(section)+"' and subjectid='"+str(sub.subject_id)+"' and marks>50)"
        fail_count = "select count(*) from student_profile sp where student_id in (select studentid from fn_performance_leaderboard_detail_v1('"+str(teacher_id.school_id)+"') pd where class ='"+str(class_v)+"' and section='"+str(section)+"' and subjectid='"+str(sub.subject_id)+"' and marks<=50)"
        #print('pass and fail count:')
        #print(pass_count)
        #print(fail_count)
        passStudents = db.session.execute(pass_count).first()
        failStudents = db.session.execute(fail_count).first()
        presentStudents = passStudents[0] + failStudents[0]
        absentStudents = totalStudent[0] - presentStudents
        #print(absentStudents)
        if absentStudents==totalStudent[0]:
            absentStudents = 0
        #print((passStudents[0]))
        #print((failStudents[0]))
        Array = {}
        Array['pass_count'] = str(passStudents[0])
        Array['fail_count'] = str(failStudents[0])
        Array['absent_students'] = str(absentStudents)
        subjectName = MessageDetails.query.with_entities(MessageDetails.description).filter_by(msg_id=sub.subject_id).first()
        Array['description'] = str(subjectName.description)
        performance_array.append(Array)
    return {'performance':performance_array}

@dashboard.route('/addEvent', methods = ["GET","POST"])
@login_required
def addEvent():        
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    form = addEventForm()
    if form.validate_on_submit():
        dataForEntry = EventDetail(event_name=form.eventName.data, event_duration=form.duration.data,event_date=form.eventDate.data,event_start=form.startDate.data,event_end=form.endDate.data,event_category=form.category.data,school_id=teacher_id.school_id, last_modified_date=datetime.today())                
        db.session.add(dataForEntry)
        db.session.commit()
        flash('Event Added!')
    indic='DashBoard'
    return render_template('addEvent.html',indic=indic, form=form,title='Add Event')
