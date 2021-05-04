from flask import current_app as app
from student_profile.utils import *
from applicationDB import *
from flask import Blueprint, Markup, render_template, request, redirect, url_for, Response,session,jsonify
from applicationDB import *
from forms import LoginForm, RegistrationForm,ContentManager, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm,ResultQueryForm,MarksForm, TestBuilderQueryForm,SchoolRegistrationForm, PaymentDetailsForm, \
    SingleStudentRegistration, feedbackReportForm, testPerformanceForm, studentPerformanceForm, QuestionUpdaterQueryForm,  QuestionBankQueryForm,studentDirectoryForm, promoteStudentForm
from datetime import datetime
from flask import g, jsonify
from sqlalchemy import func, distinct, text, update
import string
from flask_login import login_required

student_profile= Blueprint('student_profile',__name__)

@student_profile.route('/studentProfileOld')
@login_required
def studentProfileOld():
    return render_template('studentProfile.html')


@student_profile.route('/allocateStudentToSponsor')
def allocateStudentToSponsor():
    student_id = request.args.get('student_id')
    sponsor_id = request.args.get('sponsor_id')
    sponsor_name = request.args.get('sponsor_name')
    amount = request.args.get('amount')

    studentData = StudentProfile.query.filter_by(student_id=student_id).first()
    studentData.sponsor_id = sponsor_id
    studentData.sponsor_name = sponsor_name
    studentData.sponsored_amount = amount
    studentData.sponsored_on = datetime.today()
    studentData.sponsored_status='Y'
    studentData.last_modified_date = datetime.today()
    db.session.commit()
    
    return jsonify(['0'])

@student_profile.route('/indivStudentProfile')
@login_required
def indivStudentProfile():    
    student_id=request.args.get('student_id')
    flag = request.args.get('flag')
    #spnsor data check
    sponsor_id = request.args.get('sponsor_id')
    sponsor_name = request.args.get('sponsor_name')
    amount = request.args.get('amount')
    
    #New updated query
    studentProfileQuery = "select full_name, email, sponsored_status,sponsored_on,sponsor_name,phone,sp.school_id as school_id, dob, md.description as gender,class_val, section, "
    studentProfileQuery = studentProfileQuery + "roll_number,school_adm_number,profile_picture,student_id from student_profile sp inner join "
    studentProfileQuery = studentProfileQuery + "class_section cs on sp.class_sec_id= cs.class_sec_id and sp.student_id='"+str(student_id)+"'" 
    studentProfileQuery = studentProfileQuery + "inner join message_detail md on md.msg_id =sp.gender "
    studentProfileQuery = studentProfileQuery + "left join address_detail ad on ad.address_id=sp.address_id"

    studentProfileRow = db.session.execute(text(studentProfileQuery)).first()  
    
    #performanceData
    performanceQuery = "SELECT * from vw_leaderboard WHERE student_id = '"+str(student_id)+ "'"    

    perfRows = db.session.execute(text(performanceQuery)).fetchall()
    
    testCountQuery = "select count(*) as testcountval from performance_detail where student_id='"+str(student_id)+ "'"

    testCount = db.session.execute(text(testCountQuery)).first() 

    testResultQuery = "select exam_date, t2.description as test_type, test_id, t3.description as subject, marks_scored, total_marks "
    testResultQuery = testResultQuery+ "from result_upload t1 inner join message_detail t2 on t1.test_type=t2.msg_id "
    testResultQuery = testResultQuery + "inner join message_detail t3 on t3.msg_id=t1.subject_id "
    testResultQuery = testResultQuery + " where student_id=%s order by exam_date desc" % student_id
    print(testResultQuery)
    testResultRows = db.session.execute(text(testResultQuery)).fetchall()
    
    onlineTestResultQuery = "select sd.last_modified_date,rc.resp_session_id,td.test_type,md.description , sum(marks_scored) as marks_scored,sd.total_marks from response_capture rc "
    onlineTestResultQuery = onlineTestResultQuery + "inner join session_detail sd on rc.resp_session_id=sd.resp_session_id "
    onlineTestResultQuery = onlineTestResultQuery + "inner join test_details td on sd.test_id = td.test_id "
    onlineTestResultQuery = onlineTestResultQuery + "inner join message_detail md on md.msg_id = rc.subject_id where rc.student_id='"+str(student_id)+"' "
    onlineTestResultQuery = onlineTestResultQuery + "group by rc.resp_session_id,sd.last_modified_date,sd.total_marks,td.test_type,md.description order by sd.last_modified_date desc "
    onlineTestResultRows = db.session.execute(text(onlineTestResultQuery)).fetchall()
    #Remarks info
    studentRemarksQuery = "select student_id, tp.teacher_id, teacher_name, profile_picture, remark_desc, sr.last_modified_date as last_modified_date"
    studentRemarksQuery= studentRemarksQuery+ " from student_remarks sr inner join teacher_profile tp on sr.teacher_id=tp.teacher_id and student_id="+str(student_id) + " "
    studentRemarkRows = db.session.execute(text(studentRemarksQuery)).fetchall()
    #studentRemarkRows = StudentRemarks.query.filter_by(student_id=student_id).order_by(StudentRemarks.last_modified_date.desc()).limit(5).all()

    #Sponsor allocation
    urlForAllocationComplete = str(app.config['IMPACT_HOST']) + '/responseStudentAllocate'
    overallSum = 0
    overallPerfValue = 0
    sumMarks = 0
    sum1 = 0
    sum2 = 0
    totalOfflineTestMarks = "select sum(marks_scored) as sum1 from result_upload ru where student_id = '"+str(student_id)+"'"
    print(totalOfflineTestMarks)
    totalOfflineTestMarks = db.session.execute(text(totalOfflineTestMarks)).first()
    if totalOfflineTestMarks.sum1:
        print(totalOfflineTestMarks.sum1)
        sum1 = totalOfflineTestMarks.sum1
    totalOnlineTestMarks = "select sum(student_score) as sum2 from performance_detail pd where student_id = '"+str(student_id)+"'"
    totalOnlineTestMarks = db.session.execute(text(totalOnlineTestMarks)).first()
    
    if totalOnlineTestMarks.sum2:
        print(totalOnlineTestMarks.sum2)
        sum2 = totalOnlineTestMarks.sum2
    sumMarks = int(sum1) + int(sum2)
    print('Total Marks:'+str(sumMarks))
    total1 = "select total_marks as offlineTotal from result_upload ru where student_id = '"+str(student_id)+"'"
    print(total1)
    total1 = db.session.execute(text(total1)).first()
    tot1 = 0
    if total1:
        print(total1.offlinetotal)
        tot1 = total1.offlinetotal
    total2 = "select count(*) as count from performance_detail pd where student_id = '"+str(student_id)+"'"
    total2 = db.session.execute(text(total2)).first()
    total3 = 0
    grandTotal = 0
    if total2.count:
        print(total2.count)
        total3 = total2.count*100
    grandTotal = int(tot1) + int(total3)
    print('Grand Total:'+str(grandTotal))
    for rows in perfRows:
        overallSum = overallSum + int(rows.student_score)
        #print(overallSum)
    try:
        overallPerfValue = round(sumMarks/(grandTotal)*100,2)    
    except:
        overallPerfValue=0    
    guardianRows = GuardianProfile.query.filter_by(student_id=student_id).all()
    qrRows = studentQROptions.query.filter_by(student_id=student_id).all()
    qrAPIURL = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data="    
    qrArray=[]
    x = range(4)    

    #section for fetching surveys
    try:
        surveyRows = SurveyDetail.query.filter_by(school_id=studentProfileRow.school_id,is_archived='N').all()
    except:
        surveyRows=[]
        print('survey error')

    for n in x:               
        if studentProfileRow!=None and studentProfileRow!="":
            optionURL = qrAPIURL+str(student_id)+ '-'+str(studentProfileRow.roll_number)+'-'+ studentProfileRow.full_name.replace(" ", "%20")+'@'+string.ascii_uppercase[n]
        else:
            optionURL=""
        qrArray.append(optionURL) 
        #print(optionURL)
    return render_template('_indivStudentProfile.html',surveyRows=surveyRows, studentRemarkRows=studentRemarkRows, urlForAllocationComplete=urlForAllocationComplete, studentProfileRow=studentProfileRow,guardianRows=guardianRows, 
        qrArray=qrArray,perfRows=perfRows,overallPerfValue=overallPerfValue,student_id=student_id,testCount=testCount,
        testResultRows = testResultRows,onlineTestResultRows=onlineTestResultRows,disconn=1, sponsor_name=sponsor_name, sponsor_id=sponsor_id,amount=amount,flag=flag)

@student_profile.route('/studentProfile') 
@login_required
def studentProfile():    
    qstudent_id=request.args.get('student_id')
    #####Section for sponsor data fetch
    qsponsor_name = request.args.get('sponsor_name')
    qsponsor_id = request.args.get('sponsor_id')
    qamount = request.args.get('amount')
    studentDetails = StudentProfile.query.filter_by(user_id = current_user.id).first()

    if qstudent_id==None or qstudent_id=='':
        form=studentDirectoryForm()
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        teacher= TeacherProfile.query.filter_by(user_id=user.id).first()    

        available_class=ClassSection.query.with_entities(ClassSection.class_val,ClassSection.section).distinct().order_by(ClassSection.class_val).filter_by(school_id=teacher.school_id).all()
        available_section=ClassSection.query.with_entities(ClassSection.section).distinct().filter_by(school_id=teacher.school_id).all()    
        available_test_type=MessageDetails.query.filter_by(category='Test type').all()
        # available_student_list=StudentProfile.query.filter_by(school_id=teacher.school_id).all()
        available_student_list = "select student_id,full_name,profile_picture,class_val, section from student_profile sp inner join class_section cs on sp.class_sec_id = cs.class_sec_id where cs.school_id ='"+str(teacher.school_id)+"'"
        available_student_list = db.session.execute(available_student_list).fetchall()
        
        class_list = classChecker(available_class)
        
        section_list=[(i.section,i.section) for i in available_section]    
        test_type_list=[(i.msg_id,i.description) for i in available_test_type]
        # student_list=[(i.student_id,i.full_name) for i in available_student_list]

        #selectfield choices
        print(class_list)
        form.class_section.choices = class_list
        # form.section1.choices= ''
        # section_list    
        # form.test_type1.choices=test_type_list
        form.student_name.choices = ''
        flag = 1
        indic='DashBoard'
        return render_template('studentProfileNew.html',indic=indic,title='Student Profile',form=form, sponsor_name=qsponsor_name, sponsor_id = qsponsor_id, amount = qamount,available_student_list=available_student_list,flag=flag,user_type_val=str(current_user.user_type),studentDetails=studentDetails)
    else:
        value=0
        flag = 0
        if current_user.user_type==72:
            value=1
        #print(qstudent_id)
        indic='DashBoard'
        return render_template('studentProfileNew.html',indic=indic,title='Student Profile',qstudent_id=qstudent_id,disconn=value, sponsor_name=qsponsor_name, sponsor_id = qsponsor_id, amount = qamount,flag=flag,user_type_val=str(current_user.user_type),studentDetails=studentDetails)
        flag = 0       
        #print(qstudent_id)
        indic='DashBoard'
        return render_template('studentProfileNew.html',indic=indic,title='Student Profile',qstudent_id=qstudent_id,disconn=disconn, sponsor_name=qsponsor_name, sponsor_id = qsponsor_id, amount = qamount,flag=flag, user_type_val=str(current_user.user_type),studentDetails=studentDetails)
