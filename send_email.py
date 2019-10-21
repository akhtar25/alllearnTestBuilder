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
    message = "<p>Hi %s, <br><br> Thanks for registering with Alllearn." % name
    message = message + " Our goal at Alllearn is to ensure we uplift the performance of every child in our country, no matter how small the school."
    message = message + "If you have any queries or concerns, please feel free to write back to us and we'll do the best we can to answer you at the earliest.</p>"
    message = message + "<br> <br> Let's make our schools better! <br><br>Thanks, <br>Alllearn "

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
