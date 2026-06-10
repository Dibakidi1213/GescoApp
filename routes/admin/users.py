from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import School, User, db
from routes.admin.helpers import get_school_id_for_admin_context
from routes.admin import admin_bp


@admin_bp.route('/users')
@login_required
def users(school_slug=None):
    target_school_id = get_school_id_for_admin_context()

    if current_user.is_super_admin() and not target_school_id:
        users_list = User.query.filter(User.role.in_(['school_admin', 'super_admin'])).order_by(User.full_name).all()
        schools = School.query.order_by(School.name).all()
    else:
        if not target_school_id:
            flash('Veuillez sélectionner une école pour gérer les utilisateurs.', 'info')
            return redirect(url_for('admin.dashboard', school_slug=school_slug))
        users_list = User.query.filter_by(school_id=target_school_id).order_by(User.full_name).all()
        schools = []

    return render_template('admin/users.html', users=users_list, schools=schools)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id, school_slug=None):
    user = User.query.get_or_404(user_id)
    if not current_user.is_super_admin() and user.school_id != current_user.school_id:
        flash('Accès non autorisé à ce profil.', 'danger')
        return redirect(url_for('admin.users', school_slug=school_slug))

    schools = School.query.order_by(School.name).all() if current_user.is_super_admin() else []

    if request.method == 'POST':
        user.full_name = request.form.get('full_name') or user.full_name
        user.email = request.form.get('email')
        user.username = request.form.get('username') or user.username
        if current_user.is_school_admin():
            role = request.form.get('role') or user.role
            allowed_roles = {'school_admin', 'secretary', 'professor', 'discipline'}
            if role not in allowed_roles:
                flash("Rôle invalide. Les rôles autorisés sont : administrateur d'école, secrétaire, discipline, professeur.", 'danger')
                return redirect(url_for('admin.edit_user', user_id=user.id, school_slug=school_slug))
            user.role = role
        if current_user.is_super_admin():
            school_id = request.form.get('school_id')
            user.school_id = int(school_id) if school_id else user.school_id

        password = request.form.get('password')
        if password:
            user.set_password(password)

        db.session.commit()
        flash('Modifications enregistrées avec succès.', 'success')
        return redirect(url_for('admin.users', school_slug=school_slug))

    return render_template('admin/edit_user.html', user=user, schools=schools)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id, school_slug=None):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'warning')
        return redirect(url_for('admin.users', school_slug=school_slug))
    if not current_user.is_super_admin() and user.school_id != current_user.school_id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('admin.users', school_slug=school_slug))
    if user.is_super_admin() and not current_user.is_super_admin():
        flash('Vous ne pouvez pas supprimer un super administrateur.', 'danger')
        return redirect(url_for('admin.users', school_slug=school_slug))

    db.session.delete(user)
    db.session.commit()
    flash('Utilisateur supprimé.', 'success')
    return redirect(url_for('admin.users', school_slug=school_slug))


@admin_bp.route('/register-user')
@login_required
def register_user_redirect(school_slug=None):
    return redirect(url_for('auth.register', school_slug=school_slug))
