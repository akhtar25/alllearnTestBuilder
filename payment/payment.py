from flask import current_app as app
from flask import Blueprint, Markup, render_template, request, flash, url_for, Response
from applicationDB import *
from flask_login import LoginManager, current_user, login_user, logout_user
from datetime import datetime
from flask import g, jsonify
import base64
import hmac
import hashlib
import json

payment = Blueprint('payment',__name__)

# enrolledStudents = request.form.get('enrolledStudents')
# students_enrolled=enrolledStudents

@payment.route('/paymentForm')
def paymentForm():    
    if current_user.is_authenticated:
        #if current_user.country==None:
        #    flash('Please update your profile before donating ')
        #    return jsonify(['2'])

        #qschool_id = request.args.get('school_id')
        amount =  request.args.get('amount') 
        qbatch_id = request.args.get('batch_id')                
        #amount =              #hard coded value
        #qbatch_id = 1               #hard coded value

        if amount=='other':
            amount = 0
        #donation_for = request.args.get('donation_for')
        #if donation_for =='' or donation_for=='undefined':            
        #    donation_for=24
        
        courseBatchData = CourseBatch.query.filter_by(batch_id = qbatch_id).first()
        courseDetailData =CourseDetail.query.filter_by(course_id=courseBatchData.course_id).first()
        schoolData = SchoolProfile.query.filter_by(school_id=courseDetailData.school_id).first() 
        print("this is the batch id: "+str(courseBatchData.batch_id))

        print("this is the course desc: "+str(courseDetailData.description))
        #New section added to handle different vendors     
        #if schoolData.curr_sub_charge_type== 41:
        #    schoolShare = 100-int(schoolData.curr_sub_charge)
        #    selfShare = schoolData.curr_sub_charge             
        #else:

        #every payment amout is to be split in the ratio 97:3 :: Tutor: allLearn
        schoolShare = 97
        selfShare = 3
        vendorData = [
            {
                "vendorId": schoolData.curr_vendor_id,
                "commission": 97 #int(schoolShare)
            }, 
            {
                "vendorId":"SELF",
                "commission":3 #int(selfShare)
            }
        ]

        #vendorData=    [{"vendorId":"VENDOR1","commission":30}, {"vendorId":"VENDOR2","commission":40}]        
        vendorData = json.dumps(vendorData, separators=(',', ':'))
        print(vendorData)
        vendorDataEncoded = base64.b64encode(vendorData.encode('utf-8')).decode('utf-8')
        print(vendorDataEncoded)
        #end of section

        note = "Enrollment transaction"   
        payer_name = current_user.first_name + ' ' + current_user.last_name

        messageData = "" #MessageDetails.query.filter_by(msg_id=payment_for).first()

        #Inserting new order and transaction detail in db

        transactionNewInsert = PaymentTransaction(amount=courseBatchData.course_batch_fee,note=note, 
            payer_user_id=current_user.id, payer_name=str(payer_name),payer_phone=current_user.phone, payer_email=current_user.email,
            school_id=courseDetailData.school_id, teacher_id=courseDetailData.teacher_id,batch_id=qbatch_id, trans_type=254, payment_for= 264, tran_status=256, date=datetime.today()) 
        db.session.add(transactionNewInsert)
        db.session.commit()

        #Fetching all required details for the form and signature creation

        #transactionData = PaymentTransaction.query.filter_by(payer_user_id=current_user.id).order_by(PaymentTransaction.date.desc()).first()
        transactionData  = transactionNewInsert
        orderId= str(transactionData.tran_id).zfill(9)
        print("#######order id: "+str(orderId))
        currency = transactionData.currency
        appId= app.config['ALLLEARN_CASHFREE_APP_ID']
        returnUrl = url_for('paymentResponse',_external=True)
        notifyUrl = url_for('notifyUrl',_external=True)
        return render_template('_paymentForm.html',courseDetailData=courseDetailData,courseBatchData=courseBatchData, vendorDataEncoded=vendorDataEncoded,messageData=messageData,notifyUrl=notifyUrl,returnUrl=returnUrl, schoolData=schoolData, appId=appId, orderId = orderId, amount = amount, orderCurrency = currency, orderNote = note, customerName = payer_name)
    else:
        flash('Please login to enroll')
        return jsonify(['1'])

@payment.route('/freeEnrollment')
def freeEnrollment():
    if current_user.is_authenticated:
        batch_id = request.args.get('batch_id')
        courseBatchData = CourseBatch.query.filter_by(batch_id =batch_id , is_archived='N').first()
        courseBatchData.students_enrolled = int(courseBatchData.students_enrolled) + 1
        courseEnrollmentData = CourseEnrollment(course_id= courseBatchData.course_id, 
            batch_id = batch_id, student_user_id=current_user.id, is_archived='N', 
            last_modified_date = datetime.today())   
        db.session.add(courseEnrollmentData)
        db.session.commit()
        flash('Course Enrolled')
        return jsonify(['0'])
    else:
        flash('Please login to enroll')
        return jsonify(['1'])


@payment.route('/request', methods=["POST"])
def handlerequest():
    mode = app.config["MODE"] # <-------Change to TEST for test server, PROD for production
    platformSub = request.args.get('platformSub')
    if platformSub=="1":
        postData = {
            "appId" : request.form['appId'], 
            "orderId" : request.form['orderId'], 
            "orderAmount" : request.form['orderAmount'], 
            "orderCurrency" : request.form['orderCurrency'], 
            "orderNote" : request.form['orderNote'], 
            "customerName" : request.form['customerName'], 
            "customerPhone" : request.form['customerPhone'], 
            "customerEmail" : request.form['customerEmail'], 
            "returnUrl" : request.form['returnUrl'], 
            "notifyUrl" : request.form['notifyUrl'],
        }
    else:
        postData = {
            "appId" : request.form['appId'], 
            "orderId" : request.form['orderId'], 
            "orderAmount" : request.form['orderAmount'], 
            "orderCurrency" : request.form['orderCurrency'], 
            "orderNote" : request.form['orderNote'], 
            "customerName" : request.form['customerName'], 
            "customerPhone" : request.form['customerPhone'], 
            "customerEmail" : request.form['customerEmail'], 
            "returnUrl" : request.form['returnUrl'], 
            "notifyUrl" : request.form['notifyUrl'],
            "vendorSplit" : request.form['vendorSplit']
        }
    #vendorSplit = request.form['vendorSplit']
    sortedKeys = sorted(postData)
    signatureData = ""
    for key in sortedKeys:
      signatureData += key+postData[key]
    message = signatureData.encode('utf-8')
    #get secret key from config
    secret = app.config['ALLLEARN_CASHFREE_SECRET_KEY'].encode('utf-8')
    signature = base64.b64encode(hmac.new(secret,message,digestmod=hashlib.sha256).digest()).decode("utf-8")   
            
    transactionData = PaymentTransaction.query.filter_by(payer_user_id=current_user.id).order_by(PaymentTransaction.date.desc()).first()
    transactionData.order_id=postData["orderId"]
    #transactionData.anonymous_donor = anonymous_donor
    #transactionData.anonymous_amount = hide_amount
    transactionData.tran_status = 257 
    transactionData.request_sign_hash = signature
    transactionData.amount = postData["orderAmount"]

    #updating user phone number
    if current_user.phone==None or current_user.phone=="":
        userDataUpdate = User.query.filter_by(id=current_user.id).first()
        userDataUpdate.phone = request.form['customerPhone']
    db.session.commit()

    if mode == 'PROD': 
      url = "https://www.cashfree.com/checkout/post/submit"
    else: 
      url = "https://test.cashfree.com/billpay/checkout/post/submit"
    return render_template('request.html', postData = postData,signature = signature,url = url, platformSub=platformSub)


#this is the page after response from payment gateway
@payment.route('/paymentResponse', methods=["POST"])
def paymentResponse():
    payment = request.args.get('payment')

    postData = {
    "orderId" : request.form['orderId'], 
    "orderAmount" : request.form['orderAmount'], 
    "referenceId" : request.form['referenceId'], 
    "txStatus" : request.form['txStatus'], 
    "paymentMode" : request.form['paymentMode'], 
    "txMsg" : request.form['txMsg'], 
    "signature" : request.form['signature'], 
    "txTime" : request.form['txTime']
    }

    signatureData = ""
    signatureData = postData['orderId'] + postData['orderAmount'] + postData['referenceId'] + postData['txStatus'] + postData['paymentMode'] + postData['txMsg'] + postData['txTime']

    message = signatureData.encode('utf-8')
    # get secret key from your config
    secret = app.config['ALLLEARN_CASHFREE_SECRET_KEY'].encode('utf-8')
    computedsignature = base64.b64encode(hmac.new(secret,message,digestmod=hashlib.sha256).digest()).decode('utf-8')   
    print("####this is the txStatus: "+str(postData["txStatus"]))
    messageData = MessageDetails.query.filter_by(description = postData["txStatus"]).first()

    #updating response transaction details into the DB
    transactionData = PaymentTransaction.query.filter_by(order_id=postData["orderId"]).first()
    currency = transactionData.currency
 
    transactionData.gateway_ref_id = postData["referenceId"]
    if transactionData.tran_status!=263:
        transactionData.tran_status = messageData.msg_id
    transactionData.payment_mode = postData["paymentMode"]
    transactionData.tran_msg = postData["txMsg"]
    transactionData.tran_time = postData["txTime"]
    transactionData.response_sign_hash = postData["signature"]
    if postData["signature"]==computedsignature:
        transactionData.response_sign_check="Matched"
    else:
        transactionData.response_sign_check="Not Matched"
    schoolData = SchoolProfile.query.filter_by(school_id=transactionData.school_id).first()
    if payment!='sub':
        #updating school data
        if transactionData.tran_status==258 or transactionData.tran_status==263:
            courseBatchData = CourseBatch.query.filter_by(batch_id = transactionData.batch_id, is_archived='N').first()
            if courseBatchData!=None:
                courseBatchData.total_fee_received = int(courseBatchData.total_fee_received)  + int(transactionData.amount)
                courseBatchData.students_enrolled = int(courseBatchData.students_enrolled) + 1

                courseEnrollmentData = CourseEnrollment(course_id= courseBatchData.course_id, batch_id = transactionData.batch_id, student_user_id=current_user.id, is_archived='N', 
                    last_modified_date = datetime.today())   
                db.session.add(courseEnrollmentData)
                courseDataQuery = "select course_id, course_name, tp.teacher_id, teacher_name from course_detail cd"
                courseDataQuery = courseDataQuery + " inner join teacher_profile tp on tp.teacher_id=cd.teacher_id"
                courseDataQuery = courseDataQuery + " and course_id="+ str(courseBatchData.course_id) 
                courseData = db.session.execute(courseDataQuery).first()
    db.session.commit()

    return render_template('paymentResponse.html',courseData=courseData, courseBatchData=courseBatchData,transactionData = transactionData,payment=payment,postData=postData,computedsignature=computedsignature, schoolData=schoolData,currency=currency)


@payment.route('/notifyUrl',methods=["POST"])
def notifyUrl():
    postData = {
      "orderId" : request.form['orderId'], 
      "orderAmount" : request.form['orderAmount'], 
      "referenceId" : request.form['referenceId'], 
      "txStatus" : request.form['txStatus'], 
      "paymentMode" : request.form['paymentMode'], 
      "txMsg" : request.form['txMsg'], 
      "txTime" : request.form['txTime'], 
    }
    
    transactionData = Transaction.query.filter_by(order_id = postData["orderId"]).first()
    schoolData = SchoolProfile.query.filter_by(school_id=transactionData.school_id).first()
    if transactionData!=None:
        transactionData.tran_status = 263
        db.session.commit()        
        #donation_success_email_donor(schoolData.name, transactionData.donor_name,transactionData.donor_email,postData)
    else:
        print('############### no transaction detail found')
    return str(0)


def requestSignGenerator(appId, orderId, orderAmount, orderCurrency, orderNote, customerName, customerPhone,customerEmail, returnUrl, notifyUrl):    
    postData = {
      "appId" : appId,
      "orderId" : orderId,
      "orderAmount" : orderAmount,
      "orderCurrency" : orderCurrency,
      "orderNote" : orderNote,
      "customerName" : customerName,
      "customerPhone" : customerPhone,
      "customerEmail" : customerEmail,
      "returnUrl" : returnUrl,
      "notifyUrl" : notifyUrl
    }
    sortedKeys = sorted(postData)
    signatureData = ""
    for key in sortedKeys:
      signatureData += key+postData[key]

    message = bytes(signatureData,encoding='utf-8')
    #get secret key from your config
    secret = bytes(app.config['ALLLEARN_CASHFREE_SECRET_KEY'],encoding='utf-8')
    signature = base64.b64encode(hmac.new(secret, message,digestmod=hashlib.sha256).digest())
    return signature


def verifyResponseSign(receivedResponseSign, postData):
    signatureData = postData["orderId"] + postData["orderAmount"] + postData["referenceId"] + postData["txStatus"] + postData["paymentMode"] + postData["txMsg"] + postData["txTime"]
    message = bytes(signatureData).encode('utf-8')
    #get secret key from your config
    secret = bytes(app.config['ALLLEARN_CASHFREE_SECRET_KEY']).encode('utf-8')
    signature = base64.b64encode(hmac.new(secret, message,digestmod=hashlib.sha256).digest())
    if signature==receivedResponseSign:
        return True
    else:
        return False


