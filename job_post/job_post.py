from job_post.utils import *
from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, Response,session,jsonify
from send_email import new_teacher_invitation,new_applicant_for_job, application_processed, job_posted_email, send_notification_email
from applicationDB import *
from forms import createSubscriptionForm,ClassRegisterForm,postJobForm, AddLiveClassForm
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from datetime import date
from datetime import datetime
from flask import g, jsonify
from forms import PostForm
from applicationDB import Post
from sqlalchemy import func, distinct, text, update


job_post = Blueprint('job_post',__name__)

@job_post.route('/postJob',methods=['POST','GET'])
@login_required
def postJob():
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    schoolCityQuery = "select city from address_detail where address_id =(select address_id from school_profile where school_id ="+str(teacherRow.school_id)+")"
    schoolCity = db.session.execute(text(schoolCityQuery)).first()
    form = postJobForm()
    
    availableCategories=MessageDetails.query.filter_by(category='Job Category').all()
    availableJobTypes=MessageDetails.query.filter_by(category='Job Type').all()
    availableStayOptions=MessageDetails.query.filter_by(category='Stay Option').all()
    availableFoodOptions=MessageDetails.query.filter_by(category='Food Option').all()
    availableTeachingTermOption=MessageDetails.query.filter_by(category='Teaching Term Option').all()

    form.category.choices = [(str(i.description),str(i.description)) for i in availableCategories]
    form.job_type.choices = [(str(i.description),str(i.description)) for i in availableJobTypes]
    form.stay.choices = [(str(i.description),str(i.description)) for i in availableStayOptions]
    form.food.choices = [(str(i.description),str(i.description)) for i in availableFoodOptions]
    form.term.choices = [(str(i.description),str(i.description)) for i in availableTeachingTermOption]


    if request.method == 'POST' and form.validate():
        jobData=JobDetail(category=form.category.data,
            posted_by =teacherRow.teacher_id,school_id=teacherRow.school_id,description=form.description.data,min_pay=form.min_pay.data,max_pay=form.max_pay.data,
            start_date=form.start_date.data,subject=form.subject.data, 
            classes= form.classes.data, language= form.language.data,timings= form.timings.data,stay= form.stay.data, 
            fooding= form.food.data,term= form.term.data,status='Open',num_of_openings=form.num_of_openings.data,city =schoolCity.city,
            job_type =form.job_type.data,posted_on = datetime.today(),last_modified_date= datetime.today())
        db.session.add(jobData)
        db.session.commit()
        flash('New job posted created!')
        try:
            job_posted_email(teacherRow.email,teacherRow.teacher_name,form.category.data)
        except:
            pass
    else:
        #flash('Please fix the errors to submit')
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                print(err)
    indic='DashBoard'
    return render_template('postJob.html',indic=indic,title='Post Job',form=form,classSecCheckVal=classSecCheck())


@job_post.route('/openJobs')
def openJobs():
    page=request.args.get('page',0, type=int)    
    first_login = request.args.get('first_login','0').strip()
    jobTermOptions = MessageDetails.query.filter_by(category='Teaching Term Option').all()
    jobTypeOptions = MessageDetails.query.filter_by(category='Job Type').all()
    # print('User value in openJobs:'+str(user_type_val))
    if first_login=='1':
        
        print('this is the first login section')
        userRecord = User.query.filter_by(id=current_user.id).first() 
        userRecord.user_type= '161'
        db.session.commit()
        flash('Please complete your profile before applying for jobs')
        return redirect('edit_profile')
    else:
        print('first login not registered')
        if current_user.is_anonymous:
            return render_template('openJobs.html',title='Look for Jobs',first_login=first_login,jobTermOptions=jobTermOptions,jobTypeOptions=jobTypeOptions)
        else:
            return render_template('openJobs.html',title='Look for Jobs',first_login=first_login,jobTermOptions=jobTermOptions,jobTypeOptions=jobTypeOptions,user_type_val=str(current_user.user_type))


@job_post.route('/openJobsFilteredList')
def openJobsFilteredList():
    page=request.args.get('page',0, type=int)
    recordsOnPage = 5
    offsetVal = page *recordsOnPage
    
    whereClause = ""
    qjob_term = request.args.get('job_term') #all /short term / long term
    qjob_type = request.args.get('job_type') #all /part time/ full time
    qcity =  request.args.get('city')       # all/ home city
   
    print("qterm is "+str(qjob_term))
    print("qtype is "+str(qjob_type))
    print("qcity is "+str(qcity))

    whJobTerm=''
    whJobType=''
    whCity=''

    if qjob_term=='All' or qjob_term==None or qjob_term=='':
        whJobTerm=None
    else:
        whJobTerm=" t1.term=\'"+str(qjob_term)+"\'"
        whereClause = 'where ' + whJobTerm

    
    if qjob_type=='All' or qjob_type==None or qjob_type=='':
        whJobType=None
    else:
        whJobType=" t1.job_type=\'"+str(qjob_type)+"\'"
        if whereClause=='':
            whereClause = 'where '+whJobType
        else:
            whereClause =  whereClause + ' and '+whJobType
    
    if qcity=='All' or qcity==None or qcity=='':
        whCity=None
    else:
        whCity=" t1.city=\'"+ str(qcity)+"\'"
        if whereClause=='':
            whereClause = 'where '+whCity
        else:
            whereClause = whereClause + ' and '+whCity
    
    print('this is the where clause' + whereClause)
    #if whJobTerm!=None and whJobType!=None and whCity!=None:
    #    whereClause = "where " + whJobTerm + "and "+whJobType + "and "+whCity


    #teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    openJobsQuery = "select school_picture, school_name, t2.school_id, min_pay, max_pay, t1.city, t1.category, t1.job_type,t1.term, t1.subject,t1.posted_on, t1.job_id "
    openJobsQuery = openJobsQuery + "from job_detail t1 inner join school_profile t2 on t1.school_id=t2.school_id and t1.status='Open' " + whereClause 
    openJobsQuery = openJobsQuery + " order by t1.posted_on desc "
    #openJobsQuery = openJobsQuery +" OFFSET "+str(offsetVal)+" ROWS FETCH FIRST "+str(recordsOnPage)+" ROW ONLY; "
    #openJobsDataRows = db.session.execute(text(openJobsQuery)).fetchall()    
    openJobsDataRows = db.session.execute(text(openJobsQuery)).fetchall()
    
    if len(openJobsDataRows)==0:
        print('returning 1')
        return jsonify(['1'])
    else:
        next_page=page+1

        if page!=0:
            prev_page=page-1
        else:
            prev_page=None

        prev_url=None
        next_url=None


        if len(openJobsDataRows)==recordsOnPage:
            next_url = url_for('job_post.openJobsFilteredList', page = next_page,job_term=qjob_term, job_type=qjob_type,city=qcity)
            prev_url = url_for('job_post.openJobsFilteredList', page=prev_page,job_term=qjob_term, job_type=qjob_type,city=qcity)
        elif len(openJobsDataRows)<recordsOnPage:
            next_url = None
            if prev_page!=None:
                prev_url = url_for('job_post.openJobsFilteredList', page=prev_page,job_term=qjob_term, job_type=qjob_type,city=qcity)
            else:
                prev_url==None
        else:
            next_url=None
            prev_url=None
        print(type(openJobsDataRows))
        return render_template('_jobList.html',openJobsDataRows=openJobsDataRows,next_url=next_url, prev_url=prev_url)

# API for job list Start
@job_post.route('/jobsFilteredList')
def jobsFilteredList():
    page=request.args.get('page',0, type=int)
    recordsOnPage = 5
    offsetVal = page *recordsOnPage
    
    whereClause = ""
    qjob_term = request.args.get('job_term') #all /short term / long term
    qjob_type = request.args.get('job_type') #all /part time/ full time
    qcity =  request.args.get('city')       # all/ home city
   
    print("qterm is "+str(qjob_term))
    print("qtype is "+str(qjob_type))
    print("qcity is "+str(qcity))

    whJobTerm=''
    whJobType=''
    whCity=''

    if qjob_term=='All' or qjob_term==None or qjob_term=='':
        whJobTerm=None
    else:
        whJobTerm=" t1.term=\'"+str(qjob_term)+"\'"
        whereClause = 'where ' + whJobTerm

    
    if qjob_type=='All' or qjob_type==None or qjob_type=='':
        whJobType=None
    else:
        whJobType=" t1.job_type=\'"+str(qjob_type)+"\'"
        if whereClause=='':
            whereClause = 'where '+whJobType
        else:
            whereClause =  whereClause + ' and '+whJobType
    
    if qcity=='All' or qcity==None or qcity=='':
        whCity=None
    else:
        whCity=" t1.city=\'"+ str(qcity)+"\'"
        if whereClause=='':
            whereClause = 'where '+whCity
        else:
            whereClause = whereClause + ' and '+whCity
    
    print('this is the where clause' + whereClause)
    openJobsQuery = "select school_picture, school_name, t2.school_id, min_pay, max_pay, t1.city, t1.category, t1.job_type,t1.term, t1.subject,t1.posted_on, t1.job_id "
    openJobsQuery = openJobsQuery + "from job_detail t1 inner join school_profile t2 on t1.school_id=t2.school_id and t1.status='Open' " + whereClause 
    openJobsQuery = openJobsQuery + " order by t1.posted_on desc "
    openJobsDataRows = db.session.execute(text(openJobsQuery)).fetchall()
    
    # if len(openJobsDataRows)==0:
    #     print('returning 1')
    #     return jsonify(['1'])
    # else:
    #     next_page=page+1

    #     if page!=0:
    #         prev_page=page-1
    #     else:
    #         prev_page=None

    #     prev_url=None
    #     next_url=None


        # if len(openJobsDataRows)==recordsOnPage:
        #     next_url = url_for('job_post.openJobsFilteredList', page = next_page,job_term=qjob_term, job_type=qjob_type,city=qcity)
        #     prev_url = url_for('job_post.openJobsFilteredList', page=prev_page,job_term=qjob_term, job_type=qjob_type,city=qcity)
        # elif len(openJobsDataRows)<recordsOnPage:
        #     next_url = None
        #     if prev_page!=None:
        #         prev_url = url_for('job_post.openJobsFilteredList', page=prev_page,job_term=qjob_term, job_type=qjob_type,city=qcity)
        #     else:
        #         prev_url==None
        # else:
        #     next_url=None
        #     prev_url=None
    print(openJobsDataRows)
    print(type(openJobsDataRows))
    dataList = []
    for data in openJobsDataRows:
        dataList.append(data)
    print(dataList);
    return jsonify({'data':dataList})
        # return render_template('_jobList.html',openJobsDataRows=openJobsDataRows,next_url=next_url, prev_url=prev_url)

# End



@job_post.route('/jobDetail')

def jobDetail():
    job_id = request.args.get('job_id')
    school_id = ''
    userData = User.query.filter_by(id=current_user.id).first()
    givenSchoolId=request.args.get('school_id')  
    if givenSchoolId:
        school_id = givenSchoolId
    else:
        school_id = userData.school_id
    print(school_id)
    #teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()    
    schoolProfileRow = SchoolProfile.query.filter_by(school_id =school_id).first()
    addressRow = Address.query.filter_by(address_id = schoolProfileRow.address_id).first()    
    jobDetailRow = JobDetail.query.filter_by(job_id=job_id).first()
    if current_user.is_anonymous:
        print('user Anonymous')
        jobApplicationRow = ''
    else:
        print('user exist')
        jobApplicationRow = JobApplication.query.filter_by(job_id=job_id, applier_user_id=current_user.id).first()
    if jobApplicationRow:
        applied=1
    else:
        applied=0
    if current_user.is_anonymous:
        return render_template('jobDetail.html', title='Job Detail', 
            schoolProfileRow=schoolProfileRow,addressRow=addressRow,jobDetailRow=jobDetailRow,applied=applied)
    else:
        return render_template('jobDetail.html', title='Job Detail', 
            schoolProfileRow=schoolProfileRow,addressRow=addressRow,jobDetailRow=jobDetailRow,applied=applied,user_type_val=str(current_user.user_type))
    
@job_post.route('/sendJobApplication',methods=['POST','GET'])
@login_required
def sendJobApplication():
    print('We are in the right place')    
    if request.method=='POST':
        job_id_form = request.form.get('job_id_form')
        available_from=request.form.get("availableFromID")
        available_till=request.form.get("availableTillID")
        if available_from=='':
            available_from=None
        if available_till=='':
            available_till=None
        school_id=request.form.get("school_id")
        #teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
        jobApplyData=JobApplication(applier_user_id=current_user.id, job_id=job_id_form,
                applied_on =datetime.today(),status='Applied',school_id=school_id,available_from=available_from,available_till=available_till,
                last_modified_date=date.today())
        db.session.add(jobApplyData)
        db.session.commit()
        flash('Job application submitted!')
        #try:            
        jobDetailRow = JobDetail.query.filter_by(job_id=job_id_form).first()
        teacherRow = TeacherProfile.query.filter_by(teacher_id=jobDetailRow.posted_by).first()
        new_applicant_for_job(teacherRow.email,teacherRow.teacher_name,current_user.first_name + ' '+current_user.last_name,jobDetailRow.category)
        #except:
        #    pass
        return redirect(url_for('openJobs'))


@job_post.route('/appliedJobs')  # this page shows all the job posts that the user has applied to
@login_required
def appliedJobs():
    appliedQuery = "select applied_on, t3.school_id,school_name, category, subject, t2.job_id, "
    appliedQuery = appliedQuery + "t1.status as application_status, t2.status as job_status "
    appliedQuery = appliedQuery + "from job_application t1 inner join job_detail t2 on "
    appliedQuery = appliedQuery + "t1.job_id=t2.job_id inner join school_profile t3 on "
    appliedQuery = appliedQuery + "t3.school_id=t1.school_id where t1.applier_user_id='"+str(current_user.id)+"'"
    appliedRows = db.session.execute(text(appliedQuery)).fetchall()
    return render_template('appliedJobs.html',title='Applied jobs', user_type_val=str(current_user.user_type),appliedRows=appliedRows)

@job_post.route('/jobApplications')  # this page shows all the applications received by the job poster for any specifc job post
@login_required
def jobApplications():
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    jobidDet=request.args.get('job_id')

    job_id = ''
    if jobidDet:
        job_id = jobidDet
    else:
        jobDet = JobApplication.query.filter_by(school_id=teacher.school_id).first()
        if jobDet:
            job_id = jobDet.job_id
        else:
            job_id = 3
    #jobApplications = JobApplication.query.filter_by(school_id=teacher.school_id).order_by(JobApplication.applied_on.desc()).all()
    #pending descision
    jobAppQuery = "select t1.applied_on, t2.first_name, t2.last_name, t2.username,t1.applier_user_id,t1.job_id, "
    jobAppQuery=jobAppQuery+"t2.city, t1.available_from, t1.available_till, t2.education, t2.experience from "
    jobAppQuery=jobAppQuery+"job_application t1 inner join public.user t2 on t1.applier_user_id=t2.id inner join job_detail t3 on "
    jobAppQuery=jobAppQuery+" t3.job_id=t1.job_id and t3.school_id='"+str(teacher.school_id)+"' and t1.job_id='"+str(job_id)+"' and t1.status='Applied' order by applied_on desc"
    jobApplications = db.session.execute(text(jobAppQuery)).fetchall()

    #hired descision
    jobAppQueryHired = "select t1.applied_on, t2.first_name, t2.last_name, t2.username,t1.applier_user_id, t1.job_id, "
    jobAppQueryHired=jobAppQueryHired+"t2.city, t1.available_from, t1.available_till, t2.education, t2.experience from "
    jobAppQueryHired=jobAppQueryHired+"job_application t1 inner join public.user t2 on t1.applier_user_id=t2.id inner join job_detail t3 on "
    jobAppQueryHired=jobAppQueryHired+" t3.job_id=t1.job_id and t3.school_id='"+str(teacher.school_id)+"' and t1.job_id='"+str(job_id)+"' and t1.status='Hired' order by applied_on desc"
    jobApplicationsHired = db.session.execute(text(jobAppQueryHired)).fetchall()

    #shortlist descision
    jobAppQueryShortlisted = "select t1.applied_on, t2.first_name, t2.last_name, t2.username,t1.applier_user_id, t1.job_id, "
    jobAppQueryShortlisted=jobAppQueryShortlisted+"t2.city, t1.available_from, t1.available_till, t2.education, t2.experience from "
    jobAppQueryShortlisted=jobAppQueryShortlisted+"job_application t1 inner join public.user t2 on t1.applier_user_id=t2.id inner join job_detail t3 on "
    jobAppQueryShortlisted=jobAppQueryShortlisted+" t3.job_id=t1.job_id and t3.school_id='"+str(teacher.school_id)+"' and t1.job_id='"+str(job_id)+"' and t1.status='Shortlisted' order by applied_on desc"
    jobApplicationsShortlisted = db.session.execute(text(jobAppQueryShortlisted)).fetchall()

    #rejected descision
    jobAppQueryRejected = "select t1.applied_on, t2.first_name, t2.last_name, t2.username,t1.applier_user_id, t1.job_id, "
    jobAppQueryRejected=jobAppQueryRejected+"t2.city, t1.available_from, t1.available_till, t2.education, t2.experience from "
    jobAppQueryRejected=jobAppQueryRejected+"job_application t1 inner join public.user t2 on t1.applier_user_id=t2.id inner join job_detail t3 on "
    jobAppQueryRejected=jobAppQueryRejected+" t3.job_id=t1.job_id and t3.school_id='"+str(teacher.school_id)+"' and t1.job_id='"+str(job_id)+"' and t1.status='Rejected' order by applied_on desc"
    jobApplicationsRejected = db.session.execute(text(jobAppQueryRejected)).fetchall()
    
    return render_template('jobApplications.html', classSecCheckVal=classSecCheck(),title='Job Applications',jobApplications=jobApplications, jobApplicationsHired=jobApplicationsHired,jobApplicationsShortlisted= jobApplicationsShortlisted, jobApplicationsRejected = jobApplicationsRejected )

@job_post.route('/jobPosts')
@login_required
def jobPosts():
    teacher=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    jobPosts = JobDetail.query.filter_by(school_id=teacher.school_id).order_by(JobDetail.posted_on.desc()).all()
    return render_template('jobPosts.html',jobPosts=jobPosts, classSecCheckVal=classSecCheck(),school_id=teacher.school_id)



@job_post.route('/processApplication')
@login_required
def processApplication():
    applier_user_id = request.args.get('applier_user_id')
    job_id = request.args.get('job_id')
    process_type = request.args.get('process_type')
    #try:
    jobApplicationRow = JobApplication.query.filter_by(applier_user_id=applier_user_id, job_id=job_id).first()
    jobDetailRow = JobDetail.query.filter_by(job_id=job_id).first()
    applierRow = User.query.filter_by(id=applier_user_id).first()
    schoolRow = SchoolProfile.query.filter_by(school_id=jobApplicationRow.school_id).first()

    print(process_type)
    if process_type=='shortlist':
        jobApplicationRow.status= 'Shortlisted'
        flash('Application Shortlisted')
        try:
            application_processed(applierRow.email,applierRow.first_name + ' '+ applierRow.last_name, schoolRow.school_name,jobDetailRow.category, 'Shortlisted')
        except:
            pass
    elif process_type=='reject':
        jobApplicationRow.status= 'Rejected'
        flash('Application Rejected')
        try:
            application_processed(applierRow.email,applierRow.first_name + ' '+ applierRow.last_name, schoolRow.school_name,jobDetailRow.category, 'Rejected')
        except:
            pass
    elif process_type =='hire':
        jobApplicationRow.status= 'Hired'
        flash('Application Hired')
        try:
            application_processed(applierRow.email,applierRow.first_name + ' '+ applierRow.last_name, schoolRow.school_name,jobDetailRow.category, 'Hired')
        except:
            pass
    else:
        flash('Error processing application idk')
    db.session.commit()
    
    return redirect(url_for('jobApplications',job_id=job_id))
    #except:
    flash('Error processing application')
    return redirect(url_for('jobApplications',job_id=job_id))

@job_post.route('/submitPost', methods=['GET', 'POST'])
@login_required
def submitPost():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('submitPost'))
    posts = [{
        'author': {
            'username': 'John'
        },
        'body': 'Beautiful day in Portland!'
    }, {
        'author': {
            'username': 'Susan'
        },
        'body': 'The Avengers movie was so cool!'
    }]
    return render_template(
        "submitPost.html", title='Submit Post', form=form, posts=posts)
        