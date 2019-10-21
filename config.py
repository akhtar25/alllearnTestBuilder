import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # staging url    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    #DATABASE_URL ="postgres://u3oeikbfat3t4k:p3c0fc3ffa5a59d4a2680634fbf7f4c83fef3d8187462d99ac821cb406ba79fbc@ec2-18-211-206-202.compute-1.amazonaws.com:5432/d5u4rapacupf31"
    SQLALCHEMY_DATABASE_URI = DATABASE_URL + '?sslmode=require'
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    POSTS_PER_PAGE = 10