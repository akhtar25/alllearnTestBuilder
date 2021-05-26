from flask import Flask, Blueprint, Markup, render_template, request, flash, redirect, Response,session,jsonify
from applicationDB import *
from flask import g, jsonify
from sqlalchemy import distinct, text, update


topic_generate = Blueprint('topic_generate',__name__)

@topic_generate.route('/questionBuilder/<class_val>/<subject_id>')
def topic_list(class_val,subject_id):
    cl = class_val.replace("-","/")
    topic_list="select td.topic_id,td.topic_name fr@topic_listom topic_detail td inner join topic_tracker tt on td.topic_id = tt.topic_id where td.class_val = '"+str(cl)+"' and td.subject_id = '"+str(subject_id)+"' and tt.is_archived = 'N'"
    topic_list = db.session.execute(text(topic_list))
    topicArray=[]

    for topic in topic_list:
        topicObj={}
        topicObj['topic_id']=topic.topic_id
        topicObj['topic_name']=topic.topic_name
        topicArray.append(topicObj)
    
    return jsonify({'topics':topicArray})

@topic_generate.route('/questionTopicPicker')
def questionTopicPicker():
    print('Inside topic picker')
    class_val = request.args.get('class_val')
    subject_id = request.args.get('subject_id')
    topic_list="select td.topic_id,td.chapter_num,td.topic_name from topic_detail td inner join topic_tracker tt on td.topic_id = tt.topic_id where td.class_val = '"+str(class_val)+"' and td.subject_id = '"+str(subject_id)+"' and tt.is_archived = 'N'"
    topic_list = db.session.execute(text(topic_list)).fetchall()
    for topic in topic_list:
        print(topic.topic_id)
        print(topic.topic_name)
        print(topic.chapter_num)
    
    return render_template('_topics.html',topic_list=topic_list)

# @topic_generate.route('/coveredTopic',methods=['GET','POST'])
# def coveredTopic():
#     print('covered Topics')
#     class_v = request.args.get('class_val')
#     section = request.args.get('section')
#     query = "select *from topic_details where "
#     return render_template('_topicCovered.html')

@topic_generate.route('/questionChapterpicker/<class_val>/<subject_id>')
def chapter_list(class_val,subject_id):
    cl = class_val.replace('-','/')
    chapter_num = "select distinct td.chapter_num,td.chapter_name from topic_detail td inner join topic_tracker tt on td.topic_id = tt.topic_id where td.class_val='"+cl+"' and td.subject_id='"+subject_id+"' and tt.is_archived='N' order by td.chapter_num,td.chapter_name"
    print(chapter_num)
    print('Inside chapterPicker')
    
    chapter_num_list = db.session.execute(text(chapter_num))
    chapter_num_array=[]
    for chapterno in chapter_num_list:
        chapterNo = {}
        chapterNo['chapter_num']=chapterno.chapter_num
        chapterNo['chapter_name']=chapterno.chapter_name
        chapter_num_array.append(chapterNo)
    return jsonify({'chapterNum':chapter_num_array})
