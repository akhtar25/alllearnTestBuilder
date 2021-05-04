from applicationDB import *
from flask import Blueprint, render_template, request, redirect, Response
from flask_login import LoginManager, current_user, login_user, login_required
from datetime import datetime
from flask import g, jsonify
from sqlalchemy import text
from calendar import monthrange


fee_details= Blueprint('fee_details',__name__)



@fee_details.route('/feeMonthData')
def feeMonthData():
    qmonth = request.args.get('month')
    qyear = request.args.get('year')
    class_val = request.args.get('class_val')
    section = request.args.get('section')
    print('inside Summary Box route')
    print(class_val)
    print(section)
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ''
    if class_val!=None:
        class_sec_id = ClassSection.query.filter_by(class_val=class_val,section=section,school_id=teacherDataRow.school_id).first()
    print(qmonth+ ' '+qyear)
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #days in month
    daysInMonth = monthrange(int(qyear),int(qmonth))
    daysInMonth = int(daysInMonth[1])
    feeDetail = ''
    if class_val=='None' or class_val=='':
        print('if class is None')
        paid_fees = "select sum(fee_paid_amount) as collected_fee from fee_detail where school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        paid_fees = db.session.execute(text(paid_fees)).first()
        paid_student_count = "select count(*) as no_of_paid_students from fee_detail where fee_amount=fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        paid_student_count = db.session.execute(text(paid_student_count)).first()
        classSec_ids = FeeClassSecDetail.query.filter_by(school_id=teacherDataRow.school_id).all()
        unpaid_students_count = 0
        for class_sec_id in classSec_ids:
            unpaid_students = "select count(*) as no_of_unpaid_students from student_profile sp where sp.student_id not in (select student_id from fee_detail where school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"') and sp.school_id='"+str(teacherDataRow.school_id)+"' and sp.class_sec_id='"+str(class_sec_id.class_sec_id)+"'"
            unpaid_students = db.session.execute(text(unpaid_students)).first()
            unpaid_students_count = unpaid_students_count + unpaid_students.no_of_unpaid_students
        partially_paid_students = "select count(*) as partially_paid_students from fee_Detail where fee_amount>fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        partially_paid_students = db.session.execute(text(partially_paid_students)).first()
        class_sec_ids = ClassSection.query.filter_by(school_id=teacherDataRow.school_id).all()
        total_unpaid_students = 0
        if partially_paid_students:
            total_unpaid_students = int(unpaid_students_count) + int(partially_paid_students.partially_paid_students)
        
        total_unpaid_fee = 0
        for class_sec_id in class_sec_ids:
            unpaid_students = "select count(*) as no_of_unpaid_students from student_profile sp where sp.student_id not in (select student_id from fee_detail where school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"') and sp.school_id='"+str(teacherDataRow.school_id)+"' and sp.class_sec_id='"+str(class_sec_id.class_sec_id)+"'"
            unpaid_students = db.session.execute(text(unpaid_students)).first()
            fee_amount = FeeClassSecDetail.query.filter_by(class_sec_id=class_sec_id.class_sec_id,school_id=teacherDataRow.school_id).first()
            unpaid_students_fee = 0
            if unpaid_students and fee_amount:
                unpaid_students_fee = int(unpaid_students.no_of_unpaid_students) * int(fee_amount.amount)
            partially_paid_fee = "select sum(outstanding_amount) as pending_amount from fee_detail where fee_amount>fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
            partially_paid_fee = db.session.execute(text(partially_paid_fee)).first()
            if partially_paid_fee:
                print('partially paid fee:'+str(partially_paid_fee.pending_amount))
            if partially_paid_fee.pending_amount:
                total_unpaid_fee = total_unpaid_fee + unpaid_students_fee + partially_paid_fee.pending_amount
            else:
                total_unpaid_fee = total_unpaid_fee + unpaid_students_fee
    else:
        print('if class is not None')
        paid_fees = "select sum(fee_paid_amount) as collected_fee from fee_detail where school_id='"+str(teacherDataRow.school_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        paid_fees = db.session.execute(text(paid_fees)).first()
        paid_student_count = "select count(*) as no_of_paid_students from fee_detail where fee_amount=fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        paid_student_count = db.session.execute(text(paid_student_count)).first()
        unpaid_students = "select count(*) as no_of_unpaid_students from student_profile sp where sp.student_id not in (select student_id from fee_detail where school_id='"+str(teacherDataRow.school_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"') and sp.school_id='"+str(teacherDataRow.school_id)+"' and sp.class_sec_id='"+str(class_sec_id.class_sec_id)+"'"
        unpaid_students = db.session.execute(text(unpaid_students)).first()
        partially_paid_students = "select count(*) as partially_paid_students from fee_Detail where fee_amount>fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        partially_paid_students = db.session.execute(text(partially_paid_students)).first()
        total_unpaid_students = 0
        if unpaid_students and partially_paid_students:
            total_unpaid_students = int(unpaid_students.no_of_unpaid_students) + int(partially_paid_students.partially_paid_students)
        fee_amount = FeeClassSecDetail.query.filter_by(class_sec_id=class_sec_id.class_sec_id,school_id=teacherDataRow.school_id).first()
        
        unpaid_students_fee = 0
        if unpaid_students and fee_amount:
            unpaid_students_fee = int(unpaid_students.no_of_unpaid_students) * int(fee_amount.amount)
        partially_paid_fee = "select sum(outstanding_amount) as pending_amount from fee_detail where fee_amount>fee_paid_amount and school_id='"+str(teacherDataRow.school_id)+"' and class_sec_id='"+str(class_sec_id.class_sec_id)+"' and month='"+str(qmonth)+"' and year='"+str(qyear)+"'"
        partially_paid_fee = db.session.execute(text(partially_paid_fee)).first()
        total_unpaid_fee = 0
        if partially_paid_fee:
            print('partially paid fee:'+str(partially_paid_fee.pending_amount))
            if partially_paid_fee.pending_amount:
                total_unpaid_fee = unpaid_students_fee + partially_paid_fee.pending_amount
            else:
                total_unpaid_fee = unpaid_students_fee
    return render_template('_summaryBox.html',paid_fees=paid_fees.collected_fee,paid_student_count=paid_student_count.no_of_paid_students,total_unpaid_students=total_unpaid_students,total_unpaid_fee=total_unpaid_fee)


@fee_details.route('/feeStatusDetail')
def feeStatusDetail():
    qmonth = request.args.get('month')
    qyear = request.args.get('year')
    class_val = request.args.get('class_val')
    section = request.args.get('section')
    
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    class_sec_id = ClassSection.query.filter_by(class_val=class_val,section=section,school_id=teacherDataRow.school_id).first()
    print(qmonth+ ' '+qyear)
    #days in month
    daysInMonth = monthrange(int(qyear),int(qmonth))
    daysInMonth = int(daysInMonth[1])
    feeStatusDataQuery = "select sp.student_id as student_id, sp.profile_picture as profile_picture, sp.full_name as student_name,sp.roll_number, fd.fee_amount as fee_amount,fd.fee_paid_amount as paid_amount, fd.outstanding_amount as rem_amount, fd.paid_status as paid_status,fd.delay_reason"
    feeStatusDataQuery = feeStatusDataQuery + " from student_profile  sp left join "
    feeStatusDataQuery = feeStatusDataQuery + "fee_detail fd on fd.student_id=sp.student_id "
    feeStatusDataQuery = feeStatusDataQuery + " and fd.month = "+str(qmonth) + " and fd.year = "+ str(qyear) + " where sp.school_id=" + str(teacherDataRow.school_id) + " and sp.class_sec_id='"+str(class_sec_id.class_sec_id)+"' order by paid_status asc"
    feeStatusDataRows = db.session.execute(text(feeStatusDataQuery)).fetchall()
    print(str(len(feeStatusDataRows)))
    sections = ClassSection.query.filter_by(school_id=teacherDataRow.school_id,class_val=class_val).all()
    total_amt = ''
    amount = FeeClassSecDetail.query.filter_by(class_sec_id=class_sec_id.class_sec_id,school_id=teacherDataRow.school_id).first()
    if amount:
        total_amt = amount.amount
    print('Total amount:'+str(total_amt))
    return render_template('_feeStatusTable.html',total_amt=total_amt,feeStatusDataRows=feeStatusDataRows,qmonth=qmonth,qyear=qyear,class_val=class_val,section=section)
#New Section added to manage payroll
@fee_details.route('/payrollMonthData')
def payrollMonthData():
    qmonth = request.args.get('month')
    qyear = request.args.get('year')
    print(qmonth+ ' '+qyear)
    teacherDataRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    #days in month
    daysInMonth = monthrange(int(qyear),int(qmonth))
    daysInMonth = int(daysInMonth[1])
    #temporary query
    payrollDataQuery = "select tp.teacher_id as teacher_id, tp.profile_picture as profile_picture, tp.teacher_name as teacher_name, tp.curr_salary as curr_salary,tpd.days_present as days_present, tpd.calc_salary, tpd.paid_status as paid_status"
    payrollDataQuery = payrollDataQuery + " from teacher_profile  tp left join "
    payrollDataQuery = payrollDataQuery + "teacher_payroll_detail tpd on tpd.teacher_id=tp.teacher_id "
    payrollDataQuery = payrollDataQuery + " and tpd.month = "+str(qmonth) + " and tpd.year = "+ str(qyear) + " where tp.school_id=" + str(teacherDataRow.school_id) + " order by paid_status asc"
    payrollDataRows = db.session.execute(text(payrollDataQuery)).fetchall()
    print(str(len(payrollDataRows)))
    return render_template('_payrollMonthData.html',daysInMonth=daysInMonth, payrollDataRows=payrollDataRows, qmonth=qmonth, qyear = qyear)

@fee_details.route('/updateFeeData', methods=['GET','POST'])
def updateFeeData():
    teacherDetailRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()    
    qmonth = request.form.get('qmonth')
    qyear = request.form.get('qyear')
    total_amt = request.args.get('total_amt')
    total_amt = total_amt.strip()
    qclass_val = request.form.get('qclass_val')
    qsection = request.form.get('qsection')
    print('inside updateFeeData')
    print('Total Fee Amount:'+str(total_amt))
    class_sec_id = ClassSection.query.filter_by(class_val=qclass_val,section=qsection,school_id=teacherDetailRow.school_id).first()
    student_id_list = request.form.getlist('student_id')
    paid_amount_list = request.form.getlist('paid_amount')
    rem_amount_list = request.form.getlist('rem_amount')
    # validation when rem_amount is negative
    for i in range(len(rem_amount_list)-1):
        print('inside re_amount_list')
        print(i)
        print(rem_amount_list[i])
        if rem_amount_list[i]:
            if int(rem_amount_list[i])<0:
                return jsonify(['1'])
    # End
    delay_reason_list = request.form.getlist('delay_reason')
    count_list = []
    for i in range(len(paid_amount_list)):
        if paid_amount_list[i]:
            print('counter:'+str(i))
            print('paid amount:'+str(paid_amount_list[i]))
            count_list.append(i)
    # print(paid_amount_list)
    print('count_list length:'+str(len(count_list)))
    for i in range(len(count_list)):
        print('inside for loop')
        print(count_list[i])
        print(student_id_list[count_list[i]])
        if paid_amount_list[count_list[i]]:
            indivFeeRecord = FeeDetail.query.filter_by(student_id=student_id_list[count_list[i]], month=qmonth, year=qyear).first()
            if indivFeeRecord and indivFeeRecord.outstanding_amount!=0:
                print('if record already exist:'+str(paid_amount_list[count_list[i]]))
                indivFeeRecord.fee_amount = total_amt
                indivFeeRecord.fee_paid_amount = paid_amount_list[count_list[i]]
                indivFeeRecord.outstanding_amount = rem_amount_list[count_list[i]]
                indivFeeRecord.delay_reason = delay_reason_list[count_list[i]]
                print('pending amount:'+str(rem_amount_list[count_list[i]]))
                if rem_amount_list[count_list[i]]==0 or rem_amount_list[count_list[i]]=='0':
                    indivFeeRecord.paid_status = 'Y'
                else:
                    indivFeeRecord.paid_status = 'N'
            elif indivFeeRecord==None or indivFeeRecord=='':
                print('Adding new values:'+str(paid_amount_list[count_list[i]]))
                print('Paid Amount:'+paid_amount_list[count_list[i]])
                print('Total Amount:'+total_amt)
                if float(paid_amount_list[count_list[i]])==float(total_amt):
                    print('if paid amount equal to total amount')
                    feeInsert=FeeDetail(school_id=teacherDetailRow.school_id,student_id=student_id_list[count_list[i]],fee_amount = total_amt,
                    class_sec_id=class_sec_id.class_sec_id,payment_date=datetime.today(),fee_paid_amount = paid_amount_list[count_list[i]],outstanding_amount=rem_amount_list[count_list[i]],month=qmonth,year=qyear
                    ,paid_status='Y',delay_reason=delay_reason_list[count_list[i]],last_modified_date=datetime.today())
                else:
                    print('if paid amount is less than total amount')
                    feeInsert=FeeDetail(school_id=teacherDetailRow.school_id,student_id=student_id_list[count_list[i]],fee_amount = total_amt,
                    class_sec_id=class_sec_id.class_sec_id,payment_date=datetime.today(),fee_paid_amount = paid_amount_list[count_list[i]],outstanding_amount=rem_amount_list[count_list[i]],month=qmonth,year=qyear
                    ,paid_status='N',delay_reason=delay_reason_list[count_list[i]],last_modified_date=datetime.today())
                db.session.add(feeInsert)
    db.session.commit()
    return jsonify(['0'])

@fee_details.route('/updatePayrollData', methods=['GET','POST'])
def updatePayrollData():
    teacherDetailRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()    
    teacher_id_list = request.form.getlist('teacher_id')    
    current_salary_list = request.form.getlist('currentSalaryInput')
    days_count_list = request.form.getlist('dayCountInput')
    days_present_list = request.form.getlist('days_present')
    calc_salary_list = request.form.getlist('calcSalaryInput')
    #paid_status_list = request.form.getlist('paid_status')
    has_changed_list = request.form.getlist('hasChanged')
    qmonth = request.form.get('qmonth')
    qyear = request.form.get('qyear')
    #print(teacher_id_list)
    #print(current_salary_list)
    #print(days_count_list)
    #print(days_present_list)
    #print(calc_salary_list)
    #print(has_changed_list)
    #print(qmonth)
    #print(qyear)
    ##print(paid_status_list)
    #print("#########")
    for i in range(len(has_changed_list)):
        print("This is the value of i "+ str(i))
        if has_changed_list[i]=='Y':   
            print ('Something has changed')
            #if (paid_status_list[i]):
            #    paidValue = 'Y'
            #else:
            #    paidValue='N'
            indivPayrollRecord = TeacherPayrollDetail.query.filter_by(teacher_id=teacher_id_list[i], month=qmonth, year=qyear).first()
            if indivPayrollRecord==None:
                print('Adding new values')
                payrollInsert=TeacherPayrollDetail(teacher_id=teacher_id_list[i],total_salary=current_salary_list[i],month=qmonth,
                    year=qyear,days_in_month=days_count_list[i],days_present = days_present_list[i], calc_salary = calc_salary_list[i], paid_status='Y',
                    last_modified_date=datetime.today(), school_id = teacherDetailRow.school_id)
                db.session.add(payrollInsert)
            else:
                if indivPayrollRecord.calc_salary!=calc_salary_list[i]:
                    print('Updating exiting values')
                    indivPayrollRecord.days_present = days_present_list[i]
                    indivPayrollRecord.calc_salary= calc_salary_list[i]
                    indivPayrollRecord.paid_status = 'Y'
                    indivPayrollRecord.last_modified_date = datetime.today()

    db.session.commit()
    return jsonify(['0'])
