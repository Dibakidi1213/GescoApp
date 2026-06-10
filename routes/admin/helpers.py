import os
import re
import uuid
from datetime import date, datetime
from functools import wraps
from pathlib import Path

from flask import flash, g, redirect, url_for, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from models import (
    ActivityLog,
    Grade,
    Payment,
    RemoteSupportTicket,
    School,
    SchoolSubscription,
    User,
    get_active_school_subscription,
    get_latest_school_subscription,
)

PERIODS = ['1èP', '2èP', 'EXA1', '3èP', '4èP', 'EXA2', 'REPECHAGE']

PERIOD_OPTIONS = [
    ('1èP', '1ère Période (1èP)'),
    ('2èP', '2ème Période (2èP)'),
    ('EXA1', 'Examen 1 (EXA1)'),
    ('3èP', '3ème Période (3èP)'),
    ('4èP', '4ème Période (4èP)'),
    ('EXA2', 'Examen 2 (EXA2)'),
    ('REPECHAGE', 'Examen de Repêchage'),
]

SCOPE_OPTIONS = PERIOD_OPTIONS + [
    ('semester1', 'Total 1er Semestre'),
    ('semester2', 'Total 2ème Semestre'),
    ('annual', 'Total Annuel'),
]

ALLOWED_LOGO_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}


def normalize_text(value):
    return re.sub(r'\s+', ' ', str(value or '').strip()).lower()


def get_school_id_for_admin_context():
    """Détermine l'ID de l'école à utiliser pour le contexte admin."""
    if current_user.is_super_admin():
        if getattr(g, 'school_slug', None) and getattr(g, 'school', None):
            return g.school.id
        return None
    return current_user.school_id


def require_super_admin(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_super_admin():
            flash('Accès refusé : réservé au super administrateur.', 'danger')
            return redirect(url_for('admin.dashboard', school_slug=kwargs.get('school_slug')))
        return view_func(*args, **kwargs)
    return wrapper


def save_uploaded_logo(file_storage, school=None):
    """Sauvegarde un logo uploadé dans static/uploads/schools."""
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_LOGO_EXTENSIONS:
        raise ValueError('Format de logo non supporté. Utilisez PNG, JPG ou WEBP.')

    upload_dir = Path(current_app.root_path) / 'static' / 'uploads' / 'schools'
    upload_dir.mkdir(parents=True, exist_ok=True)

    prefix = f"school_{school.id}_" if school and school.id else 'school_'
    stored_name = f"{prefix}{uuid.uuid4().hex}{extension}"
    destination = upload_dir / stored_name
    file_storage.save(destination)
    return f"/static/uploads/schools/{stored_name}"


def build_subscription_snapshots(schools):
    snapshots = {}
    for school in schools:
        active = get_active_school_subscription(school.id)
        latest = get_latest_school_subscription(school.id)
        snapshots[school.id] = {
            'active': active,
            'latest': latest,
        }
    return snapshots


def get_subscription_stats():
    today = date.today()
    active_count = SchoolSubscription.query.filter(
        SchoolSubscription.status == 'active',
        SchoolSubscription.start_date <= today,
        SchoolSubscription.end_date >= today,
    ).count()
    pending_count = SchoolSubscription.query.filter_by(status='pending_payment').count()
    open_support_count = RemoteSupportTicket.query.filter(
        RemoteSupportTicket.status.in_(['open', 'in_progress'])
    ).count()
    return {
        'active_subscription_count': active_count,
        'pending_subscription_count': pending_count,
        'open_support_count': open_support_count,
    }


def get_recent_activity_for_school(school_id, limit=8):
    return (
        ActivityLog.query.join(User, ActivityLog.user_id == User.id)
        .filter(User.school_id == school_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )


def get_payment_total_for_school(school_id, year=None):
    query = Payment.query.filter(Payment.school_id == school_id)
    if year:
        query = query.filter(
            Payment.payment_date >= date(int(str(year).split('-')[0].strip()), 1, 1),
            Payment.payment_date <= date(int(str(year).split('-')[-1].strip()), 12, 31),
        )
    return query.with_entities(Payment.amount).all()


def sum_payments_for_school(school_id, year=None):
    from models import db
    query = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).filter(
        Payment.school_id == school_id
    )
    if year:
        try:
            start_year = int(str(year).split('-')[0].strip())
            end_year = int(str(year).split('-')[-1].strip())
            query = query.filter(
                Payment.payment_date >= date(start_year, 1, 1),
                Payment.payment_date <= date(end_year, 12, 31),
            )
        except (TypeError, ValueError):
            pass
    return float(query.scalar() or 0)


def secretary_grades_url_for_user():
    if current_user.is_authenticated and current_user.school and current_user.school.slug:
        return url_for('admin.grades_management', school_slug=current_user.school.slug) + '#deverrouillage-cours'
    return url_for('admin.grades_management') + '#deverrouillage-cours'


class SectionGroup:
    """Regroupe les enregistrements Section par nom pour l'affichage admin."""

    def __init__(self, name, sections, school=None):
        self.name = name
        self.id = sections[0].id if sections else None
        self.school = school or (sections[0].school if sections else None)
        self._sections = sections
        levels = set()
        classes = set()
        pairs = []
        for section in sections:
            if section.level:
                levels.add(section.level)
            if section.class_name:
                classes.add(section.class_name)
            if section.level and section.class_name:
                pairs.append({'level': section.level, 'class': section.class_name})
        self.all_levels = sorted(levels, key=lambda x: (len(x), x))
        self.all_classes = sorted(classes)
        self.level_class_pairs = pairs


def group_sections_for_display(sections):
    grouped = {}
    for section in sections:
        grouped.setdefault(section.name, []).append(section)
    result = []
    for name, items in sorted(grouped.items(), key=lambda item: item[0].lower()):
        school = items[0].school if items else None
        result.append(SectionGroup(name, items, school=school))
    return result
