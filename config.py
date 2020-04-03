import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # staging url    
    # DATABASE_URL = os.environ.get('DATABASE_URL')   
    DATABASE_URL = "postgres://uf6as3sigg3bn5:p5203252e9b23d6af79a04f794f38041eed7e7114fbe40776d843cce06258783f@alllearnstaginginstanceid.c8et4fo3vjlv.ap-south-1.rds.amazonaws.com/d2vtb4it0a1hst"   
    # DATABASE_URL = "postgres://u3oeikbfat3t4k:p3c0fc3ffa5a59d4a2680634fbf7f4c83fef3d8187462d99ac821cb406ba79fbc@d5u4rapacupf31.c8et4fo3vjlv.ap-south-1.rds.amazonaws.com/d5u4rapacupf31"
    EMAIL_API_KEY = os.environ.get('EMAIL_API_KEY')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL + '?sslmode=require'
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT') 
    POSTS_PER_PAGE = 10
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration")
    ALLLEARN_INTERNAL_KEY = os.environ.get('ALLLEARN_INTERNAL_KEY')
    # IMPACT_HOST = os.environ.get('IMPACT_HOST')
    #ALLLEARN_INTERNAL_KEY = "1QAZXSW2JJJJ4RFVLI8761919ASDF654ASDF5D5D222"
    IMPACT_HOST = "alllearnimpactstaging.herukoapp.com"
    # IMPACT_HOST = "http://127.0.0.1:8000"