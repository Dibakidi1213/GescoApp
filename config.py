import os
from datetime import timedelta

class Config:
    """Configuration de base pour l'application."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-a-changer-en-prod'

    # Base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or         'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance/jnc_kalasi.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sécurité & JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-dev-secret'
    JWT_EXPIRATION_DELTA = timedelta(hours=1)
    JWT_REFRESH_EXPIRATION_DELTA = timedelta(days=30)

    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day; 50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"

    # Mail (Optionnel)
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # Uploads (Bulletins PDF)
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'bulletins')
