from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    """Modèle pour les utilisateurs de la plateforme."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) # admin, secretaire, professeur, discipline
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relation avec le profil professeur si applicable
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class School(db.Model):
    """Modèle pour les écoles."""
    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    logo = db.Column(db.String(200))
    config_json = db.Column(db.JSON) # Pour stocker des paramètres spécifiques
    year_start = db.Column(db.Integer) # Ex: 2023
    year_end = db.Column(db.Integer)   # Ex: 2024

    users = db.relationship('User', backref='school', lazy=True)
    classes = db.relationship('Class', backref='school', lazy=True)

class Class(db.Model):
    """Modèle pour les classes d'une école."""
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    level = db.Column(db.String(20))   # Ex: 1ère, 2ème, 6ème
    section = db.Column(db.String(50)) # Ex: Primaire, Humanités Scientifiques, etc.
    capacity = db.Column(db.Integer)

    students = db.relationship('Student', backref='current_class', lazy=True)
    subjects = db.relationship('Subject', backref='class_level', lazy=True)

class Student(db.Model):
    """Modèle pour les élèves."""
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10)) # M ou F
    birth_date = db.Column(db.Date)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    parent_phone = db.Column(db.String(20))
    parent_email = db.Column(db.String(100))

    grades = db.relationship('Grade', backref='student', lazy=True)
    attendance = db.relationship('Attendance', backref='student', lazy=True)
    conduct = db.relationship('Conduct', backref='student', lazy=True)
    incidents = db.relationship('Incident', backref='student', lazy=True)
    bulletins = db.relationship('Bulletin', backref='student', lazy=True)

class Subject(db.Model):
    """Modèle pour les matières/cours."""
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    coefficient = db.Column(db.Float, default=1.0)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))

    # Maxima par période pour le bulletin
    max_1p = db.Column(db.Float, default=10.0)
    max_2p = db.Column(db.Float, default=10.0)
    max_exa1 = db.Column(db.Float, default=20.0)
    max_3p = db.Column(db.Float, default=10.0)
    max_4p = db.Column(db.Float, default=10.0)
    max_exa2 = db.Column(db.Float, default=20.0)

    teachers = db.relationship('Teacher', backref='subject', lazy=True)

class Teacher(db.Model):
    """Modèle pour l'attribution des cours aux professeurs."""
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)

    grades = db.relationship('Grade', backref='teacher', lazy=True)

class Grade(db.Model):
    """Modèle pour les cotes (notes) des élèves."""
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20)) # 1èP, 2èP, EXA1, 3èP, 4èP, EXA2
    status = db.Column(db.String(20), default='draft') # draft, submitted, validated
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'))

class Attendance(db.Model):
    """Modèle pour le suivi des présences."""
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False) # present, absent, retard
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Conduct(db.Model):
    """Modèle pour l'évaluation de la conduite."""
    __tablename__ = 'conduct'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    type = db.Column(db.String(50)) # Ex: Application, Conduite, Propreté
    severity = db.Column(db.Integer) # Score ou niveau
    description = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Incident(db.Model):
    """Modèle pour les incidents disciplinaires."""
    __tablename__ = 'incidents'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    category = db.Column(db.String(50)) # Ex: Retard, Bagarre, Insolence
    description = db.Column(db.Text)
    evidence = db.Column(db.String(200)) # Chemin vers une preuve (image/doc)
    severity = db.Column(db.String(20)) # Mineur, Majeur, Critique
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bulletin(db.Model):
    """Modèle pour les bulletins générés."""
    __tablename__ = 'bulletins'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    period = db.Column(db.String(50)) # Trimestre 1, Semestre 1, Fin d'année
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_path = db.Column(db.String(200))

class AuditLog(db.Model):
    """Modèle pour les journaux d'audit et de sécurité."""
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False) # Ex: LOGIN, GRADE_UPDATE, DELETE_STUDENT
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
