import pytest
from app import create_app
from models import db, User, School, Class, Student, Subject, Teacher
from flask_bcrypt import generate_password_hash
from datetime import timedelta
import os

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret'
    JWT_SECRET_KEY = 'jwt-test-secret'
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    JWT_EXPIRATION_DELTA = timedelta(seconds=3600)
    JWT_REFRESH_EXPIRATION_DELTA = timedelta(seconds=86400)

@pytest.fixture
def app():
    """Crée une instance de l'application pour les tests."""
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app):
    """Un client de test pour effectuer des requêtes HTTP."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Un runner pour les commandes CLI."""
    return app.test_cli_runner()

@pytest.fixture
def db_session(app):
    """Initialise la base de données pour chaque test."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.drop_all()

@pytest.fixture
def test_data(db_session):
    """Popule la DB avec des données de base pour les tests."""
    # École
    school = School(name="Ecole Test", year_start=2024, year_end=2025)
    db_session.add(school)
    db_session.commit()

    # Utilisateurs (Rôles)
    roles = ['admin', 'secretaire', 'professeur', 'discipline']
    users = {}
    for role in roles:
        user = User(
            username=f"test_{role}",
            email=f"{role}@test.com",
            password_hash=generate_password_hash("TestPassword123!").decode('utf-8'),
            role=role,
            school_id=school.id
        )
        db_session.add(user)
        users[role] = user

    db_session.commit()

    # Classe
    cls = Class(name="7è EB", level="7", section="EB", school_id=school.id)
    db_session.add(cls)
    db_session.commit()

    # Élève
    student = Student(name="Eleve Test", gender="M", class_id=cls.id)
    db_session.add(student)
    db_session.commit()

    # Matière
    subject = Subject(name="Math", class_id=cls.id, max_1p=20, max_exa1=40)
    db_session.add(subject)
    db_session.commit()

    # Assignation Prof
    teacher = Teacher(user_id=users['professeur'].id, class_id=cls.id, subject_id=subject.id)
    db_session.add(teacher)
    db_session.commit()

    return {
        'school': school,
        'users': users,
        'class': cls,
        'student': student,
        'subject': subject,
        'teacher': teacher
    }
