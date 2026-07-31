from collections import defaultdict

from flask import Blueprint, g, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, logout_user

from models import AttendanceRecord, ConductGrade, Section, db
from routes.attendance_utils import (
    ATTENDANCE_STATUS_LABELS,
    ATTENDANCE_STATUSES,
    CONDUCT_PERIODS,
    CONDUCT_VALUE_OPTIONS,
    CONDUCT_VALUES,
    class_label,
    get_attendance_course_for_section,
    holiday_map,
    month_bounds,
    month_key_for_day,
    parse_iso_date,
    parse_month,
    students_for_section_year,
    validate_attendance_scope,
    working_days_for_month,
)


discipline_bp = Blueprint('discipline', __name__, template_folder='../templates')


@discipline_bp.before_request
def restrict_discipline():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if current_user.school and not current_user.school.is_active:
        logout_user()
        return redirect(url_for('auth.login'))

    if not current_user.is_discipline():
        if '/api/' in request.path:
            return jsonify({'error': 'Acces refuse.'}), 403
        return redirect(url_for('auth.redirect_by_role'))

    if getattr(g, 'school_slug', None) and current_user.school:
        if current_user.school.slug != g.school_slug:
            return redirect(url_for('auth.redirect_by_role'))


def _serialize_section(section):
    return {
        'id': section.id,
        'name': section.name,
        'level': section.level,
        'class_name': section.class_name,
        'label': class_label(section),
    }


def _get_section_or_404(section_id):
    section = db.session.get(Section, section_id)
    if not section or section.school_id != current_user.school_id:
        return None
    return section


@discipline_bp.route('/')
@login_required
def dashboard(school_slug=None):
    school_id = current_user.school_id
    sections = Section.query.filter_by(school_id=school_id).order_by(
        Section.name,
        Section.level,
        Section.class_name,
    ).all()
    sections_catalog = [_serialize_section(section) for section in sections]

    return render_template(
        'discipline/dashboard.html',
        sections_catalog=sections_catalog,
        today_iso=parse_iso_date(request.args.get('date')).isoformat() if parse_iso_date(request.args.get('date')) else None,
        conduct_periods=CONDUCT_PERIODS,
        conduct_values=CONDUCT_VALUE_OPTIONS,
    )


@discipline_bp.route('/api/attendance/<int:section_id>', methods=['GET'])
@login_required
def get_attendance(section_id, school_slug=None):
    school_id = current_user.school_id
    section = _get_section_or_404(section_id)
    if not section:
        return jsonify({'error': 'Classe introuvable.'}), 404

    attendance_day = parse_iso_date(request.args.get('date'))
    month_value = request.args.get('month') or (month_key_for_day(attendance_day) if attendance_day else '')
    month_key, error = validate_attendance_scope(attendance_day, month_value, school_id)
    if error:
        return jsonify({
            'error': error,
            'closed': True,
            'students': [],
            'section': _serialize_section(section),
        }), 400

    academic_year = session.get('academic_year', '2025 - 2026')
    students = students_for_section_year(school_id, section.id, academic_year)
    course = get_attendance_course_for_section(section, school_id, month_key, create=False)

    records = []
    if course and students:
        records = AttendanceRecord.query.filter(
            AttendanceRecord.school_id == school_id,
            AttendanceRecord.course_id == course.id,
            AttendanceRecord.attendance_date == attendance_day,
            AttendanceRecord.academic_year == academic_year,
            AttendanceRecord.student_id.in_([student.id for student in students]),
        ).order_by(AttendanceRecord.period.desc(), AttendanceRecord.id.desc()).all()

    record_by_student = {}
    for record in records:
        if record.student_id not in record_by_student or record.period == month_key:
            record_by_student[record.student_id] = record
    payload_students = []
    for student in students:
        record = record_by_student.get(student.id)
        status = record.status if record and record.status in ATTENDANCE_STATUSES else 'present'
        payload_students.append({
            'student_id': student.id,
            'full_name': student.full_name(),
            'gender': student.gender,
            'status': status,
            'status_label': ATTENDANCE_STATUS_LABELS.get(status, 'Present'),
        })

    month_start = parse_month(month_key)
    start_day, end_day = month_bounds(month_start)
    holidays = holiday_map(school_id, start_day, end_day)

    return jsonify({
        'section': _serialize_section(section),
        'attendance_date': attendance_day.isoformat(),
        'month': month_key,
        'academic_year': academic_year,
        'class_label': class_label(section),
        'working_days': [day.isoformat() for day in working_days_for_month(school_id, month_key)],
        'holidays': [
            {'date': day.isoformat(), 'label': holiday.label}
            for day, holiday in sorted(holidays.items())
        ],
        'students': payload_students,
    })


@discipline_bp.route('/api/attendance/<int:section_id>/save', methods=['POST'])
@login_required
def save_attendance(section_id, school_slug=None):
    school_id = current_user.school_id
    section = _get_section_or_404(section_id)
    if not section:
        return jsonify({'error': 'Classe introuvable.'}), 404

    data = request.get_json() or {}
    attendance_day = parse_iso_date(data.get('attendance_date'))
    month_key, error = validate_attendance_scope(attendance_day, data.get('month'), school_id)
    if error:
        return jsonify({'error': error}), 400

    entries = data.get('entries') or []
    if not isinstance(entries, list):
        return jsonify({'error': 'Format de presence invalide.'}), 400

    academic_year = session.get('academic_year', '2025 - 2026')
    students = students_for_section_year(school_id, section.id, academic_year)
    valid_student_ids = {student.id for student in students}
    if not valid_student_ids:
        return jsonify({'error': 'Aucun eleve trouve pour cette classe.'}), 404

    course = get_attendance_course_for_section(
        section,
        school_id,
        month_key,
        professor_id=current_user.id,
        create=True,
    )

    existing_records = AttendanceRecord.query.filter(
        AttendanceRecord.school_id == school_id,
        AttendanceRecord.course_id == course.id,
        AttendanceRecord.attendance_date == attendance_day,
        AttendanceRecord.academic_year == academic_year,
        AttendanceRecord.student_id.in_(valid_student_ids),
    ).order_by(AttendanceRecord.period.desc(), AttendanceRecord.id.desc()).all()
    existing_by_student = {}
    for record in existing_records:
        if record.student_id not in existing_by_student or record.period == month_key:
            existing_by_student[record.student_id] = record

    created = 0
    updated = 0
    skipped = 0
    invalid = []

    for item in entries:
        if not isinstance(item, dict):
            skipped += 1
            continue
        try:
            student_id = int(item.get('student_id'))
        except (TypeError, ValueError):
            skipped += 1
            continue
        if student_id not in valid_student_ids:
            skipped += 1
            continue

        status = str(item.get('status') or '').strip().lower()
        if status not in ATTENDANCE_STATUSES:
            invalid.append(student_id)
            continue

        record = existing_by_student.get(student_id)
        if record:
            record.status = status
            record.section_id = section.id
            record.period = month_key
            record.professor_id = current_user.id
            updated += 1
        else:
            db.session.add(AttendanceRecord(
                school_id=school_id,
                section_id=section.id,
                course_id=course.id,
                student_id=student_id,
                professor_id=current_user.id,
                attendance_date=attendance_day,
                period=month_key,
                status=status,
                academic_year=academic_year,
            ))
            created += 1

    if invalid:
        db.session.rollback()
        return jsonify({'error': 'Statut de presence invalide.'}), 400

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Presence journaliere enregistree.',
        'attendance_date': attendance_day.isoformat(),
        'month': month_key,
        'class_label': class_label(section),
        'created': created,
        'updated': updated,
        'skipped': skipped,
    })


@discipline_bp.route('/api/conduct/<int:section_id>', methods=['GET'])
@login_required
def get_conduct(section_id, school_slug=None):
    school_id = current_user.school_id
    section = _get_section_or_404(section_id)
    if not section:
        return jsonify({'error': 'Classe introuvable.'}), 404

    academic_year = session.get('academic_year', '2025 - 2026')
    students = students_for_section_year(school_id, section.id, academic_year)
    student_ids = [student.id for student in students]
    conduct_grades = []
    if student_ids:
        conduct_grades = ConductGrade.query.filter(
            ConductGrade.school_id == school_id,
            ConductGrade.student_id.in_(student_ids),
            ConductGrade.academic_year == academic_year,
        ).all()

    conduct_map = defaultdict(dict)
    for conduct in conduct_grades:
        conduct_map[conduct.student_id][conduct.period] = conduct.value

    return jsonify({
        'section': _serialize_section(section),
        'periods': CONDUCT_PERIODS,
        'values': CONDUCT_VALUE_OPTIONS,
        'students': [{
            'student_id': student.id,
            'full_name': student.full_name(),
            'conducts': {
                period: conduct_map[student.id].get(period, '')
                for period in CONDUCT_PERIODS
            },
        } for student in students],
    })


@discipline_bp.route('/api/conduct/<int:section_id>/save', methods=['POST'])
@login_required
def save_conduct(section_id, school_slug=None):
    school_id = current_user.school_id
    section = _get_section_or_404(section_id)
    if not section:
        return jsonify({'error': 'Classe introuvable.'}), 404

    data = request.get_json() or {}
    entries = data.get('grades') or []
    if not isinstance(entries, list):
        return jsonify({'error': 'Format de conduite invalide.'}), 400

    academic_year = session.get('academic_year', '2025 - 2026')
    students = students_for_section_year(school_id, section.id, academic_year)
    valid_student_ids = {student.id for student in students}

    cleaned_entries = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        try:
            student_id = int(item.get('student_id'))
        except (TypeError, ValueError):
            continue
        period = str(item.get('period') or '').strip()
        value = str(item.get('value') or '').strip().upper()
        if student_id not in valid_student_ids:
            continue
        if period not in CONDUCT_PERIODS:
            return jsonify({'error': 'Periode de conduite invalide.'}), 400
        if value and value not in CONDUCT_VALUES:
            return jsonify({'error': 'Valeur de conduite invalide. Utilisez E, TB, B, AB, MA ou ME.'}), 400
        cleaned_entries.append((student_id, period, value))

    student_ids = {student_id for student_id, _period, _value in cleaned_entries}
    existing = []
    if student_ids:
        existing = ConductGrade.query.filter(
            ConductGrade.school_id == school_id,
            ConductGrade.student_id.in_(student_ids),
            ConductGrade.academic_year == academic_year,
        ).all()

    existing_map = defaultdict(dict)
    for conduct in existing:
        existing_map[conduct.student_id][conduct.period] = conduct

    changed = 0
    for student_id, period, value in cleaned_entries:
        conduct = existing_map[student_id].get(period)
        if conduct:
            if value:
                conduct.value = value
                changed += 1
            else:
                db.session.delete(conduct)
                changed += 1
        elif value:
            db.session.add(ConductGrade(
                school_id=school_id,
                student_id=student_id,
                academic_year=academic_year,
                period=period,
                value=value,
            ))
            changed += 1

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Conduites enregistrees.',
        'changed': changed,
    })
