from flask import Flask, render_template, g, request, abort, redirect, url_for
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from sqlalchemy import inspect, text
from config import Config

from models import db, User, School, sync_school_activation_with_subscription
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.discipline import discipline_bp
from routes.professor import professor_bp
from routes.secretary import secretary_bp
from routes.titulaire import titulaire_bp
from url_utils import OIDConverter

app = Flask(__name__)
app.config.from_object(Config)
app.url_map.converters['oid'] = OIDConverter

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"
login_manager.session_protection = "basic"

# Protection CSRF globale (Flask-WTF). Chaque formulaire POST embarque son token
# via {{ csrf_token() }} dans le template.
from flask_wtf import CSRFProtect
csrf = CSRFProtect(app)


@app.before_request
def set_cookie_secure_flags():
    # Ne marque le cookie de session « Secure » que lorsque la connexion est
    # réellement chiffrée (HTTPS direct ou via proxy X-Forwarded-Proto).
    # Sur http://localhost (développement), un cookie Secure peut être ignoré
    # par le navigateur et provoquer des déconnexions aléatoires.
    secure = request.is_secure
    if request.headers.get('X-Forwarded-Proto') == 'https':
        secure = True
    app.config['SESSION_COOKIE_SECURE'] = secure
    app.config['REMEMBER_COOKIE_SECURE'] = secure

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(admin_bp, url_prefix='/<school_slug>/admin', name='school_admin')
app.register_blueprint(discipline_bp, url_prefix='/<school_slug>/discipline')
app.register_blueprint(professor_bp, url_prefix='/<school_slug>/professor')
app.register_blueprint(secretary_bp, url_prefix='/<school_slug>/secretary')
app.register_blueprint(titulaire_bp, url_prefix='/<school_slug>/titulaire')


@app.after_request
def apply_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
    response.headers.setdefault(
        'Content-Security-Policy',
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data: https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "connect-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'self'"
    )
    if request.is_secure:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response


def _ensure_bulletin_config_columns():
    inspector = inspect(db.engine)
    if 'bulletin_configs' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('bulletin_configs')}
    with db.engine.begin() as conn:
        if 'validated' not in columns:
            conn.execute(text('ALTER TABLE bulletin_configs ADD COLUMN validated BOOLEAN NOT NULL DEFAULT FALSE'))
        if 'validated_at' not in columns:
            conn.execute(text('ALTER TABLE bulletin_configs ADD COLUMN validated_at TIMESTAMP NULL'))
        if 'validated_by_user_id' not in columns:
            conn.execute(text('ALTER TABLE bulletin_configs ADD COLUMN validated_by_user_id INTEGER NULL'))
        if 'ige_number' not in columns:
            conn.execute(text('ALTER TABLE bulletin_configs ADD COLUMN ige_number VARCHAR(50) NULL'))


def _ensure_school_columns():
    inspector = inspect(db.engine)
    if 'schools' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('schools')}
    with db.engine.begin() as conn:
        if 'province' not in columns:
            conn.execute(text('ALTER TABLE schools ADD COLUMN province VARCHAR(120) NULL'))
        if 'city' not in columns:
            conn.execute(text('ALTER TABLE schools ADD COLUMN city VARCHAR(120) NULL'))
        if 'commune' not in columns:
            conn.execute(text('ALTER TABLE schools ADD COLUMN commune VARCHAR(120) NULL'))
        if 'bulletin_school_name' not in columns:
            conn.execute(text('ALTER TABLE schools ADD COLUMN bulletin_school_name VARCHAR(255) NULL'))
        if 'school_code' not in columns:
            conn.execute(text('ALTER TABLE schools ADD COLUMN school_code VARCHAR(50) NULL'))
        if 'other_denomination' not in columns:
            conn.execute(text('ALTER TABLE schools ADD COLUMN other_denomination VARCHAR(255) NULL'))
        if 'deliberation_message' not in columns:
            conn.execute(text('ALTER TABLE schools ADD COLUMN deliberation_message TEXT NULL'))


def _ensure_academic_year_columns():
    inspector = inspect(db.engine)
    if 'students' in inspector.get_table_names():
        columns = {column['name'] for column in inspector.get_columns('students')}
        with db.engine.begin() as conn:
            if 'academic_year' not in columns:
                conn.execute(text('ALTER TABLE students ADD COLUMN academic_year VARCHAR(30) NULL'))
            if 'student_id_number' not in columns:
                conn.execute(text('ALTER TABLE students ADD COLUMN student_id_number VARCHAR(80) NULL'))

    if 'grades' in inspector.get_table_names():
        columns = {column['name'] for column in inspector.get_columns('grades')}
        with db.engine.begin() as conn:
            if 'academic_year' not in columns:
                conn.execute(text('ALTER TABLE grades ADD COLUMN academic_year VARCHAR(30) NULL'))
            if 'flagged' not in columns:
                conn.execute(text('ALTER TABLE grades ADD COLUMN flagged BOOLEAN NOT NULL DEFAULT FALSE'))


def _ensure_student_is_promoted():
    inspector = inspect(db.engine)
    if 'students' not in inspector.get_table_names():
        return
    columns = {column['name'] for column in inspector.get_columns('students')}
    with db.engine.begin() as conn:
        if 'is_promoted' not in columns:
            conn.execute(text('ALTER TABLE students ADD COLUMN is_promoted BOOLEAN NOT NULL DEFAULT FALSE'))


def _ensure_bulletin_config_section_unique():
    inspector = inspect(db.engine)
    if 'bulletin_configs' not in inspector.get_table_names():
        return
    constraints = {c['name'] for c in inspector.get_unique_constraints('bulletin_configs')}
    indexes = {idx['name'] for idx in inspector.get_indexes('bulletin_configs')}
    with db.engine.begin() as conn:
        if 'unique_bulletin_config_per_level' in constraints:
            conn.execute(text('ALTER TABLE bulletin_configs DROP CONSTRAINT unique_bulletin_config_per_level'))
        if 'unique_bulletin_config_per_section_level' not in constraints and 'unique_bulletin_config_per_section_level' not in indexes:
            conn.execute(text('CREATE UNIQUE INDEX unique_bulletin_config_per_section_level ON bulletin_configs (school_id, section_id, level, academic_year)'))


def _ensure_attendance_columns():
    inspector = inspect(db.engine)
    if 'attendance_records' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('attendance_records')}
    with db.engine.begin() as conn:
        if 'section_id' not in columns:
            conn.execute(text('ALTER TABLE attendance_records ADD COLUMN section_id INTEGER NULL'))
        if 'period' not in columns:
            conn.execute(text('ALTER TABLE attendance_records ADD COLUMN period VARCHAR(30) NULL'))


def _ensure_exam_columns():
    inspector = inspect(db.engine)
    if 'exam_assignments' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('exam_assignments')}
    with db.engine.begin() as conn:
        if 'session_label' not in columns:
            conn.execute(text('ALTER TABLE exam_assignments ADD COLUMN session_label VARCHAR(120) NULL'))
        if 'start_date' not in columns:
            conn.execute(text('ALTER TABLE exam_assignments ADD COLUMN start_date VARCHAR(20) NULL'))
        if 'end_date' not in columns:
            conn.execute(text('ALTER TABLE exam_assignments ADD COLUMN end_date VARCHAR(20) NULL'))
        if 'period_label' in columns:
            conn.execute(text('ALTER TABLE exam_assignments DROP COLUMN period_label'))

    if 'exam_configs' in inspector.get_table_names():
        config_columns = {column['name'] for column in inspector.get_columns('exam_configs')}
        with db.engine.begin() as conn:
            if 'start_date' not in config_columns:
                conn.execute(text('ALTER TABLE exam_configs ADD COLUMN start_date DATE NULL'))
            if 'end_date' not in config_columns:
                conn.execute(text('ALTER TABLE exam_configs ADD COLUMN end_date DATE NULL'))
            if 'period_label' in config_columns:
                conn.execute(text('ALTER TABLE exam_configs DROP COLUMN period_label'))


def _ensure_user_roles():
    inspector = inspect(db.engine)
    if 'users' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('users')}
    with db.engine.begin() as conn:
        if 'qualification' not in columns:
            conn.execute(text('ALTER TABLE users ADD COLUMN qualification VARCHAR(120) NULL'))
        if 'journee_pedagogique' not in columns:
            conn.execute(text('ALTER TABLE users ADD COLUMN journee_pedagogique VARCHAR(120) NULL'))
        if 'titulariat_section_id' in columns and 'titulaire_section_id' not in columns:
            conn.execute(text('ALTER TABLE users RENAME COLUMN titulariat_section_id TO titulaire_section_id'))
        elif 'titulaire_section_id' not in columns:
            conn.execute(text('ALTER TABLE users ADD COLUMN titulaire_section_id INTEGER NULL'))

    if 'role' not in columns:
        return

    with db.engine.begin() as conn:
        has_legacy_cashier = conn.execute(
            text("SELECT 1 FROM users WHERE CAST(role AS TEXT) = 'cashier' LIMIT 1")
        ).scalar()
        if has_legacy_cashier:
            conn.execute(text("UPDATE users SET role = 'discipline' WHERE CAST(role AS TEXT) = 'cashier'"))

        has_legacy_titulariat = conn.execute(
            text("SELECT 1 FROM users WHERE CAST(role AS TEXT) = 'titulariat' LIMIT 1")
        ).scalar()
        if has_legacy_titulariat:
            conn.execute(text("UPDATE users SET role = 'titulaire' WHERE CAST(role AS TEXT) = 'titulariat'"))


def _ensure_user_schools_table():
    from models import user_schools
    inspector = inspect(db.engine)
    if 'user_schools' not in inspector.get_table_names():
        user_schools.create(bind=db.engine)


def _normalize_user_names():
    """Met tous les noms d'utilisateur en minuscules (préfixe le nom d'affichage)."""
    from models import User
    if 'users' not in inspect(db.engine).get_table_names():
        return
    with db.engine.begin():
        for user in User.query.all():
            if user.username != user.username.lower():
                print(f"Normalisation du nom d'utilisateur : {user.username} -> {user.username.lower()}")
                user.username = user.username.lower()
        db.session.commit()


@app.before_request
def ensure_schema():
    if not app.config.get('SCHEMA_INITIALIZED', False):
        db.create_all()
        _ensure_school_columns()
        _ensure_bulletin_config_columns()
        _ensure_academic_year_columns()
        _ensure_attendance_columns()
        _ensure_exam_columns()
        _ensure_user_roles()
        _ensure_user_schools_table()
        _ensure_student_is_promoted()
        _ensure_bulletin_config_section_unique()
        _normalize_user_names()
        from models import AcademicYear
        if not AcademicYear.query.first():
            db.session.add(AcademicYear(name="2025 - 2026", is_active=True))
            db.session.commit()
        from models import User
        import os
        import secrets
        import string
        super_admin = User.query.filter_by(role='super_admin').first()
        if not super_admin:
            default_admin_password = os.environ.get('SUPERADMIN_PASSWORD') or ''.join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(16)
            )
            super_admin = User(
                username='superadmin',
                role='super_admin',
                full_name='Super Administrateur',
                email='superadmin@gescoapp.com',
                must_change_password=True,
            )
            super_admin.set_password(default_admin_password)
            db.session.add(super_admin)
            db.session.commit()
            if os.environ.get('SUPERADMIN_PASSWORD'):
                app.logger.warning('Super admin créé à partir de la variable SUPERADMIN_PASSWORD.')
            else:
                app.logger.warning(f'Super admin créé avec un mot de passe aléatoire (une seule fois affiché) : {default_admin_password}')
        elif os.environ.get('SUPERADMIN_PASSWORD'):
            if not super_admin.check_password(os.environ['SUPERADMIN_PASSWORD']):
                super_admin.set_password(os.environ['SUPERADMIN_PASSWORD'])
                db.session.commit()
                app.logger.warning('Mot de passe du super admin mis à jour via SUPERADMIN_PASSWORD.')
        app.config['SCHEMA_INITIALIZED'] = True


@app.url_value_preprocessor
def pull_school_slug(endpoint, values):
    if not values:
        return
    school_slug = values.get('school_slug', None)  # Don't pop for school_home route
    if school_slug:
        school = School.query.filter_by(slug=school_slug).first()
        if not school:
            abort(404)
        sync_school_activation_with_subscription(school)
        db.session.commit()
        g.school = school
        g.school_slug = school_slug
    else:
        g.school = None
        g.school_slug = None

@app.url_defaults
def add_school_slug(endpoint, values):
    if 'school_slug' in values:
        return
    if not hasattr(g, 'school_slug') or not g.school_slug:
        return
    if endpoint.startswith(('admin.', 'discipline.', 'professor.', 'secretary.', 'titulaire.')):
        values['school_slug'] = g.school_slug

@app.context_processor
def inject_academic_years():
    from models import AcademicYear
    from flask import session
    
    # Résoudre l'année courante
    if 'academic_year' not in session:
        active = AcademicYear.query.filter_by(is_active=True).first()
        if active:
            session['academic_year'] = active.name
        else:
            latest = AcademicYear.query.order_by(AcademicYear.name.desc()).first()
            if latest:
                session['academic_year'] = latest.name
            else:
                session['academic_year'] = "2025 - 2026"
                
    all_years = [y.name for y in AcademicYear.query.order_by(AcademicYear.name.desc()).all()]
    if not all_years:
        all_years = ["2025 - 2026"]
        
    return {
        'current_academic_year': session.get('academic_year', '2025 - 2026'),
        'all_academic_years': all_years
    }


@app.context_processor
def inject_oid_helpers():
    from url_utils import encode_id
    return {'oid': encode_id}


@app.context_processor
def inject_class_denomination():
    from routes.attendance_utils import class_denomination
    return {'class_denomination': class_denomination}


@app.context_processor
def inject_secretary_dashboard_url():
    secretary_dashboard_url = None
    if current_user.is_authenticated and current_user.school and current_user.school.slug:
        secretary_dashboard_url = url_for('secretary.dashboard', school_slug=current_user.school.slug)

    return {
        'secretary_dashboard_url': secretary_dashboard_url
    }


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/set-academic-year', methods=['POST'])
def set_academic_year():
    from flask import session
    year = request.form.get('academic_year')
    if year:
        session['academic_year'] = year
    ref = request.referrer
    if ref and request.host in ref:
        return redirect(ref)
    return redirect(url_for('index'))

@app.route('/<school_slug>/')
def school_home(school_slug):
    school = School.query.filter_by(slug=school_slug, is_active=True).first_or_404()
    if current_user.is_authenticated:
        if current_user.is_super_admin():
            return redirect(url_for('admin.dashboard', school_slug=school_slug))
        if current_user.school and current_user.school.slug == school_slug:
            return redirect(url_for('auth.redirect_by_role'))
        return redirect(url_for('auth.login'))
    return render_template('login.html', school=school)

@app.route('/test-api')
def test_api():
    return render_template('test_api.html')

if __name__ == '__main__':
    # Prevent accidental debug/weak-secret startup in production
    if not app.config.get('SECRET_KEY'):
        raise RuntimeError('SECRET_KEY environment variable must be set before starting the application')
    app.run()
