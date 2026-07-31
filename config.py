import os
import re

basedir = os.path.abspath(os.path.dirname(__file__))


def fix_pg_uri(uri):
    """Fix common Render.com/Railway DATABASE_URL format for SQLAlchemy."""
    if uri and uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql://', 1)
    if uri and uri.startswith('postgresql://'):
        if 'sslmode' not in uri:
            separator = '&' if '?' in uri else '?'
            uri += f'{separator}sslmode=require'
    return uri


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change_me_in_local_dev_only')

    _raw_uri = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'gescoapp.db'))
    SQLALCHEMY_DATABASE_URI = fix_pg_uri(_raw_uri)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WEASYPRINT_BASE_URL = os.environ.get('WEASYPRINT_BASE_URL', 'http://127.0.0.1:5000')

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True

    ALLOW_RESTORE_DOWNLOAD = os.environ.get('ALLOW_RESTORE_DOWNLOAD', 'false').lower() == 'true'

    WTF_CSRF_TIME_LIMIT = 3600
