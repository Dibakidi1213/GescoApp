from flask import Flask, render_template, g, request, abort, redirect, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from sqlalchemy import inspect, text
from config import Config

from models import db, User, School, sync_school_activation_with_subscription
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.professor import professor_bp
from routes.secretary import secretary_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(admin_bp, url_prefix='/<school_slug>/admin', name='school_admin')
app.register_blueprint(professor_bp, url_prefix='/<school_slug>/professor')
app.register_blueprint(secretary_bp, url_prefix='/<school_slug>/secretary')


def _ensure_bulletin_config_columns():
    inspector = inspect(db.engine)
    if 'bulletin_configs' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('bulletin_configs')}
    with db.engine.begin() as conn:
        if 'validated' not in columns:
            conn.execute(text('ALTER TABLE bulletin_configs ADD COLUMN validated BOOLEAN NOT NULL DEFAULT 0'))
        if 'validated_at' not in columns:
            conn.execute(text('ALTER TABLE bulletin_configs ADD COLUMN validated_at DATETIME NULL'))
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
        if 'academic_year' not in columns:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE grades ADD COLUMN academic_year VARCHAR(30) NULL'))


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


def _ensure_user_roles():
    inspector = inspect(db.engine)
    if 'users' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('users')}
    if 'role' not in columns:
        return

    with db.engine.begin() as conn:
        conn.execute(text("UPDATE users SET role = 'discipline' WHERE role = 'cashier'"))


@app.before_request
def ensure_schema():
    if not app.config.get('SCHEMA_INITIALIZED', False):
        db.create_all()
        _ensure_school_columns()
        _ensure_bulletin_config_columns()
        _ensure_academic_year_columns()
        _ensure_attendance_columns()
        _ensure_user_roles()
        from models import AcademicYear
        if not AcademicYear.query.first():
            db.session.add(AcademicYear(name="2025 - 2026", is_active=True))
            db.session.commit()
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
    if endpoint.startswith(('admin.', 'professor.', 'secretary.')):
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
            return render_template('login.html', school=school)
        if current_user.school and current_user.school.slug == school_slug:
            return redirect(url_for('auth.redirect_by_role'))
        return redirect(url_for('auth.login'))
    return render_template('login.html', school=school)

@app.route('/test-api')
def test_api():
    return render_template('test_api.html')

if __name__ == '__main__':
    app.run(debug=True)
