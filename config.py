import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change_me_securely')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'gescoapp.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WEASYPRINT_BASE_URL = 'http://127.0.0.1:5000'
