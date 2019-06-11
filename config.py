import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # staging url
    SQLALCHEMY_DATABASE_URI = 'postgres://hdajieypqzrwyj:581c3879bf85fc45e42b58bcfc644b4b317f3a3a5fc1fe02839e92bffd4cafa7@ec2-54-235-114-242.compute-1.amazonaws.com:5432/dkcim4jjhp6vt?sslmode=require'
    #DATABASE_URL = os.environ.get('DATABASE_URL')
    #SQLALCHEMY_DATABASE_URI = DATABASE_URL + '?sslmode=require'
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    POSTS_PER_PAGE = 10