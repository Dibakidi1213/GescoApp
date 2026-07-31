from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, School, LoginHistory, sync_school_activation_with_subscription

auth_bp = Blueprint('auth', __name__, template_folder='../templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/<school_slug>/login', methods=['GET', 'POST'])
def login(school_slug=None):
    if current_user.is_authenticated:
        return redirect(url_for('auth.redirect_by_role'))

    school = None
    if school_slug:
        school = School.query.filter_by(slug=school_slug, is_active=True).first_or_404()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')[:255] if request.headers.get('User-Agent') else None

        if user and user.check_password(password):
            if not user.is_super_admin() and user.school:
                sync_school_activation_with_subscription(user.school)
                db.session.commit()
            if not user.is_super_admin() and user.school and not user.school.is_active:
                flash("Cette école est désactivée. Connexion indisponible.", 'danger')
                db.session.add(LoginHistory(user_id=user.id, school_id=user.school_id, ip_address=ip_address, user_agent=user_agent, success=False))
                db.session.commit()
                return render_template('login.html', school=school)
            login_user(user)
            db.session.add(LoginHistory(user_id=user.id, school_id=user.school_id, ip_address=ip_address, user_agent=user_agent, success=True))
            user.last_login_at = db.func.now()
            user.last_login_ip = ip_address
            user.login_failed_attempts = 0
            db.session.commit()
            return redirect(url_for('auth.redirect_by_role'))

        if user:
            user.login_failed_attempts = (user.login_failed_attempts or 0) + 1
            user.last_failed_login_at = db.func.now()
            user.last_failed_login_ip = ip_address
            db.session.add(LoginHistory(user_id=user.id, school_id=user.school_id, ip_address=ip_address, user_agent=user_agent, success=False))
            db.session.commit()

        flash('Identifiants invalides.', 'danger')

    return render_template('login.html', school=school)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Déconnexion réussie.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/redirect')
@login_required
def redirect_by_role():
    if current_user.is_super_admin():
        return redirect(url_for('admin.dashboard'))

    if current_user.school and current_user.school.slug:
        school_slug = current_user.school.slug
        if current_user.is_school_admin() or current_user.is_secretary():
            return redirect(url_for('admin.dashboard', school_slug=school_slug))
        if current_user.is_professor():
            return redirect(url_for('professor.dashboard', school_slug=school_slug))
        if current_user.is_discipline():
            return redirect(url_for('discipline.dashboard', school_slug=school_slug))
        if current_user.role == 'cashier':
            return redirect(url_for('admin.discipline_redirect', school_slug=school_slug))

    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.is_admin():
        flash('Accès refusé.', 'danger')
        return redirect(url_for('auth.redirect_by_role'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        role = request.form['role']
        email = request.form.get('email')

        if current_user.is_super_admin():
            # Super admin: gestion des administrateurs d'école.
            if role != 'school_admin':
                flash("Le super administrateur peut créer uniquement des administrateurs d'école.", 'danger')
                return redirect(url_for('admin.register_user_redirect'))

            school_id = request.form.get('school_id')
            if not school_id:
                flash("Veuillez sélectionner une école.", 'warning')
                return redirect(url_for('admin.register_user_redirect'))

        elif current_user.is_school_admin():
            if role == 'super_admin':
                flash('Vous ne pouvez pas créer de super administrateur.', 'danger')
                return redirect(url_for('admin.register_user_redirect'))
            if role not in {'school_admin', 'secretary', 'professor', 'discipline'}:
                flash("Rôle invalide. Les rôles autorisés sont : administrateur, secrétaire, discipline, professeur.", 'danger')
                return redirect(url_for('admin.register_user_redirect'))
            school_id = current_user.school_id
        else:
            flash('Accès refusé.', 'danger')
            return redirect(url_for('auth.redirect_by_role'))

        if User.query.filter_by(username=username).first():
            flash("Le nom d'utilisateur existe déjà.", 'warning')
        else:
            user = User(
                school_id=school_id,
                username=username,
                full_name=full_name,
                role=role,
                email=email
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Utilisateur créé avec succès.', 'success')
            return redirect(url_for('admin.users'))

    schools = []
    if current_user.is_super_admin():
        schools = School.query.order_by(School.name).all()

    return render_template('admin/register_user.html', schools=schools)
