import os
from flask import Flask, render_template, request, flash, redirect, url_for, Response,session,jsonify
from send_email import welcome_email, send_password_reset_email
from applicationDB import *
from qrReader import *
from config import Config
from forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm,ResultQueryForm,MarksForm,QuestionBuilderQueryForm,TestBuilderQueryForm
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from logging.handlers import RotatingFileHandler
import os
import logging
import datetime as dt
from flask_moment import Moment
from elasticsearch import Elasticsearch
from flask import g, jsonify
from forms import SearchForm
from forms import PostForm
from applicationDB import Post
import barCode
import json, boto3
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func, distinct, text, update
from sqlalchemy.sql import label
import re
import random
import pandas as pd
import pprint

def subjects(class_val):
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id=SchoolProfile.query.with_entities(SchoolProfile.board_id).filter_by(school_id=teacher_id.school_id).first()
    subject_id=Topic.query.with_entities(Topic.subject_id).distinct().filter_by(class_val=class_val,board_id=board_id).all()
    subject_name_list=[]
    for id in subject_id:
        subject_name=MessageDetails.query.filter_by(msg_id=id).first()
        if subject_name in subject_name_list:
            continue
        subject_name_list.append(subject_name)
    subjectArray = []
    
    for subject in subject_name_list:
        subjectObj = {}
        subjectObj['subject_id'] = subject.msg_id
        subjectObj['subject_name'] = subject.description
        subjectArray.append(subjectObj)

    return subjectArray

def subjectPerformance(class_val,school_id):
    board_id=SchoolProfile.query.with_entities(SchoolProfile.board_id).filter_by(school_id=school_id).first()
    subject_id=Topic.query.with_entities(Topic.subject_id).distinct().filter_by(class_val=class_val,board_id=board_id).all()
    subject_name_list=[]
    for id in subject_id:
        subject_name=MessageDetails.query.filter_by(msg_id=id).first()
        if subject_name in subject_name_list:
            continue
        subject_name_list.append(subject_name)
    subjectArray = []

    for subject in subject_name_list:
        subjectObj = {}
        subjectObj['subject_id'] = subject.msg_id
        subjectObj['subject_name'] = subject.description
        subjectObj['subject_marks'] = random.randint(0,100)
        subjectObj['subject_total_marks'] = 100
        subjectObj['subject_avg_marks'] = subjectObj['subject_marks']
        subjectObj['subject_class_avg'] = random.randint(70,100)
        subjectArray.append(subjectObj)

    return subjectArray



def topics(class_val,subject_id):
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    board_id=SchoolProfile.query.with_entities(SchoolProfile.board_id).filter_by(school_id=teacher_id.school_id).first()
    topic_list=Topic.query.filter_by(class_val=class_val,subject_id=subject_id,board_id=board_id).all()

    topicArray=[]

    for topic in topic_list:
        topicObj={}
        topicObj['topic_id']=topic.topic_id
        topicObj['topic_name']=topic.topic_name
        topicArray.append(topicObj)
    
    return topicArray

def signs3Folder(folder,filetype):
    teacher_id=TeacherProfile.query.filter_by(user_id=current_user.id).first()
    school_id=teacher_id.school_id
    if folder == 'student_profile':
        return "school_data/school_id_"+str(school_id)+"/"+folder
    elif folder == 'question_references':
        if filetype == 'image/jpeg' or filetype == 'image/png':
            return folder+"/images"
    elif folder == 'school_profile':
        return "school_data/school_id_"+str(school_id)+"/"+folder
        



    
