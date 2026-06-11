from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

# Table d'association Many-to-Many entre Parents (Utilisateurs) et Élèves
parent_student = db.Table('parent_student',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('students.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    """Modèle pour les utilisateurs de la plateforme avec sécurité renforcée."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) # admin, secretaire, professeur, discipline, parent
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Sécurité supplémentaire
    is_2fa_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    last_password_change = db.Column(db.DateTime, default=datetime.utcnow)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_login_attempt = db.Column(db.DateTime)
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class School(db.Model):
    """Modèle pour une école enregistrée sur la plateforme."""
    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    logo = db.Column(db.String(255))
    province = db.Column(db.String(50))
    ville = db.Column(db.String(50))
    commune = db.Column(db.String(50))
    code = db.Column(db.String(20)) # Code de l'école
    year_start = db.Column(db.Integer)
    year_end = db.Column(db.Integer)
    config_json = db.Column(db.Text) # Configuration spécifique (ex: périodes, maxima)

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

class Student(db.Model):
    """Modèle pour les élèves."""
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10)) # M ou F
    birth_date = db.Column(db.Date)
    birth_place = db.Column(db.String(100))
    permanent_id = db.Column(db.String(20))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    parent_phone = db.Column(db.String(20))
    parent_email = db.Column(db.String(100))

    grades = db.relationship('Grade', backref='student', lazy=True)
    attendance = db.relationship('Attendance', backref='student', lazy=True)
    conduct = db.relationship('Conduct', backref='student', lazy=True)
    incidents = db.relationship('Incident', backref='student', lazy=True)
    bulletins = db.relationship('Bulletin', backref='student', lazy=True)

    parents = db.relationship('User', secondary=parent_student, backref=db.backref('children', lazy='dynamic'))

class Subject(db.Model):
    """Modèle pour les matières enseignées."""
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100)) # Ex: Sciences, Langues
    sub_domain = db.Column(db.String(100))
    coefficient = db.Column(db.Integer, default=1)
    max_1p = db.Column(db.Float)
    max_2p = db.Column(db.Float)
    max_exa1 = db.Column(db.Float)
    max_3p = db.Column(db.Float)
    max_4p = db.Column(db.Float)
    max_exa2 = db.Column(db.Float)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)

class Teacher(db.Model):
    """Modèle pour l'attribution des cours aux professeurs."""
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)

    # Relationships
    subject = db.relationship('Subject', backref='teachers')
    class_level = db.relationship('Class', backref='teachers')
    user = db.relationship('User', backref='teacher_profile')
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
    """Modèle pour les présences quotidiennes."""
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False) # present, absent, retard
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Conduct(db.Model):
    """Modèle pour le suivi de la conduite."""
    __tablename__ = 'conduct'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    type = db.Column(db.String(50)) # Conduite générale, Effort, etc.
    severity = db.Column(db.Integer) # 1 à 5
    description = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Incident(db.Model):
    """Modèle pour les incidents disciplinaires."""
    __tablename__ = 'incidents'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Bagarre, Vol, etc.
    description = db.Column(db.Text)
    evidence = db.Column(db.String(255)) # Lien vers une photo ou preuve
    severity = db.Column(db.String(20)) # mineur, majeur, critique
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bulletin(db.Model):
    """Modèle pour l'archivage des bulletins générés."""
    __tablename__ = 'bulletins'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    period = db.Column(db.String(20), nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_path = db.Column(db.String(255), nullable=False)

class AuditLog(db.Model):
    """Modèle pour le journal d'audit de sécurité."""
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    """Modèle pour la communication Professeur-Parent."""
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
