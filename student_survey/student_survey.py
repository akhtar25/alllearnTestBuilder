from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, Response,session,jsonify
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime
from flask import g, jsonify
from sqlalchemy import func, distinct, text, update
student_survey= Blueprint('student_survey',__name__)

@student_survey.route('/studentSurveys')
def studentSurveys():
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    surveyDetailQuery = "select sd.survey_id, survey_name, question_count, count(ssr.student_id ) as student_responses, question_count, sd.last_modified_date "
    surveyDetailQuery = surveyDetailQuery+ "from survey_detail sd left join student_survey_response ssr on ssr.survey_id =sd.survey_id "
    surveyDetailQuery = surveyDetailQuery+" where sd.school_id ="+str(teacherRow.school_id)+ " and sd.is_archived='N' group by sd.survey_id,survey_name, question_count,question_count, sd.last_modified_date"
    surveyDetailRow = db.session.execute(surveyDetailQuery).fetchall()
    #surveyDetailRow = SurveyDetail.query.filter_by(school_id=teacherRow.school_id).all()
    indic='DashBoard'
    return render_template('studentSurveys.html',indic=indic,title='Student Surveys', surveyDetailRow=surveyDetailRow,user_type_val=str(current_user.user_type))

@student_survey.route('/indivSurveyDetail/')
def indivSurveyDetail():
    survey_id = request.args.get('survey_id')
    survey_id = survey_id.split('_')[1]
    student_id = request.args.get('student_id')    
    studSurveyData = " select sq.sq_id as sq_id, question,sq.survey_id,survey_response_id , sp.student_id, answer from student_survey_response ssr "
    studSurveyData = studSurveyData  + " right join survey_questions sq on "
    studSurveyData = studSurveyData  +  " sq.survey_id =ssr.survey_id and "
    studSurveyData = studSurveyData  +  " sq.sq_id =ssr.sq_id and ssr.student_id ="+ str(student_id)
    studSurveyData = studSurveyData  +  " left join student_profile sp "
    studSurveyData = studSurveyData  +  " on sp.student_id =ssr.student_id "
    studSurveyData = studSurveyData  +  " where sq.survey_id =" + str(survey_id)
    surveyQuestions = db.session.execute(text(studSurveyData)).fetchall()
    return render_template('_indivSurveyDetail.html',surveyQuestions=surveyQuestions,student_id=student_id,survey_id=survey_id)

@student_survey.route('/updateSurveyAnswer',methods=["GET","POST"])
def updateSurveyAnswer():
    sq_id_list = request.form.getlist('sq_id')
    survey_response_id_list = request.form.getlist('survey_response_id')
    answer_list = request.form.getlist('answer')
    survey_id = request.form.get('survey_id')
    student_id = request.form.get('student_id')
    for i in range(len(sq_id_list)):
        if survey_response_id_list[i]!='None':
            studentSurveyAnsUpdate = StudentSurveyResponse.query.filter_by(sq_id=sq_id_list[i], survey_response_id=survey_response_id_list[i]).first()
            studentSurveyAnsUpdate.answer = answer_list[i]
            surveyDetailRow = SurveyDetail.query.filter_by(survey_id=survey_id).first()            
        else:
            addNewSurveyResponse = StudentSurveyResponse(survey_id=survey_id, sq_id=sq_id_list[i], 
                student_id=student_id, answer=answer_list[i], last_modified_date=datetime.today())
            db.session.add(addNewSurveyResponse)
    db.session.commit()
    return jsonify(['0'])

@student_survey.route('/addNewSurvey',methods=["GET","POST"])
def addNewSurvey():    
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    questions = request.form.getlist('questionInput')
    questionCount = len(questions)
    newSurveyRow = SurveyDetail(survey_name=request.form.get('surveyName'),teacher_id= teacherRow.teacher_id, 
        school_id=teacherRow.school_id, question_count = questionCount, is_archived='N',last_modified_date=datetime.today())
    db.session.add(newSurveyRow)
    db.session.commit()
    currentSurvey = SurveyDetail.query.filter_by(teacher_id=teacherRow.teacher_id).order_by(SurveyDetail.last_modified_date.desc()).first()
    for i in range(questionCount):
        newSurveyQuestion= SurveyQuestions(survey_id=currentSurvey.survey_id, question=questions[i], is_archived='N',last_modified_date=datetime.today())
        db.session.add(newSurveyQuestion)
    db.session.commit()
    return jsonify(['0'])


@student_survey.route('/archiveSurvey')
def archiveSurvey():
    survey_id = request.args.get('survey_id')
    surveyData = SurveyDetail.query.filter_by(survey_id=survey_id).first()
    surveyData.is_archived='Y'
    db.session.commit()
    return jsonify(['0'])
#End of student survey section
