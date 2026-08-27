from collections import defaultdict
import re
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, g, session
from flask_login import login_required, current_user, logout_user

from models import db, Course, Student, Grade, Section, BulletinConfig, BulletinBranch, Notification, ConductGrade
from routes.attendance_utils import class_denomination
from url_utils import encode_id, decode_id_or_int

secretary_bp = Blueprint('secretary', __name__, template_folder='../templates')

SECRETARY_PERIOD_FIELD_MAP = {
    '1èP': 'max_period_1',
    '2èP': 'max_period_2',
    'EXA1': 'max_exam_1',
    '3èP': 'max_period_3',
    '4èP': 'max_period_4',
    'EXA2': 'max_exam_2',
}
PERIODS = ['1èP', '2èP', 'EXA1', '3èP', '4èP', 'EXA2']


def _normalize_text(value):
    return re.sub(r'\s+', ' ', str(value or '').strip()).lower()


def _format_class_label(section):
    if not section:
        return 'Classe inconnue'
    return class_denomination(section)


def _section_matches(section, section_name=None, level=None, class_name=None):
    if section_name and _normalize_text(section.name) != _normalize_text(section_name):
        return False
    if level and _normalize_text(section.level) != _normalize_text(level):
        return False
    if class_name and _normalize_text(section.class_name) != _normalize_text(class_name):
        return False
    return True


def _get_section_by_hierarchy(school_id, section_name=None, level=None, class_name=None):
    if not section_name or not level or not class_name:
        return None

    sections = Section.query.filter_by(school_id=school_id).all()
    for section in sections:
        if _section_matches(section, section_name=section_name, level=level, class_name=class_name):
            return section
    return None


def _get_course_branch(course):
    if not course:
        return None

    section = getattr(course, 'section', None)
    if not section:
        return getattr(course, 'branch', None)

    config = BulletinConfig.query.filter_by(
        school_id=course.school_id,
        section_id=section.id,
        level=section.level
    ).order_by(BulletinConfig.updated_at.desc(), BulletinConfig.id.desc()).first()
    if not config:
        config = BulletinConfig.query.filter_by(
            school_id=course.school_id,
            section_id=section.id,
            level=section.level
        ).order_by(BulletinConfig.updated_at.desc(), BulletinConfig.id.desc()).first()
    if not config:
        return getattr(course, 'branch', None)

    branches = config.branches.order_by(BulletinBranch.order, BulletinBranch.id).all()
    if not branches:
        return getattr(course, 'branch', None)

    course_branch_id = getattr(course, 'branch_id', None)
    if course_branch_id is not None:
        matched_branch = next((branch for branch in branches if branch.id == course_branch_id), None)
        if matched_branch:
            return matched_branch

    normalized_title = _normalize_text(course.title)
    for branch in branches:
        if _normalize_text(branch.name) == normalized_title:
            return branch

    if len(branches) == 1:
        return branches[0]

    fallback_branch = getattr(course, 'branch', None)
    if fallback_branch and getattr(fallback_branch, 'config_id', None) == getattr(config, 'id', None):
        return fallback_branch

    return None


def _coerce_branch_value(branch, field_name, fallback_field=None, default_value=0):
    value = getattr(branch, field_name, None)
    if value is None or (isinstance(value, str) and str(value).strip() == ''):
        if fallback_field:
            value = getattr(branch, fallback_field, None)
    if value is None or (isinstance(value, str) and str(value).strip() == ''):
        value = default_value
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default_value)


def _branch_period_limits(branch):
    return {
        '1èP': _coerce_branch_value(branch, 'max_period_1', default_value=10),
        '2èP': _coerce_branch_value(branch, 'max_period_2', default_value=10),
        'EXA1': _coerce_branch_value(branch, 'max_exam_1', default_value=20),
        '3èP': _coerce_branch_value(branch, 'max_period_3', default_value=10),
        '4èP': _coerce_branch_value(branch, 'max_period_4', default_value=10),
        'EXA2': _coerce_branch_value(branch, 'max_exam_2', default_value=20),
    }


def _get_period_field_name(period):
    field_names = (
        'max_period_1',
        'max_period_2',
        'max_exam_1',
        'max_period_3',
        'max_period_4',
        'max_exam_2',
    )

    try:
        index = PERIODS.index(period)
    except ValueError:
        return None

    if index < 0 or index >= len(field_names):
        return None

    return field_names[index]


def _serialize_section(section):
    from url_utils import encode_id
    return {
        'id': section.id,
        'token': encode_id(section.id),
        'name': section.name,
        'level': section.level,
        'class_name': section.class_name,
        'label': _format_class_label(section),
    }


def _build_class_period_stats(school_id, section, academic_year):
    courses = Course.query.filter_by(school_id=school_id, section_id=section.id).order_by(Course.title).all()
    course_ids = [course.id for course in courses]
    course_titles = {course.id: course.title for course in courses}
    stats = {}

    for period in PERIODS:
        stats[period] = {
            'period': period,
            'state': 'open',
            'submitted_count': 0,
            'total_count': 0,
            'courses_count': len(courses),
            'courses': {},
        }

    if not course_ids:
        return stats, courses

    grades = Grade.query.filter(
        Grade.school_id == school_id,
        Grade.course_id.in_(course_ids),
        Grade.academic_year == academic_year
    ).all()

    for grade in grades:
        period_stats = stats.get(grade.period)
        if not period_stats:
            continue
        period_stats['total_count'] += 1
        title = course_titles.get(grade.course_id, f'Cours #{grade.course_id}')
        course_stats = period_stats['courses'].setdefault(
            title, {'submitted_count': 0, 'total_count': 0}
        )
        course_stats['total_count'] += 1
        if grade.submitted:
            period_stats['submitted_count'] += 1
            course_stats['submitted_count'] += 1

    for period_stats in stats.values():
        total_count = period_stats['total_count']
        submitted_count = period_stats['submitted_count']
        if total_count > 0 and submitted_count == total_count:
            period_stats['state'] = 'locked'
        elif submitted_count > 0:
            period_stats['state'] = 'partial'
        else:
            period_stats['state'] = 'open'

    return stats, courses


def _create_notification(*, school_id, recipient_id, title, message, notification_type, actor_id=None, url=None):
    notification = Notification(
        school_id=school_id,
        recipient_id=recipient_id,
        actor_id=actor_id,
        notification_type=notification_type,
        title=title,
        message=message,
        url=url,
    )
    db.session.add(notification)
    return notification


def _serialize_notification(notification):
    from url_utils import encode_id
    return {
        'id': notification.id,
        'token': encode_id(notification.id),
        'title': notification.title,
        'message': notification.message,
        'type': notification.notification_type,
        'is_read': bool(notification.is_read),
        'created_at': notification.created_at.isoformat() if notification.created_at else None,
        'read_at': notification.read_at.isoformat() if notification.read_at else None,
        'url': notification.url
    }


@secretary_bp.before_request
def restrict_secretary():
    """Check secretary role - redirect for pages, return JSON for API calls."""
    is_secretary_role = current_user.is_authenticated and current_user.is_secretary()
    is_discipline_role = current_user.is_authenticated and hasattr(current_user, 'is_discipline') and current_user.is_discipline()

    if not current_user.is_authenticated or not (is_secretary_role or is_discipline_role):
        if '/secretary/api/' in request.path:
            return jsonify({'error': 'Unauthorized'}), 401
        return redirect(url_for('auth.login'))

    if current_user.school and not current_user.school.is_active:
        logout_user()
        return redirect(url_for('auth.login'))

    if getattr(g, 'school_slug', None) and not current_user.is_super_admin():
        if not current_user.school or current_user.school.slug != g.school_slug:
            return redirect(url_for('auth.redirect_by_role'))

    if is_discipline_role:
        allowed_endpoints = {
            'secretary.conduite',
            'secretary.get_conduite',
            'secretary.save_conduite',
        }
        if request.endpoint not in allowed_endpoints:
            if '/secretary/api/' in request.path:
                return jsonify({'error': 'Unauthorized'}), 403
            return redirect(url_for('auth.redirect_by_role'))


@secretary_bp.route('/')
def dashboard(school_slug=None):
    """Secretary dashboard showing submitted grades."""
    school_id = current_user.school_id
    year = session.get('academic_year', '2025 - 2026')

    courses = Course.query.filter_by(school_id=school_id).order_by(Course.title).all()
    sections = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level, Section.class_name).all()
    notifications = Notification.query.filter_by(
        school_id=school_id,
        recipient_id=current_user.id
    ).order_by(Notification.is_read.asc(), Notification.created_at.desc(), Notification.id.desc()).limit(5).all()
    unread_notifications_count = Notification.query.filter_by(
        school_id=school_id,
        recipient_id=current_user.id,
        is_read=False
    ).count()

    submitted_grades_count = db.session.query(Grade).filter(
        Grade.school_id == school_id,
        Grade.submitted == True,
        Grade.academic_year == year
    ).count()

    return render_template(
        'secretary/dashboard.html',
        courses=courses,
        sections=sections,
        submitted_grades_count=submitted_grades_count,
        periods=PERIODS,
        notifications=notifications,
        unread_notifications_count=unread_notifications_count,
    )


@secretary_bp.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications(school_slug=None):
    school_id = current_user.school_id
    limit = request.args.get('limit', default=5, type=int) or 5

    notifications = Notification.query.filter_by(
        school_id=school_id,
        recipient_id=current_user.id
    ).order_by(Notification.is_read.asc(), Notification.created_at.desc(), Notification.id.desc()).limit(limit).all()

    unread_count = Notification.query.filter_by(
        school_id=school_id,
        recipient_id=current_user.id,
        is_read=False
    ).count()

    return jsonify({
        'notifications': [_serialize_notification(notification) for notification in notifications],
        'unread_count': unread_count
    })


@secretary_bp.route('/api/notifications/<oid:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id, school_slug=None):
    school_id = current_user.school_id
    notification = Notification.query.filter_by(
        id=notification_id,
        school_id=school_id,
        recipient_id=current_user.id
    ).first()

    if not notification:
        return jsonify({'error': 'Notification introuvable.'}), 404

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now()
        db.session.commit()

    return jsonify({
        'success': True,
        'notification': _serialize_notification(notification)
    })


@secretary_bp.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read(school_slug=None):
    school_id = current_user.school_id
    notifications = Notification.query.filter_by(
        school_id=school_id,
        recipient_id=current_user.id,
        is_read=False
    ).all()

    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.now()

    db.session.commit()

    return jsonify({
        'success': True,
        'count': len(notifications)
    })


@secretary_bp.route('/api/sections', methods=['GET'])
@login_required
def get_sections(school_slug=None):
    """Return distinct section names for the secretary's school."""
    school_id = current_user.school_id
    sections = Section.query.filter_by(school_id=school_id).order_by(Section.name).all()

    section_names = []
    seen = set()
    for section in sections:
        normalized = _normalize_text(section.name)
        if normalized in seen:
            continue
        seen.add(normalized)
        section_names.append(section.name)

    return jsonify(section_names)


@secretary_bp.route('/api/levels/<section_name>', methods=['GET'])
@login_required
def get_levels(section_name, school_slug=None):
    """Return distinct levels available for a section name."""
    school_id = current_user.school_id
    sections = Section.query.filter_by(school_id=school_id).order_by(Section.level).all()

    levels = []
    seen = set()
    for section in sections:
        if _normalize_text(section.name) != _normalize_text(section_name):
            continue
        normalized = _normalize_text(section.level)
        if normalized in seen:
            continue
        seen.add(normalized)
        levels.append(section.level)

    return jsonify(levels)


@secretary_bp.route('/api/classes/<section_name>/<level>', methods=['GET'])
@login_required
def get_classes(section_name, level, school_slug=None):
    """Return classes for a section name and level."""
    school_id = current_user.school_id
    sections = Section.query.filter_by(school_id=school_id).order_by(Section.class_name).all()

    classes = []
    seen_ids = set()
    for section in sections:
        if _normalize_text(section.name) != _normalize_text(section_name):
            continue
        if _normalize_text(section.level) != _normalize_text(level):
            continue
        if section.id in seen_ids:
            continue
        seen_ids.add(section.id)
        classes.append(_serialize_section(section))

    return jsonify(classes)


@secretary_bp.route('/api/courses', methods=['GET'])
@login_required
def get_courses(school_slug=None):
    """Get all courses for the secretary's school."""
    school_id = current_user.school_id

    section_id = decode_id_or_int(request.args.get('section_id'))
    section_name = request.args.get('section_name', type=str)
    level = request.args.get('level', type=str)
    class_name = request.args.get('class_name', type=str)

    query = Course.query.filter_by(school_id=school_id)
    if section_id:
        query = query.filter_by(section_id=section_id)
    elif section_name and level and class_name:
        section = _get_section_by_hierarchy(school_id, section_name, level, class_name)
        if not section:
            return jsonify([])
        query = query.filter_by(section_id=section.id)

    courses = query.order_by(Course.title).all()
    return jsonify([
        {
            'id': course.id,
            'token': encode_id(course.id),
            'title': course.title,
            'section_id': course.section_id,
            'professor_id': course.professor_id,
            'professor_name': course.professor.full_name if course.professor else 'Unknown',
            'section_name': course.section.name if course.section else 'Unknown',
            'level': course.section.level if course.section else None,
            'class_name': course.section.class_name if course.section else None,
        }
        for course in courses
    ])


@secretary_bp.route('/api/class-period-status/<oid:section_id>', methods=['GET'])
@login_required
def get_class_period_status(section_id, school_slug=None):
    """Return period status aggregated for a whole class."""
    school_id = current_user.school_id
    academic_year = session.get('academic_year', '2025 - 2026')

    section = db.session.get(Section, section_id)
    if not section or section.school_id != school_id:
        return jsonify({'error': 'Classe non trouvée.'}), 403

    periods, courses = _build_class_period_stats(school_id, section, academic_year)
    return jsonify({
        'section': _serialize_section(section),
        'courses_count': len(courses),
        'periods': periods,
    })


@secretary_bp.route('/api/locked-grades/<oid:course_id>', methods=['GET'])
@login_required
def get_locked_grades(course_id, school_slug=None):
    """Get all grades for a course, with their submission state."""
    school_id = current_user.school_id

    course = Course.query.filter_by(id=course_id, school_id=school_id).first()
    if not course:
        return jsonify({'error': 'Cours non trouvé.'}), 403

    period = request.args.get('period', type=str)
    year = session.get('academic_year', '2025 - 2026')

    query = Grade.query.filter_by(
        school_id=school_id,
        course_id=course_id,
        academic_year=year
    )
    if period:
        query = query.filter_by(period=period)

    grades = query.all()

    grades_by_period = {}
    branch = _get_course_branch(course)
    period_limits = _branch_period_limits(branch) if branch else {}

    for grade in grades:
        if grade.period not in grades_by_period:
            grades_by_period[grade.period] = []

        student = db.session.get(Student, grade.student_id)
        max_allowed = period_limits.get(grade.period, 20)

        grades_by_period[grade.period].append({
            'grade_id': grade.id,
            'grade_token': encode_id(grade.id),
            'student_id': grade.student_id,
            'student_name': student.full_name() if student else 'Unknown',
            'period': grade.period,
            'value': float(grade.value) if grade.value is not None else None,
            'max_allowed': max_allowed,
            'submitted': bool(grade.submitted),
            'submitted_by': grade.submitted_by,
            'submitted_by_name': grade.submitted_by_user.full_name if grade.submitted_by_user else 'Unknown',
            'submitted_at': grade.submitted_at.isoformat() if grade.submitted_at else None,
            'flagged': bool(grade.flagged),
        })

    return jsonify(grades_by_period)


@secretary_bp.route('/api/update-grade/<oid:grade_id>', methods=['POST'])
@login_required
def update_grade(grade_id, school_slug=None):
    """Update a locked grade as secretary."""
    school_id = current_user.school_id
    data = request.get_json() or {}

    grade = Grade.query.filter_by(id=grade_id, school_id=school_id).first()
    if not grade:
        return jsonify({'error': 'Note non trouvée.'}), 403

    if not grade.submitted:
        return jsonify({'error': "Cette note n'est pas verrouillée."}), 400

    old_value = float(grade.value) if grade.value is not None else None

    try:
        new_value = float(data.get('value', grade.value))
    except (TypeError, ValueError):
        return jsonify({'error': 'Valeur de note invalide.'}), 400

    if new_value < 0:
        return jsonify({'error': 'La note ne peut pas être inférieure à 0.'}), 400

    course = grade.course
    if course:
        branch = _get_course_branch(course)
        period = grade.period
        period_limits = _branch_period_limits(branch) if branch else {}

        max_allowed = period_limits.get(period, 20)
        if new_value > max_allowed:
            return jsonify({'error': f'La note maximale pour {period} est {max_allowed}.'}), 400

    grade.value = new_value
    grade.flagged = True
    professor = course.professor if course else None
    if professor and old_value is not None and float(old_value) != float(new_value):
        student_name = grade.student.display_name() if grade.student else "l'élève"
        _create_notification(
            school_id=school_id,
            recipient_id=professor.id,
            actor_id=current_user.id,
            notification_type='grade_updated_by_secretary',
            title='Cote modifiée par le secrétariat',
            message=(
                f'Le secrétariat a modifié la cote de {student_name} '
                f'pour {course.title} ({grade.period}) : {old_value:g} -> {new_value:g}.'
            ),
        )

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Note mise à jour',
        'grade_id': grade_id,
        'value': float(new_value),
    })


@secretary_bp.route('/api/unlock-period/<oid:course_id>', methods=['POST'])
@login_required
def unlock_period(course_id, school_slug=None):
    """Unlock all grades for a period (return to professor for editing)."""
    school_id = current_user.school_id
    data = request.get_json() or {}
    period = data.get('period')
    year = session.get('academic_year', '2025 - 2026')

    course = Course.query.filter_by(id=course_id, school_id=school_id).first()
    if not course:
        return jsonify({'error': 'Cours non trouvé.'}), 403

    if not period or period not in PERIODS:
        return jsonify({'error': 'Période invalide.'}), 400

    grades = Grade.query.filter_by(
        school_id=school_id,
        course_id=course_id,
        period=period,
        academic_year=year,
        submitted=True
    ).all()

    professor = course.professor if course else None

    for grade in grades:
        grade.submitted = False

    if professor and grades:
        # Link to the secretary dashboard with course and period pre-selected
        school_slug_param = school_slug or (current_user.school.slug if current_user.school else None)
        course_link = url_for('secretary.dashboard', school_slug=school_slug_param) + f"?course_id={course.id}&period={period}"
        student_names = ', '.join(sorted({g.student.full_name() for g in grades if g.student}))
        _create_notification(
            school_id=school_id,
            recipient_id=professor.id,
            actor_id=current_user.id,
            notification_type='period_unlocked_by_secretary',
            title='Période déverrouillée par le secrétariat',
            message=(
                f'Le secrétariat a déverrouillé {len(grades)} note(s) de la période {period} '
                f'pour le cours {course.title}. '
                f"Élèves affectés : {student_names}. Vous pouvez reprendre les modifications."
            ),
            url=course_link,
        )

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Toutes les notes de {period} ont été déverrouillées.',
        'count': len(grades),
    })


@secretary_bp.route('/api/unlock-class-period/<oid:section_id>', methods=['POST'])
@login_required
def unlock_class_period(section_id, school_slug=None):
    """Unlock all submitted grades for a given class and period."""
    school_id = current_user.school_id
    data = request.get_json() or {}
    period = data.get('period')
    year = session.get('academic_year', '2025 - 2026')

    section = db.session.get(Section, section_id)
    if not section or section.school_id != school_id:
        return jsonify({'error': 'Classe non trouvée.'}), 403

    if not period or period not in PERIODS:
        return jsonify({'error': 'Période invalide.'}), 400

    courses = Course.query.filter_by(school_id=school_id, section_id=section.id).order_by(Course.title).all()
    course_ids = [course.id for course in courses]
    if not course_ids:
        return jsonify({'error': 'Aucun cours trouvé pour cette classe.'}), 404

    grades = Grade.query.filter(
        Grade.school_id == school_id,
        Grade.course_id.in_(course_ids),
        Grade.period == period,
        Grade.academic_year == year,
        Grade.submitted == True
    ).all()

    if not grades:
        return jsonify({'error': 'Aucune note verrouillée trouvée pour cette période.'}), 404

    affected_professors = defaultdict(list)
    class_label = _format_class_label(section)

    # Map professor_id -> {'count': int, 'students': set(), 'courses': set(), 'course_ids': set()}
    affected_professors = defaultdict(lambda: {'count': 0, 'students': set(), 'courses': set(), 'course_ids': set()})

    for grade in grades:
        grade.submitted = False
        course = grade.course
        professor = course.professor if course else None
        student = grade.student
        if professor:
            ap = affected_professors[professor.id]
            ap['count'] += 1
            if student:
                ap['students'].add(student.full_name())
            if course:
                ap['courses'].add(course.title)
                ap['course_ids'].add(course.id)

    for professor_id, info in affected_professors.items():
        student_list = ', '.join(sorted(info['students'])) if info['students'] else 'N/A'
        courses_list = ', '.join(sorted(info['courses'])) if info['courses'] else 'N/A'
        # Limit student list display to avoid overly long notifications
        max_names = 12
        student_display = student_list
        if len(info['students']) > max_names:
            first_names = sorted(info['students'])[:max_names]
            student_display = f"{', '.join(first_names)} (+{len(info['students'])-max_names} autres)"

        # Build a link to the secretary dashboard pre-selecting a relevant course if available
        school_slug_param = school_slug or (current_user.school.slug if current_user.school else None)
        if info['course_ids']:
            first_course_id = next(iter(info['course_ids']))
            notif_url = url_for('secretary.dashboard', school_slug=school_slug_param) + f"?course_id={first_course_id}&period={period}"
        else:
            notif_url = url_for('secretary.dashboard', school_slug=school_slug_param) + f"?section_id={section.id}&period={period}"

        _create_notification(
            school_id=school_id,
            recipient_id=professor_id,
            actor_id=current_user.id,
            notification_type='period_unlocked_by_secretary',
            title='Période déverrouillée par le secrétariat',
            message=(
                f'Le secrétariat a déverrouillé {info["count"]} note(s) de la période {period} pour la classe {class_label}. '
                f'Cours concernés : {courses_list}. '
                f'Elèves affectés : {student_display}. Vous pouvez reprendre les modifications.'
            ),
            url=notif_url,
        )

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'{len(grades)} notes de {period} ont été déverrouillées pour la classe {class_label}.',
        'count': len(grades),
        'courses_count': len(courses),
    })


@secretary_bp.route('/conduite')
def conduite(school_slug=None):
    """Secretary interface to input Conduct grades."""
    target_slug = school_slug or (current_user.school.slug if current_user.school else None)
    if current_user.is_discipline():
        if target_slug:
            return redirect(url_for('discipline.dashboard', school_slug=target_slug) + '#conduite')
        return redirect(url_for('auth.redirect_by_role'))
    if target_slug:
        return redirect(url_for('admin.attendance_management', school_slug=target_slug))
    return redirect(url_for('auth.redirect_by_role'))


@secretary_bp.route('/api/conduite/<oid:section_id>', methods=['GET'])
@login_required
def get_conduite(section_id, school_slug=None):
    if not current_user.is_discipline():
        return jsonify({'error': 'Acces refuse.'}), 403

    school_id = current_user.school_id
    year = session.get('academic_year', '2025 - 2026')
    
    section = db.session.get(Section, section_id)
    if not section or section.school_id != school_id:
        return jsonify({'error': 'Classe non trouvée.'}), 403

    students = Student.query.filter_by(school_id=school_id, section_id=section_id).order_by(Student.last_name, Student.first_name).all()
    
    student_ids = [s.id for s in students]
    conduct_grades = ConductGrade.query.filter(
        ConductGrade.school_id == school_id,
        ConductGrade.student_id.in_(student_ids),
        ConductGrade.academic_year == year
    ).all()
    
    conduct_map = defaultdict(dict)
    for cg in conduct_grades:
        conduct_map[cg.student_id][cg.period] = cg.value

    result = []
    for student in students:
        result.append({
            'student_id': student.id,
            'full_name': student.full_name(),
            'conducts': {
                '1èP': conduct_map[student.id].get('1èP', ''),
                '2èP': conduct_map[student.id].get('2èP', ''),
                '3èP': conduct_map[student.id].get('3èP', ''),
                '4èP': conduct_map[student.id].get('4èP', '')
            }
        })
        
    return jsonify(result)


@secretary_bp.route('/api/conduite/<oid:section_id>', methods=['POST'])
@login_required
def save_conduite(section_id, school_slug=None):
    if not current_user.is_discipline():
        return jsonify({'error': 'Acces refuse.'}), 403

    school_id = current_user.school_id
    year = session.get('academic_year', '2025 - 2026')
    
    section = db.session.get(Section, section_id)
    if not section or section.school_id != school_id:
        return jsonify({'error': 'Classe non trouvée.'}), 403

    data = request.get_json() or {}
    grades_data = data.get('grades', [])
    
    if not isinstance(grades_data, list):
        return jsonify({'error': 'Format de données invalide.'}), 400

    student_ids = [item.get('student_id') for item in grades_data if item.get('student_id')]
    
    # Load existing
    existing = ConductGrade.query.filter(
        ConductGrade.school_id == school_id,
        ConductGrade.student_id.in_(student_ids),
        ConductGrade.academic_year == year
    ).all()
    
    existing_map = defaultdict(dict)
    for cg in existing:
        existing_map[cg.student_id][cg.period] = cg

    valid_periods = ['1èP', '2èP', '3èP', '4èP']
    
    for item in grades_data:
        student_id = item.get('student_id')
        if not student_id:
            continue
            
        period = item.get('period')
        if period not in valid_periods:
            continue
            
        value = str(item.get('value', '')).strip()
        
        cg = existing_map[student_id].get(period)
        if cg:
            if value:
                cg.value = value
            else:
                db.session.delete(cg)
        else:
            if value:
                new_cg = ConductGrade(
                    school_id=school_id,
                    student_id=student_id,
                    academic_year=year,
                    period=period,
                    value=value
                )
                db.session.add(new_cg)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Cotes de conduite enregistrées.'})
