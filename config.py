import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'postgres://bpcleitmuybslc:3e37d8b9549fe032323c47b9a38018ac27a0f0ad4516e81c2fc7a87dfc5f4451@ec2-50-19-224-165.compute-1.amazonaws.com:5432/d1mrsoqu6qnsmj?sslmode=require'
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    POSTS_PER_PAGE = 3