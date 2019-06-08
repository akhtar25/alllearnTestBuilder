import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    #SQLALCHEMY_DATABASE_URI = 'postgres://ewzyzkapvqdlmd:9a80347627991e0aa81ae530b5efd2d90ed615fcc939354684005e6ac4b01ac2@ec2-54-235-167-210.compute-1.amazonaws.com:5432/dfovuta8g4jtqr?sslmode=require'
    DATABASE_URL = os.environ.get('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL + '?sslmode=require'
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    POSTS_PER_PAGE = 10