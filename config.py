import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # staging url  
    DATABASE_URL = os.environ.get("DATABASE_URL", None)
    #staging
    # DATABASE_URL = "postgres://uf6as3sigg3bn5:p5203252e9b23d6af79a04f794f38041eed7e7114fbe40776d843cce06258783f@alllearnstaginginstanceid.c8et4fo3vjlv.ap-south-1.rds.amazonaws.com/d2vtb4it0a1hst"   

    #prod
    # DATABASE_URL = "postgres://u3oeikbfat3t4k:p3c0fc3ffa5a59d4a2680634fbf7f4c83fef3d8187462d99ac821cb406ba79fbc@d5u4rapacupf31.c8et4fo3vjlv.ap-south-1.rds.amazonaws.com/d5u4rapacupf31"
    
    EMAIL_API_KEY = os.environ.get('EMAIL_API_KEY')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL + '?sslmode=require'
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT') 
    POSTS_PER_PAGE = 10
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_ID = "489889654406-6gu44r1h5l4ocjqe9hto2pski2m0ulm4.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration")
    ALLLEARN_INTERNAL_KEY = os.environ.get('ALLLEARN_INTERNAL_KEY')
    IMPACT_HOST = os.environ.get('IMPACT_HOST')
    #New value for anonymous user id passed as a dev for practice test pages
    ANONYMOUS_USERID = os.environ.get('ANONYMOUS_USERID')
    #ANONYMOUS_USERID = 886
    MODE = os.environ.get('MODE')
    #MODE = "TEST"
    
    #TEST CREDS
    ALLLEARN_CASHFREE_APP_ID =  os.environ.get('ALLLEARN_CASHFREE_APP_ID')
    ALLLEARN_CASHFREE_SECRET_KEY = os.environ.get('ALLLEARN_CASHFREE_SECRET_KEY')
     
    CASHFREE_API_TEST = "https://ces-gamma.cashfree.com"
    CASHFREE_API_PROD = "https://ces-api.cashfree.com"
    #ALLLEARN_INTERNAL_KEY = "1QAZXSW2JJJJ4RFVLI8761919ASDF654ASDF5D5D222"
    #IMPACT_HOST = "alllearnimpactstaging.herukoapp.com"
    #IMPACT_HOST = "http://127.0.0.1:8000"
