import os

class Config:
   
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key'

    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False



