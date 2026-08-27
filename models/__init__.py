import re
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


def slugify(value):
    slug = re.sub(r'[^a-z0-9]+', '-', str(value or '').strip().lower())
    return slug.strip('-') or 'school'


db = SQLAlchemy()


user_schools = db.Table(
    'user_schools',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('school_id', db.Integer, db.ForeignKey('schools.id'), primary_key=True),
)


class School(db.Model):
    __tablename__ = 'schools'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=True)
    address = db.Column(db.String(255))
    province = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    logo = db.Column(db.String(255))
    city = db.Column(db.String(120), nullable=True)
    commune = db.Column(db.String(120), nullable=True)
    bulletin_school_name = db.Column(db.String(255), nullable=True)
    school_code = db.Column(db.String(50), nullable=True)
    slogan = db.Column(db.String(255), nullable=True)
    other_denomination = db.Column(db.String(255), nullable=True)
    study_prefect_name = db.Column(db.String(120), nullable=True)
    deliberation_message = db.Column(db.Text, nullable=True)
    ministry = db.Column(db.String(255), nullable=True, default="MINISTERE DE L'ENSEIGNEMENT PRIMAIRE, SECONDAIRE ET TECHNIQUE", server_default=db.text("'MINISTERE DE L''ENSEIGNEMENT PRIMAIRE, SECONDAIRE ET TECHNIQUE'"))
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.text('true'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    users = db.relationship('User', back_populates='school', lazy='dynamic')
    sections = db.relationship('Section', back_populates='school', lazy='dynamic')
    courses = db.relationship('Course', back_populates='school', lazy='dynamic')
    students = db.relationship('Student', back_populates='school', lazy='dynamic')
    grades = db.relationship('Grade', back_populates='school', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='school', lazy='dynamic')
    bulletin_configs = db.relationship('BulletinConfig', back_populates='school', lazy='dynamic')
    attendance_records = db.relationship('AttendanceRecord', back_populates='school', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='school', lazy='dynamic')
    holidays = db.relationship('SchoolHoliday', back_populates='school', lazy='dynamic')
    subscriptions = db.relationship('SchoolSubscription', back_populates='school', lazy='dynamic')
    remote_support_tickets = db.relationship('RemoteSupportTicket', back_populates='school', lazy='dynamic')
    exam_rooms = db.relationship('ExamRoom', back_populates='school', lazy='dynamic')
    exam_assignments = db.relationship('ExamAssignment', back_populates='school', lazy='dynamic')
    exam_configs = db.relationship('ExamConfig', back_populates='school', lazy='dynamic')


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)  # Nullable pour super_admin
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('super_admin', 'school_admin', 'secretary', 'discipline', 'professor', 'titulaire', name='role_enum'), nullable=False)
    titulaire_section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Added for user management
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.text('true'))  # For blocking/unblocking
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    login_failed_attempts = db.Column(db.Integer, default=0, nullable=False)
    last_failed_login_at = db.Column(db.DateTime, nullable=True)
    last_failed_login_ip = db.Column(db.String(45), nullable=True)
    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)
    qualification = db.Column(db.String(120), nullable=True)
    journee_pedagogique = db.Column(db.String(120), nullable=True)

    school = db.relationship('School', back_populates='users')
    titulaire_section = db.relationship('Section', foreign_keys=[titulaire_section_id], backref=db.backref('titulaire_users', lazy='dynamic'))
    linked_schools = db.relationship('School', secondary=user_schools, backref=db.backref('linked_users', lazy='dynamic'))
    courses = db.relationship('Course', back_populates='professor', lazy='dynamic')
    attendance_records = db.relationship('AttendanceRecord', foreign_keys='AttendanceRecord.professor_id', back_populates='professor', lazy='dynamic')
    created_subscriptions = db.relationship('SchoolSubscription', foreign_keys='SchoolSubscription.created_by_user_id', back_populates='created_by_user', lazy='dynamic')
    validated_subscription_payments = db.relationship('SchoolSubscriptionPayment', foreign_keys='SchoolSubscriptionPayment.confirmed_by_user_id', back_populates='confirmed_by_user', lazy='dynamic')
    opened_support_tickets = db.relationship('RemoteSupportTicket', foreign_keys='RemoteSupportTicket.created_by_user_id', back_populates='created_by_user', lazy='dynamic')
    handled_support_tickets = db.relationship('RemoteSupportTicket', foreign_keys='RemoteSupportTicket.handled_by_user_id', back_populates='handled_by_user', lazy='dynamic')
    received_notifications = db.relationship('Notification', foreign_keys='Notification.recipient_id', back_populates='recipient', lazy='dynamic')
    sent_notifications = db.relationship('Notification', foreign_keys='Notification.actor_id', back_populates='actor', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_super_admin(self):
        return self.role == 'super_admin'

    def is_school_admin(self):
        return self.role == 'school_admin'

    def is_admin(self):
        return self.role in ['super_admin', 'school_admin']

    def is_secretary(self):
        return self.role == 'secretary'

    def is_cashier(self):
        return self.role == 'cashier'

    def is_discipline(self):
        return self.role == 'discipline'

    def is_professor(self):
        return self.role == 'professor'

    def is_titulaire(self):
        return self.role == 'titulaire'

    def is_secretaire(self):
        return self.role == 'secretary'

    def accessible_schools(self):
        """Écoles accessibles à l'utilisateur.

        Super admin : toutes les écoles.
        Professeur : son école d'attache + les écoles où il est explicitement
        lié (user_schools) + les écoles où il enseigne (cours attribués).
        Autres rôles : son école d'attache uniquement.
        """
        if self.is_super_admin():
            return School.query.order_by(School.name).all()

        school_ids = set()
        if self.school_id:
            school_ids.add(self.school_id)
        if self.is_professor():
            from models import Course
            course_school_ids = [
                row[0] for row in Course.query.filter(
                    Course.professor_id == self.id,
                    Course.school_id.isnot(None)
                ).with_entities(Course.school_id).distinct().all()
            ]
            school_ids.update(course_school_ids)
        school_ids.update(school.id for school in self.linked_schools)

        if not school_ids:
            return []
        return School.query.filter(School.id.in_(school_ids), School.is_active.is_(True)).order_by(School.name).all()

    def can_access_school(self, school_id):
        """Retourne True si l'utilisateur peut accéder à l'école donnée."""
        if self.is_super_admin():
            return True
        return any(school.id == school_id for school in self.accessible_schools())


class Section(db.Model):
    __tablename__ = 'sections'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    class_name = db.Column(db.String(20), nullable=False)

    school = db.relationship('School', back_populates='sections')
    students = db.relationship('Student', back_populates='section', lazy='dynamic')
    courses = db.relationship('Course', back_populates='section', lazy='dynamic')


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    professor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('bulletin_branches.id'), nullable=True)

    school = db.relationship('School', back_populates='courses')
    section = db.relationship('Section', back_populates='courses')
    professor = db.relationship('User', back_populates='courses')
    branch = db.relationship('BulletinBranch')
    grades = db.relationship('Grade', back_populates='course', lazy='dynamic')
    attendance_records = db.relationship('AttendanceRecord', back_populates='course', lazy='dynamic')


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    place_of_birth = db.Column(db.String(120))
    birth_date = db.Column(db.Date)
    gender = db.Column(db.Enum('M', 'F', name='gender_enum'), default='M')
    father_name = db.Column(db.String(120))
    mother_name = db.Column(db.String(120))
    parent_phone = db.Column(db.String(50))
    student_id_number = db.Column(db.String(80))
    serial_number = db.Column(db.String(80))
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    photo_url = db.Column(db.String(255))
    academic_year = db.Column(db.String(30), nullable=True)
    is_promoted = db.Column(db.Boolean, default=False, nullable=False, server_default=db.text('false'))
    registered_at = db.Column(db.DateTime, server_default=db.func.now())

    school = db.relationship('School', back_populates='students')
    section = db.relationship('Section', back_populates='students')
    grades = db.relationship('Grade', back_populates='student', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='student', lazy='dynamic')
    attendance_records = db.relationship('AttendanceRecord', back_populates='student', lazy='dynamic')

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def display_name(self):
        return f"{self.last_name} {self.first_name}".strip()

    def generate_slug(self):
        return slugify(self.full_name())


class Grade(db.Model):
    __tablename__ = 'grades'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    period = db.Column(db.String(30), nullable=False, default='P1', server_default=db.text("'P1'"))
    value = db.Column(db.Numeric(5, 2), nullable=False)
    submitted = db.Column(db.Boolean, default=False, nullable=False, server_default=db.text('FALSE'))
    submitted_at = db.Column(db.DateTime, nullable=True)
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    academic_year = db.Column(db.String(30), nullable=True)
    flagged = db.Column(db.Boolean, default=False, nullable=False, server_default=db.text('FALSE'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    school = db.relationship('School', back_populates='grades')
    student = db.relationship('Student', back_populates='grades')
    course = db.relationship('Course', back_populates='grades')
    submitted_by_user = db.relationship('User', foreign_keys=[submitted_by])


class ConductGrade(db.Model):
    __tablename__ = 'conduct_grades'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    academic_year = db.Column(db.String(30), nullable=True)
    period = db.Column(db.String(30), nullable=False) # '1èP', '2èP', '3èP', '4èP'
    value = db.Column(db.String(10), nullable=False) # 'E', 'TB', etc.

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    school = db.relationship('School')
    student = db.relationship('Student')
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'academic_year', 'period', name='unique_student_conduct'),
    )


class LoginHistory(db.Model):
    __tablename__ = 'login_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    login_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    user_agent = db.Column(db.String(255), nullable=True)
    success = db.Column(db.Boolean, nullable=False, default=True)
    
    user = db.relationship('User', backref=db.backref('login_history', lazy='dynamic'))
    school = db.relationship('School', backref=db.backref('login_history', lazy='dynamic'))


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for system actions
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    action_type = db.Column(db.String(50), nullable=False)  # e.g., 'grade_update', 'user_create', 'settings_change'
    action_description = db.Column(db.String(255), nullable=False)
    related_model = db.Column(db.String(50), nullable=True)  # e.g., 'Grade', 'User', 'School'
    related_id = db.Column(db.Integer, nullable=True)  # ID of the related record
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    
    user = db.relationship('User', backref=db.backref('activity_log', lazy='dynamic'))
    school = db.relationship('School', backref=db.backref('activity_log', lazy='dynamic'))


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notification_type = db.Column(db.String(50), nullable=False, default='general',     server_default=db.text("'general'"))
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text('false'))
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    school = db.relationship('School', back_populates='notifications')
    recipient = db.relationship('User', foreign_keys=[recipient_id], back_populates='received_notifications')
    actor = db.relationship('User', foreign_keys=[actor_id], back_populates='sent_notifications')


class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    period = db.Column(db.String(30), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='present', server_default=db.text("'present'"))
    note = db.Column(db.String(255), nullable=True)
    academic_year = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    school = db.relationship('School', back_populates='attendance_records')
    section = db.relationship('Section')
    course = db.relationship('Course', back_populates='attendance_records')
    student = db.relationship('Student', back_populates='attendance_records')
    professor = db.relationship('User', foreign_keys=[professor_id], back_populates='attendance_records')

    __table_args__ = (
        db.UniqueConstraint(
            'school_id', 'course_id', 'student_id', 'attendance_date', 'academic_year',
            name='unique_attendance_record'
        ),
    )


class SchoolHoliday(db.Model):
    __tablename__ = 'school_holidays'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    holiday_date = db.Column(db.Date, nullable=False)
    label = db.Column(db.String(120), nullable=False)
    academic_year = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    school = db.relationship('School', back_populates='holidays')

    __table_args__ = (
        db.UniqueConstraint('school_id', 'holiday_date', name='unique_school_holiday_date'),
    )


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    concept = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    school = db.relationship('School', back_populates='payments')
    student = db.relationship('Student', back_populates='payments')


class BulletinConfig(db.Model):
    __tablename__ = 'bulletin_configs'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    level = db.Column(db.String(50), nullable=False)
    ige_number = db.Column(db.String(50), nullable=True)  # Format: IGE/PS/026
    academic_year = db.Column(db.String(30), nullable=True)
    validated = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text('false'))
    validated_at = db.Column(db.DateTime, nullable=True)
    validated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    school = db.relationship('School', back_populates='bulletin_configs')
    section = db.relationship('Section')
    validated_by_user = db.relationship('User', foreign_keys=[validated_by_user_id])
    branches = db.relationship('BulletinBranch', back_populates='config', cascade='all, delete-orphan', lazy='dynamic')

    __table_args__ = (db.UniqueConstraint('school_id', 'section_id', 'level', 'academic_year', name='unique_bulletin_config_per_section_level'),)
    
    def generate_ige_number(self):
        """Generate IGE number in format IGE/[SECTION]/[NUMERO]"""
        if not self.section:
            return None
        
        # Get section abbreviation (e.g., "PS" from "Primaire Scientifique")
        section_abbr = self._get_section_abbreviation(self.section.name)
        
        # Get next number for this section in this school
        next_num = self._get_next_ige_sequence(section_abbr)
        
        # Format: IGE/PS/026
        ige_num = f"IGE/{section_abbr}/{next_num:03d}"
        return ige_num
    
    @staticmethod
    def _get_section_abbreviation(section_name):
        """Convert section name to 2-letter abbreviation"""
        # Common mappings
        mappings = {
            'primaire scientifique': 'PS',
            'primaire littéraire': 'PL',
            'secondaire scientifique': 'SS',
            'secondaire littéraire': 'SL',
            'technique scientifique': 'TS',
            'technique littéraire': 'TL',
        }
        
        section_lower = section_name.lower().strip()
        for key, abbr in mappings.items():
            if key in section_lower:
                return abbr
        
        # Fallback: take first letter of first two words
        words = section_name.split()
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        elif len(words) == 1:
            return (section_name[:2]).upper()
        
        return "XX"
    
    def _get_next_ige_sequence(self, section_abbr):
        """Get next sequence number for this section"""
    # Query all IGE numbers for this section in this school that start with IGE/[abbr]/
        prefix = f"IGE/{section_abbr}/"
        
        # Get the highest number already used
        max_num = 0
        existing_configs = BulletinConfig.query.filter(
            BulletinConfig.school_id == self.school_id,
            BulletinConfig.ige_number.ilike(prefix + '%')
        ).all()
        
        for config in existing_configs:
            if config.ige_number:
                try:
                    # Extract number from IGE/PS/026
                    num_str = config.ige_number.split('/')[-1]
                    num = int(num_str)
                    max_num = max(max_num, num)
                except (ValueError, IndexError):
                    pass
        
        return max_num + 1


class BulletinBranch(db.Model):
    __tablename__ = 'bulletin_branches'

    id = db.Column(db.Integer, primary_key=True)
    config_id = db.Column(db.Integer, db.ForeignKey('bulletin_configs.id'), nullable=False)
    type = db.Column(db.String(20), default='branch')  # 'domain', 'subdomain', or 'branch'
    category = db.Column(db.String(30), default='general',     server_default=db.text("'general'")) # 'general', 'specifique', 'option'
    domain = db.Column(db.String(120))
    subdomain = db.Column(db.String(120))
    name = db.Column(db.String(120), nullable=False)
    order = db.Column(db.Integer, default=0)
    max_value = db.Column(db.Numeric(5, 2), default=20)
    
    # Individual maxima for each period and exam
    max_period_1 = db.Column(db.Numeric(5, 2), default=10)
    max_period_2 = db.Column(db.Numeric(5, 2), default=10)
    max_exam_1 = db.Column(db.Numeric(5, 2), default=10)
    max_period_3 = db.Column(db.Numeric(5, 2), default=10)
    max_period_4 = db.Column(db.Numeric(5, 2), default=10)
    max_exam_2 = db.Column(db.Numeric(5, 2), default=10)
    
    include_period_1 = db.Column(db.Boolean, default=True)
    include_period_2 = db.Column(db.Boolean, default=True)
    include_comp_1 = db.Column(db.Boolean, default=True)
    include_period_3 = db.Column(db.Boolean, default=True)
    include_period_4 = db.Column(db.Boolean, default=True)
    include_comp_2 = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    config = db.relationship('BulletinConfig', back_populates='branches')


class AcademicYear(db.Model):
    __tablename__ = 'academic_years'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)  # Ex: "2025 - 2026"
    is_active = db.Column(db.Boolean, default=False, nullable=False, server_default=db.text('false'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class SchoolSubscription(db.Model):
    __tablename__ = 'school_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    plan_name = db.Column(db.String(120), nullable=False)
    billing_cycle = db.Column(db.String(30), nullable=False, default='monthly', server_default=db.text("'monthly'"))
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0, server_default='0')
    currency = db.Column(db.String(10), nullable=False, default='USD', server_default=db.text("'USD'"))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='pending_payment', server_default=db.text("'pending_payment'"))
    auto_renew = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text('false'))
    notes = db.Column(db.Text, nullable=True)
    activated_at = db.Column(db.DateTime, nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    school = db.relationship('School', back_populates='subscriptions')
    created_by_user = db.relationship('User', foreign_keys=[created_by_user_id], back_populates='created_subscriptions')
    payments = db.relationship('SchoolSubscriptionPayment', back_populates='subscription', lazy='dynamic', cascade='all, delete-orphan')


class SchoolSubscriptionPayment(db.Model):
    __tablename__ = 'school_subscription_payments'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('school_subscriptions.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0, server_default='0')
    currency = db.Column(db.String(10), nullable=False, default='USD', server_default=db.text("'USD'"))
    paid_on = db.Column(db.Date, nullable=False, default=date.today)
    reference = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(30), nullable=False, default='pending', server_default=db.text("'pending'"))
    note = db.Column(db.Text, nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    confirmed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    school = db.relationship('School')
    subscription = db.relationship('SchoolSubscription', back_populates='payments')
    confirmed_by_user = db.relationship('User', foreign_keys=[confirmed_by_user_id], back_populates='validated_subscription_payments')


class RemoteSupportTicket(db.Model):
    __tablename__ = 'remote_support_tickets'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    request_type = db.Column(db.String(30), nullable=False, default='maintenance', server_default=db.text("'maintenance'"))
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    preferred_contact = db.Column(db.String(120), nullable=True)
    remote_tool = db.Column(db.String(80), nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='open', server_default=db.text("'open'"))
    resolution_notes = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    handled_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    school = db.relationship('School', back_populates='remote_support_tickets')
    created_by_user = db.relationship('User', foreign_keys=[created_by_user_id], back_populates='opened_support_tickets')
    handled_by_user = db.relationship('User', foreign_keys=[handled_by_user_id], back_populates='handled_support_tickets')


def expire_school_subscriptions(school_id=None, reference_date=None):
    current_day = reference_date or date.today()
    query = SchoolSubscription.query.filter(
        SchoolSubscription.status == 'active',
        SchoolSubscription.end_date < current_day
    )
    if school_id is not None:
        query = query.filter(SchoolSubscription.school_id == school_id)

    touched_school_ids = set()
    for subscription in query.all():
        subscription.status = 'expired'
        touched_school_ids.add(subscription.school_id)
    return touched_school_ids


def get_active_school_subscription(school_id, reference_date=None):
    current_day = reference_date or date.today()
    return SchoolSubscription.query.filter(
        SchoolSubscription.school_id == school_id,
        SchoolSubscription.status == 'active',
        SchoolSubscription.start_date <= current_day,
        SchoolSubscription.end_date >= current_day
    ).order_by(SchoolSubscription.end_date.desc(), SchoolSubscription.id.desc()).first()


def get_latest_school_subscription(school_id):
    return SchoolSubscription.query.filter(
        SchoolSubscription.school_id == school_id
    ).order_by(SchoolSubscription.end_date.desc(), SchoolSubscription.id.desc()).first()


def sync_school_activation_with_subscription(school, reference_date=None):
    if school is None:
        return None

    current_day = reference_date or date.today()
    expire_school_subscriptions(school_id=school.id, reference_date=current_day)
    active_subscription = get_active_school_subscription(school.id, reference_date=current_day)
    school.is_active = bool(active_subscription)
    return active_subscription


class DeliberationCriteria(db.Model):
    __tablename__ = 'deliberation_criteria'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    academic_year = db.Column(db.String(30), nullable=False)
    level_group = db.Column(db.String(50), nullable=False) # e.g., '1ere_2eme', '3eme_humanites', '4eme_humanites', '5eme_humanites'
    
    min_percentage_auto = db.Column(db.Numeric(5, 2), default=50)
    max_echecs_auto = db.Column(db.Integer, default=0)
    
    min_percentage_repechage = db.Column(db.Numeric(5, 2), default=50)
    max_echecs_repechage = db.Column(db.Integer, default=0) # 6, 4, 5
    
    min_score_specific_branch = db.Column(db.Numeric(5, 2), default=30)
    min_score_option_branch = db.Column(db.Numeric(5, 2), default=35)
    
    min_percentage_redoublement = db.Column(db.Numeric(5, 2), default=45)
    
    require_good_conduct = db.Column(db.Boolean, default=True)
    max_mauvaise_conduite = db.Column(db.Integer, default=2) # 2 MA ou 3 ME
    
    min_percentage_exclusion = db.Column(db.Numeric(5, 2), default=45)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    school = db.relationship('School')


class DeliberationResult(db.Model):
    __tablename__ = 'deliberation_results'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    academic_year = db.Column(db.String(30), nullable=False)
    period = db.Column(db.String(30), nullable=False) # '1èP', '2èP', 'EXA1', ..., 'ANNEE'
    
    total_percentage = db.Column(db.Numeric(5, 2), nullable=False)
    echecs_count = db.Column(db.Integer, default=0)
    
    decision = db.Column(db.String(50), nullable=False) # 'PASSAGE_AUTOMATIQUE', 'REPECHAGE', 'REDOUBLEMENT', 'EXCLUSION'
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    school = db.relationship('School')
    student = db.relationship('Student')
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'academic_year', 'period', name='unique_student_deliberation'),
    )


class ExamRoom(db.Model):
    __tablename__ = 'exam_rooms'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    benches = db.Column(db.Integer, nullable=False, default=0)
    students_per_bench = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    school = db.relationship('School', back_populates='exam_rooms')
    assignments = db.relationship('ExamAssignment', back_populates='room', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def capacity(self):
        return max(0, self.benches or 0) * max(0, self.students_per_bench or 0)


class ExamAssignment(db.Model):
    __tablename__ = 'exam_assignments'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    exam_room_id = db.Column(db.Integer, db.ForeignKey('exam_rooms.id'), nullable=False)
    academic_year = db.Column(db.String(30), nullable=False)
    macaron_number = db.Column(db.Integer, nullable=False)
    bench_number = db.Column(db.Integer, nullable=False)
    seat_number = db.Column(db.Integer, nullable=False)
    session_label = db.Column(db.String(120), nullable=True)
    start_date = db.Column(db.String(20), nullable=True)
    end_date = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    school = db.relationship('School', back_populates='exam_assignments')
    student = db.relationship('Student')
    room = db.relationship('ExamRoom', back_populates='assignments')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'academic_year', name='unique_student_exam_year'),
    )


class ExamConfig(db.Model):
    __tablename__ = 'exam_configs'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    academic_year = db.Column(db.String(30), nullable=False)
    session_label = db.Column(db.String(120), nullable=False, default='')
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    school = db.relationship('School', back_populates='exam_configs')

    __table_args__ = (
        db.UniqueConstraint('school_id', 'academic_year', name='uq_exam_config_school_year'),
    )
