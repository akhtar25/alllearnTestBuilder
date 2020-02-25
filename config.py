import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # staging url    
    DATABASE_URL = os.environ.get('DATABASE_URL')   
    #DATABASE_URL = "postgres://uf6as3sigg3bn5:p5203252e9b23d6af79a04f794f38041eed7e7114fbe40776d843cce06258783f@alllearnstaginginstanceid.c8et4fo3vjlv.ap-south-1.rds.amazonaws.com/d2vtb4it0a1hst"   
    EMAIL_API_KEY = os.environ.get('EMAIL_API_KEY')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL + '?sslmode=require'
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    POSTS_PER_PAGE = 10
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration")