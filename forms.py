from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField, IntegerField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])

class UserForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Rôle', choices=[('admin', 'Admin'), ('secretaire', 'Secrétaire'), ('professeur', 'Professeur'), ('discipline', 'Discipline')], validators=[DataRequired()])
    school_id = IntegerField('ID École', validators=[Optional()])

class SchoolForm(FlaskForm):
    name = StringField('Nom de l\'école', validators=[DataRequired(), Length(max=100)])
    address = StringField('Adresse', validators=[Optional(), Length(max=200)])
    year_start = IntegerField('Année de début', validators=[Optional()])
    year_end = IntegerField('Année de fin', validators=[Optional()])

class ClassForm(FlaskForm):
    name = StringField('Nom de la classe', validators=[DataRequired(), Length(max=50)])
    school_id = IntegerField('ID École', validators=[DataRequired()])
    level = StringField('Niveau', validators=[Optional(), Length(max=20)])
    capacity = IntegerField('Capacité', validators=[Optional(), NumberRange(min=1)])

class StudentForm(FlaskForm):
    name = StringField('Nom complet', validators=[DataRequired(), Length(max=100)])
    birth_date = DateField('Date de naissance', validators=[Optional()])
    class_id = IntegerField('ID Classe', validators=[Optional()])
    parent_phone = StringField('Téléphone parent', validators=[Optional(), Length(max=20)])
    parent_email = StringField('Email parent', validators=[Optional(), Email()])

class GradeForm(FlaskForm):
    student_id = IntegerField('ID Étudiant', validators=[DataRequired()])
    subject_id = IntegerField('ID Matière', validators=[DataRequired()])
    value = FloatField('Note', validators=[DataRequired(), NumberRange(min=0, max=20)])
    period = StringField('Période', validators=[Optional(), Length(max=50)])

class AttendanceForm(FlaskForm):
    student_id = IntegerField('ID Étudiant', validators=[DataRequired()])
    class_id = IntegerField('ID Classe', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    status = SelectField('Statut', choices=[('present', 'Présent'), ('absent', 'Absent'), ('retard', 'En retard')], validators=[DataRequired()])

class ConductForm(FlaskForm):
    student_id = IntegerField('ID Étudiant', validators=[DataRequired()])
    type = StringField('Type', validators=[DataRequired(), Length(max=50)])
    severity = IntegerField('Sévérité', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])

class IncidentForm(FlaskForm):
    student_id = IntegerField('ID Étudiant', validators=[DataRequired()])
    category = StringField('Catégorie', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional()])
    severity = StringField('Sévérité', validators=[Optional(), Length(max=20)])
