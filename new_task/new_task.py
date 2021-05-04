from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, Response,session,jsonify
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime
from flask import jsonify
from sqlalchemy import func, distinct, text, update
from urllib.request import urlopen,Request
from urllib.parse import quote,urlparse, parse_qs


new_task = Blueprint('new_task',__name__)

@new_task.route('/studentHomeWork')
@login_required
def studentHomeWork():
    user_type = current_user.user_type
    if user_type==134:
        user_id = User.query.filter_by(id=current_user.id).first()
        student_id = StudentProfile.query.filter_by(user_id=user_id.id).first()
        print('class_sec_id:'+str(student_id.class_sec_id))
        homeworkDetailQuery = "select sd.homework_id, homework_name, question_count, sd.last_modified_date,count(ssr.answer) as ans_count "
        homeworkDetailQuery = homeworkDetailQuery+ "from homework_detail sd left join student_homework_response ssr on ssr.homework_id =sd.homework_id "
        homeworkDetailQuery = homeworkDetailQuery+" where sd.school_id ="+str(student_id.school_id)+ " and sd.is_archived='N' and sd.class_sec_id='"+str(student_id.class_sec_id)+"' group by sd.homework_id,homework_name,question_count, sd.last_modified_date"
        homeworkDetailQuery = homeworkDetailQuery+" order by sd.last_modified_date desc"
        print(homeworkDetailQuery)
        homeworkData = db.session.execute(homeworkDetailQuery).fetchall()
        print('student_id:'+str(student_id.student_id))
        studentDetails = StudentProfile.query.filter_by(user_id=current_user.id).first()  
        indic='homework'
    return render_template('studentHomeWork.html',indic=indic,student_id=student_id.student_id,homeworkData=homeworkData,user_type_val=str(current_user.user_type), studentDetails=studentDetails)

@new_task.route('/HomeWork')
@login_required
def HomeWork():
    qclass_val = request.args.get('class_val')
    qsection=request.args.get('section')
    teacherRow = ''
    if current_user.user_type==134:
        teacherRow = StudentProfile.query.filter_by(user_id=current_user.id).first()        
    else:
        teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    classSections=ClassSection.query.filter_by(school_id=teacherRow.school_id).all()
    count = 0
    for section in classSections:
        print("Class Section:"+section.section)
            #this section is to load the page for the first class section if no query value has been provided
        if count==0:
            getClassVal = section.class_val
            getSection = section.section
            count+=1
    if qclass_val is None:
        qclass_val = getClassVal
        qsection = getSection
    
    class_sec_id = ClassSection.query.filter_by(school_id=teacherRow.school_id,class_val=qclass_val,section=qsection).first()
    homeworkDetailQuery = "select sd.homework_id, homework_name, question_count, count(ssr.student_id ) as student_responses, question_count, sd.last_modified_date "
    homeworkDetailQuery = homeworkDetailQuery+ "from homework_detail sd left join student_homework_response ssr on ssr.homework_id =sd.homework_id "
    homeworkDetailQuery = homeworkDetailQuery+" where sd.school_id ="+str(teacherRow.school_id)+ " and sd.is_archived='N' and sd.class_sec_id='"+str(class_sec_id.class_sec_id)+"' group by sd.homework_id,homework_name, question_count,question_count, sd.last_modified_date"
    homeworkDetailQuery = homeworkDetailQuery+" order by sd.last_modified_date desc"
    print(homeworkDetailQuery)
    homeworkDetailRow = db.session.execute(homeworkDetailQuery).fetchall()
    #surveyDetailRow = SurveyDetail.query.filter_by(school_id=teacherRow.school_id).all()
    distinctClasses = db.session.execute(text("SELECT  distinct class_val,sum(class_sec_id),count(section) as s FROM class_section cs where school_id="+ str(teacherRow.school_id)+" GROUP BY class_val order by s")).fetchall() 
    classSections=ClassSection.query.filter_by(school_id=teacherRow.school_id).all()
    indic='DashBoard'
    return render_template('HomeWork.html',indic=indic,title='Homework', homeworkDetailRow=homeworkDetailRow,distinctClasses=distinctClasses,classSections=classSections,qclass_val=qclass_val,qsection=qsection,user_type_val=str(current_user.user_type))

@new_task.route('/homeworkReview')
@login_required
def homeworkReview():
    homework_id = request.args.get('homework_id')
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #homeworkRevData = "select *from fn_student_homework_status("+str(teacherRow.school_id)+","+str(homework_id)+")"
    homeworkRevData = "select sp.full_name as student_name, sp.student_id ,count(answer) as ans_count,hd.question_count as qcount,hd.homework_id from student_homework_response shr inner join student_profile sp "
    homeworkRevData = homeworkRevData + "on sp.student_id = shr.student_id inner join homework_detail hd on hd.homework_id = shr.homework_id "
    homeworkRevData = homeworkRevData + "where sp.school_id = '"+str(teacherRow.school_id)+"' and shr.homework_id='"+str(homework_id)+"' group by student_name , qcount, sp.student_id, hd.homework_id"
    homeworkRevData = db.session.execute(text(homeworkRevData)).fetchall()    
    homework_name = HomeWorkDetail.query.filter_by(homework_id=homework_id).first()
    classSections=ClassSection.query.filter_by(school_id=teacherRow.school_id,class_sec_id=homework_name.class_sec_id ).first()
    return render_template('homeworkReview.html',homeworkRevData=homeworkRevData,class_val=classSections.class_val,section=classSections.section,homework_name=homework_name.homework_name,homework_id=homework_id)

@new_task.route('/indivHomeworkReview',methods=['GET','POST'])
@login_required
def indivHomeworkReview():
    homework_id = request.args.get('homework_id') 
    student_id = request.args.get('student_id')
    #homework_id = HomeWorkDetail.query.filter_by(homework_id=homework_id).first()
    #reviewData = "select  hq.sq_id as sq_id, hq.question,hq.ref_type,hq.ref_url,shr.answer,shr.teacher_remark as teacher_remark from homework_questions hq left join student_homework_response shr "
    #reviewData = reviewData + "on hq.homework_id = shr.homework_id and hq.sq_id =shr.sq_id where hq.homework_id = '"+str(homework_id.homework_id)+"'"
    reviewData = "select  hq.sq_id as sq_id, hq.question,hq.ref_type,hq.ref_url,shr.answer,shr.teacher_remark as teacher_remark "
    #from homework_questions hq left join student_homework_response shr "
    #reviewData = reviewData + "on hq.homework_id = shr.homework_id and hq.sq_id =shr.sq_id where hq.homework_id = '"+str(homework_id.homework_id)+"'"
    reviewData = reviewData + " from homework_detail hd inner join homework_questions hq on "
    reviewData = reviewData + " hd.homework_id = hq.homework_id and hd.homework_id =" + str(homework_id)
    reviewData = reviewData + " left join student_homework_response shr on "
    reviewData = reviewData + " hq.sq_id =shr.sq_id and shr.student_id = " + str(student_id)
    reviewData = reviewData + " and shr.homework_response_id in (select min(homework_response_id )from student_homework_response shr "
    reviewData = reviewData + " where student_id ="+ str(student_id) +" and homework_id ="+ str(homework_id) +" group by sq_id ) "
    #print(reviewData)
    reviewData = db.session.execute(text(reviewData)).fetchall()    
    return render_template('_indivHomeWorkReview.html',reviewData=reviewData,student_id=student_id)

@new_task.route('/indivHomeworkDetail',methods=['GET','POST'])
@login_required
def indivHomeWorkDetail():
    homework_id = request.args.get('homework_id') 
    user_id = User.query.filter_by(id=current_user.id).first()
    student_id = StudentProfile.query.filter_by(user_id=user_id.id).first()
    homework_name = HomeWorkDetail.query.filter_by(homework_id=homework_id).first()
    #homeworkQuestions = HomeWorkQuestions.query.filter_by(homework_id=homework_id).all()

    #homeworkDataQQuery = " select distinct hq.sq_id as sq_id, question,hq.homework_id ,ref_type, ref_url, homework_response_id , sp.student_id, answer,teacher_remark from student_homework_response shr "
    #homeworkDataQQuery = homeworkDataQQuery + "right join homework_questions hq on "
    #homeworkDataQQuery = homeworkDataQQuery +  "hq.homework_id =shr.homework_id and "
    #homeworkDataQQuery = homeworkDataQQuery +  "hq.sq_id =shr.sq_id and shr.student_id = "+ str(student_id.student_id)
    #homeworkDataQQuery = homeworkDataQQuery +  " left join student_profile sp "
    #homeworkDataQQuery = homeworkDataQQuery +  "on sp.student_id =shr.student_id where hq.homework_id ="+ str(homework_id)
    #homeworkDataQQuery = homeworkDataQQuery +  " and homework_response_id in "
    #homeworkDataQQuery = homeworkDataQQuery +  " (select min(homework_response_id )from student_homework_response shr "
    #homeworkDataQQuery = homeworkDataQQuery +  " where student_id ="+ str(student_id.student_id) + " and homework_id ="+ str(homework_id) +" group by sq_id ) "
    homeworkDataQQuery = "select distinct hq.sq_id as sq_id, question,hq.homework_id ,ref_type, ref_url, homework_response_id , shr.student_id, answer,teacher_remark "
    homeworkDataQQuery = homeworkDataQQuery +  " from homework_detail hd inner join homework_questions hq "
    homeworkDataQQuery = homeworkDataQQuery +  " on hd.homework_id = hq.homework_id and hd.homework_id =" + str(homework_id)
    homeworkDataQQuery = homeworkDataQQuery +  " left join student_homework_response shr on "
    homeworkDataQQuery = homeworkDataQQuery +  " hq.sq_id =shr.sq_id and shr.student_id =" + str(student_id.student_id)
    homeworkDataQQuery = homeworkDataQQuery +  " and shr.homework_response_id in (select min(homework_response_id )from student_homework_response shr "
    homeworkDataQQuery = homeworkDataQQuery +  " where student_id ="+ str(student_id.student_id) +" and homework_id ="+ str(homework_id) +" group by sq_id )"

    print(homeworkDataQQuery)
    homeworkDataRows = db.session.execute(text(homeworkDataQQuery)).fetchall()
    homeworkAttach = db.session.execute(text("select attachment from homework_detail where homework_id='"+str(homework_id)+"'")).first()
    return render_template('_indivHomeWorkDetail.html',homeworkDataRows=homeworkDataRows,homework_name=homework_name,homework_id=homework_id,student_id=student_id,homeworkAttach=homeworkAttach)

@new_task.route('/addAnswerRemark',methods=["GET","POST"])
def addAnswerRemark():
    remark = request.form.getlist('remark')
    student_id = request.args.get('student_id')
    sq_id_list = request.form.getlist('sq_id')
    print('######'+str(len(sq_id_list) ))
    for i in range(len(sq_id_list)):
        remarkData = StudentHomeWorkResponse.query.filter_by(student_id=student_id,sq_id= sq_id_list[i]).first()  

        print('################################e   entered remark section')
        print(str(StudentHomeWorkResponse.query.filter_by(student_id=student_id,sq_id= sq_id_list[i])))
        if remarkData!=None:            
            remarkData.teacher_remark = remark[i]
    db.session.commit()
    return jsonify(['0'])

checkValue = ''
@new_task.route('/addHomeworkAnswer',methods=["GET","POST"])
def addHomeworkAnswer():
    sq_id_list = request.form.getlist('sq_id')
    answer_list = request.form.getlist('answer')
    homework_id = request.form.get('homework_id')
    print('add homework answer')
    user_id = User.query.filter_by(id=current_user.id).first()
    student_id = StudentProfile.query.filter_by(user_id=user_id.id).first()
    for i in range(len(sq_id_list)):
        checkStudentReponse = StudentHomeWorkResponse.query.filter_by(student_id=student_id.student_id,sq_id=sq_id_list[i]).first()
        if checkStudentReponse==None or checkStudentReponse=="":
            addNewHomeWorkResponse = StudentHomeWorkResponse(homework_id=homework_id, sq_id=sq_id_list[i], 
                student_id=student_id.student_id, answer=answer_list[i], last_modified_date=datetime.today())
            db.session.add(addNewHomeWorkResponse)
            print("Not present")
        else:
            return jsonify(['1'])
        #    checkStudentReponse.answer=answer_list[i]
        #    print("Already present")
    db.session.commit()
    return jsonify(['0'])


def get_yt_video_id(url):
    """Returns Video_ID extracting from the given url of Youtube
    
    Examples of URLs:
      Valid:
        'http://youtu.be/_lOT2p_FCvA',
        'www.youtube.com/watch?v=_lOT2p_FCvA&feature=feedu',
        'http://www.youtube.com/embed/_lOT2p_FCvA',
        'http://www.youtube.com/v/_lOT2p_FCvA?version=3&amp;hl=en_US',
        'https://www.youtube.com/watch?v=rTHlyTphWP0&index=6&list=PLjeDyYvG6-40qawYNR4juzvSOg-ezZ2a6',
        'youtube.com/watch?v=_lOT2p_FCvA',
      
      Invalid:
        'youtu.be/watch?v=_lOT2p_FCvA',
    """
    

    if url.startswith(('youtu', 'www')):
        url = 'http://' + url
    embeddingURL = "https://www.youtube.com/embed/"
    query = urlparse(url)
    
    if 'youtube' in query.hostname:
        if query.path == '/watch':
            return "96", embeddingURL + parse_qs(query.query)['v'][0]
        elif query.path.startswith(('/embed/', '/v/')):
            return "96",embeddingURL + query.path.split('/')[2]
    elif 'youtu.be' in query.hostname:
        return "96",embeddingURL + query.path[1:]
    else:
        return "97",url


def checkContentType(contentName):
    with urlopen(contentName) as response:
        info = response.info()
        contentTypeVal = info.get_content_type()
        splittedContentType = contentTypeVal.split('/')
        if splittedContentType[1]=='pdf' or splittedContentType[1]=='msword':
            return "99"
        elif splittedContentType[0]=='audio':
            return "97"
        elif splittedContentType[1]=='image':
            return "98"
        else:
            return "227"


@new_task.route('/addNewHomeWork',methods=["GET","POST"])
def addNewHomeWork():     
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    questions = request.form.getlist('questionInput')
    #contentType = request.form.getlist('contentType')
    contentName = request.form.getlist('contentName')
    homeworkContent = request.form.get('homeworkContent')
    print('inside addNew Homework')
    print(homeworkContent)
    for i in range(len(contentName)):
        print(contentName[i])
    #for i in range(len(contentType)):
    #    print('content type:'+str(contentType[i]))
    questionCount = len(questions)
    class_val = request.form.get('class')
    section = request.form.get('section')
    class_sec_id = ClassSection.query.filter_by(school_id=teacherRow.school_id,class_val=class_val,section=section).first()
    newHomeWorkRow = HomeWorkDetail(homework_name=request.form.get('homeworkName'),teacher_id= teacherRow.teacher_id, 
        school_id=teacherRow.school_id, question_count = questionCount, is_archived='N',class_sec_id=class_sec_id.class_sec_id,last_modified_date=datetime.today(),attachment=homeworkContent)
    db.session.add(newHomeWorkRow)
    db.session.commit()
    currentHomeWork = HomeWorkDetail.query.filter_by(teacher_id=teacherRow.teacher_id).order_by(HomeWorkDetail.last_modified_date.desc()).first()
        
    for i in range(questionCount):           
        if contentName[i] !='':               
            refType ,contentName[i] = get_yt_video_id(contentName[i])
            if refType!=96:
                refType= checkContentType(contentName[i])                
        else:
            refType=226
        newHomeWorkQuestion= HomeWorkQuestions(homework_id=currentHomeWork.homework_id, question=questions[i], is_archived='N',last_modified_date=datetime.today(),ref_type=int(refType),ref_url=contentName[i])
        db.session.add(newHomeWorkQuestion)
    db.session.commit()
    return jsonify(['0:'+ str(currentHomeWork.homework_id)])






@new_task.route('/archiveHomeWork')
def archiveHomeWork():
    homework_id = request.args.get('homework_id')
    homeworkData = HomeWorkDetail.query.filter_by(homework_id=homework_id).first()
    homeworkData.is_archived='Y'
    db.session.commit()
    return jsonify(['0'])