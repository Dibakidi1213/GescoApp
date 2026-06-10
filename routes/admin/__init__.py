from flask import Blueprint, redirect, url_for, flash, g
from flask_login import current_user

admin_bp = Blueprint('admin', __name__)


@admin_bp.before_request
def restrict_admin():
    """Restreint l'accès au blueprint admin aux rôles autorisés."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    allowed_roles = {'super_admin', 'school_admin', 'secretary'}
    if current_user.role not in allowed_roles:
        flash('Accès refusé : permissions insuffisantes.', 'danger')
        return redirect(url_for('auth.redirect_by_role'))

    if getattr(g, 'school_slug', None) and not current_user.is_super_admin():
        if not current_user.school or current_user.school.slug != g.school_slug:
            return redirect(url_for('auth.redirect_by_role'))


from routes.admin import (  # noqa: E402,F401
    academic,
    bulletins,
    courses,
    dashboard,
    grades,
    misc,
    schools,
    students,
    subscriptions,
    users,
    deliberation,
)
