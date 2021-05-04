from applicationDB import *
from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, url_for, Response,session,jsonify
from applicationDB import *
from flask_login import LoginManager, current_user, logout_user, login_required
from datetime import datetime
from flask import g, jsonify

inventory= Blueprint('inventory',__name__)

@inventory.route('/inventoryManagement')
def inventoryManagement():
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    print('#####################'+str(teacherRow))
    inventoryDetailRow = InventoryDetail.query.filter_by(school_id = teacherRow.school_id, is_archived='N').all()
    
    class_list=ClassSection.query.distinct().order_by(ClassSection.class_val).filter_by(school_id=teacherRow.school_id).all()    
    return render_template('inventoryManagement.html',inventoryDetailRow=inventoryDetailRow,class_list=class_list)

@inventory.route('/addInventoryItem', methods=["GET","POST"])
def addInventoryItem():
    teacherRow=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    inventoryName = request.form.get('inventoryName')    
    newInventoryRow = InventoryDetail(inv_name=request.form.get('invName'),teacher_id= teacherRow.teacher_id, 
        inv_description = request.form.get('invDescription'), inv_category = 225, total_stock = request.form.get('totalStock'),
        item_rate = request.form.get('itemRate'), total_cost = request.form.get('totalCost'), stock_out=0, 
        school_id=teacherRow.school_id, is_archived='N',last_modified_date=datetime.today())
    db.session.add(newInventoryRow)
    db.session.commit()        
    addedInventory = InventoryDetail.query.filter_by(teacher_id = teacherRow.teacher_id, is_archived='N').order_by(InventoryDetail.last_modified_date.desc()).first()
    return jsonify([addedInventory.inv_id])


@inventory.route('/archiveInventory')
def archiveInventory():
    inv_id = request.args.get('inv_id')
    InventoryData = InventoryDetail.query.filter_by(inv_id=inv_id).first()
    InventoryData.is_archived='Y'
    db.session.commit()
    return jsonify(['0'])



@inventory.route('/studentInventoryAlloc')
def studentInventoryAlloc():
    class_sec_id = request.args.get('class_sec_id')
    inv_id = request.args.get('inv_id')
    inv_id = inv_id.split('_')[1]
    #studentInventoryQuery = "select sp.student_id , sp.full_name from student_profile sp  where sp.class_Sec_id="+ str(class_sec_id)    
    #studentInventoryData = db.session.execute(studentInventoryQuery).fetchall()    
    studentInventoryData = StudentProfile.query.filter_by(class_sec_id = str(class_sec_id)).all()
    return render_template('_studentInventoryAlloc.html',studentInventoryData=studentInventoryData)


@inventory.route('/updateInventoryAllocation')
def updateInventoryAllocation():
    ##last bit of changes required here to save inventory allocation
    return jsonify(['0'])
#End of inventory pages
