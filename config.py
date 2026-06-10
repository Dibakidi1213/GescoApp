import os
from datetime import timedelta

class Config:
    # Clé secrète pour les sessions Flask et Flask-WTF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'votre-cle-secrete-par-defaut'

    # Configuration de la base de données (SQLite par défaut, PostgreSQL via variable d'env)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///school.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuration JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'votre-jwt-secret-par-defaut'
    JWT_EXPIRATION_DELTA = timedelta(hours=24)

    # Autres configurations
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max pour les uploads
