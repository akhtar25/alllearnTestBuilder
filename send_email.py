from email.mime.text import MIMEText
import smtplib
from flask import render_template
from threading import Thread
from flask import current_app as app


def send_async_email(msg, from_email, from_password):

    gmail=smtplib.SMTP('smtp.sendgrid.net',587)
    gmail.ehlo()
    gmail.starttls()    
    gmail.login(from_email,from_password)
    gmail.send_message(msg)



def send_email(email, name, subjectToSend, messageToSend):
    #from_email="alllearndev@gmail.com"
    #from_password = app.config['SECRET_KEY']
    from_email = "apikey"
    from_password = app.config['EMAIL_API_KEY']
    to_email=email

    subject=subjectToSend
    message=messageToSend

    msg=MIMEText(message,'html')
    msg['Subject']=subject
    msg['To']=to_email
    #msg['From']=from_email
    msg['From']="Alllearn"

    Thread(target=send_async_email, args=(msg, from_email, from_password)).start()


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    email=user.email
    name=user
    subject = "Alllearn - Password Reset mail"
    message = render_template('reset_password.html', user=user, token=token)

    send_email(email, name, subject, message)

def welcome_email(email, name):
    subject = "Welcome to Alllearn"
    message = "<p>Hi %s, <br><br> Thanks for registering with Alllearn</p>." % name
    message = message + " <p>We're so happy to welcome to the family. Our goal at Alllearn is to help school teachers uplift their students' performance and deliver effective classes.</p>"
    message = message + "<p>For the next step, simply login to the account and choose from the following options:"
    message = message + "<br>1. If you're a school principal or admin you can register your school <br>2. if you are a teacher you can request access to your school's dashboard from your school admin. </p>"
    message = message + "<p>If you have any queries or concerns, please let us know on email(contact@alllearn.in) or whatsapp(+91 991-036-8828) and we'll get back to you at the earliest.</p>"
    message = message + "<br> <br> Welcome once again! <br><br>Thanks, <br>Alllearn "
    send_email(email, name, subject, message)

def teacher_access_request_email(email,name, school, requestFrom,adminUsername):
    subject = "Alllearn - Teacher access request for %s" % requestFrom
    message = render_template('teacher_access_req_email.html', name=name, school=school,requestFrom=requestFrom, adminUsername=adminUsername)
    send_email(email, name, subject, message)

def access_granted_email(email,name, school):
    subject = "Alllearn - Access granted to %s" % school
    message = render_template('access_granted_email.html', name=name, school=school)
    send_email(email, name, subject, message)

def guardian_access_request_email(email,name, school, requestFrom):
    subject = "Alllearn - Guardian access request for %s" % requestFrom
    message = render_template('guardian_access_req_email.html', name=name, school=school)
    send_email(email, name, subject, message)



def new_school_reg_email(school):
    subject = "Alllearn - New School Registered %s" % school
    name = "Alllearn Team"
    email = "contact@alllearn.in"
    message = render_template('new_school_reg_email.html', school=school, name=name)
    send_email(email, name, subject, message)


def new_teacher_invitation(email,name,school, inviteFrom):
    subject = "Alllearn - Invitation to %s's dashboard for %s" % (school, name)
    message = render_template('new_teacher_invitation_email.html', name=name, school=school, inviteFrom=inviteFrom)
    send_email(email, name, subject, message)

def new_applicant_for_job(email,adminName,applicantName,jobName):
    subject = 'Alllearn - Received new application for the job %s' % (jobName)
    message = render_template('new_applicant_for_job.html', adminName = adminName, applicantName=applicantName, jobName=jobName)
    name = "Alllearn"
    send_email(email, name, subject, message)


def job_posted_email(email,name, school,jobName):
    subject = "Alllearn - New job posted for %s" % (school)
    message = "<p>Hi %s, <br><br> The new job you posted for %s is now live.</p>" % (name,jobName)
    message = message + " <p>You should start receiving applications right away.</p>"
    message = message + "<p>In case you wish to edit or close the job or have any queries please let us know at contact@alllearn.in"
    message = message + " <br><br>Thanks, <br>Alllearn team"
    name = 'Alllearn'
    send_email(email, name, subject, message)


def application_processed(email,applicantName, school,jobName, process_type):
    subject = "Alllearn - Application %s for %s role at %s" % (process_type, jobName, school)
    message = "<p>Hi %s, <br><br> Your application for the role of %s at %s has been <b>%s</b>.</p>" % (applicantName,jobName,school,process_type)
    message = message + "<p>For any queries please write to us at contact@alllearn.in"
    message = message + " <br><br>Thanks, <br>Alllearn team"
    name = 'Alllearn'
    send_email(email, name, subject, message)