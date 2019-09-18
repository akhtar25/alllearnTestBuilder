from email.mime.text import MIMEText
import smtplib
from flask import render_template
from threading import Thread
from flask import current_app as app


def send_async_email(msg, from_email, from_password):

    gmail=smtplib.SMTP('smtp.gmail.com',587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(from_email,from_password)
    gmail.send_message(msg)



def send_email(email, name, subjectToSend, messageToSend):
    from_email="contact@alllearn.in"
    #from_password = app.config['SECRET_KEY']
    from_password = "indiana4jones"
    to_email=email

    subject=subjectToSend
    message=messageToSend

    msg=MIMEText(message,'html')
    msg['Subject']=subject
    msg['To']=to_email
    msg['From']=from_email

    Thread(target=send_async_email, args=(msg, from_email, from_password)).start()


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    email=user.email
    name=user
    subject = "Alllearn - Password Reset mail"
    message = render_template('reset_password.html', user=user, token=token)

    send_email(email, name, subject, message)

def newsletterEmail(email, name):

    subject = "Welcome to Alllearn"
    message = "<p>Hi %s, <br><br> Thanks for registering with Alllearn Group." % name
    message = message + " Our goal at Alllear is to ensure we uplift the performance of every child in our country, no matter how small the school."
    message = message + "If you have any queries or concerns, please feel free to write back to us and we'll do the best we can to answer you at the earliest.</p>"
    message = message + "<br> <br> Let's make our schools better! <br><br>Thanks, <br>Alllearn "

    send_email(email, name, subject, message)
