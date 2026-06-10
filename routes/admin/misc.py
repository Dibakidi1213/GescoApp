from datetime import date, datetime

from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user

from models import AttendanceRecord, Course, Payment, Section, Student, User, db
from routes.admin.helpers import PERIOD_OPTIONS, get_school_id_for_admin_context, require_super_admin, sum_payments_for_school
from routes.admin import admin_bp

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


def _render_placeholder(title, message='Cette fonctionnalité sera disponible prochainement.'):
    return render_template('admin/placeholder.html', title=title, message=message)


ATTENDANCE_STATUS_OPTIONS = [
    ('present', 'Présent'),
    ('absent', 'Absent'),
    ('malade', 'Malade'),
]
ATTENDANCE_STATUS_MAP = dict(ATTENDANCE_STATUS_OPTIONS)
ATTENDANCE_PERIOD_VALUES = {value for value, _label in PERIOD_OPTIONS}
ATTENDANCE_PLACEHOLDER_PREFIX = 'Présence de classe'


def _attendance_class_label(section):
    if not section:
        return ''
    return ' / '.join(part for part in [section.name, section.level, section.class_name] if part)


def _attendance_course_title(period):
    return f'{ATTENDANCE_PLACEHOLDER_PREFIX} - {period}'


def _get_attendance_course_for_section(section, school_id, period, create=False):
    if not section:
        return None

    course = Course.query.filter_by(
        school_id=school_id,
        section_id=section.id,
        title=_attendance_course_title(period),
    ).first()
    if course or not create:
        return course

    course = Course(
        school_id=school_id,
        section_id=section.id,
        title=_attendance_course_title(period),
        professor_id=current_user.id,
    )
    db.session.add(course)
    db.session.flush()
    return course


def _parse_attendance_date(raw_value):
    raw = str(raw_value or '').strip()
    if not raw:
        return date.today()
    try:
        return datetime.strptime(raw, '%Y-%m-%d').date()
    except ValueError:
        return None


@admin_bp.route('/professors', methods=['GET', 'POST'])
@login_required
def professors(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    if not school_id:
        flash('Aucune école associée.', 'danger')
        return redirect(url_for('admin.dashboard', school_slug=school_slug))

    if request.method == 'POST':
        if request.files.get('import_file'):
            if not OPENPYXL_AVAILABLE:
                flash('Import Excel indisponible : installez openpyxl pour activer cette fonctionnalité.', 'warning')
                return redirect(url_for('admin.professors', school_slug=school_slug))

            workbook = openpyxl.load_workbook(request.files['import_file'])
            sheet = workbook.active
            header_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), None)
            headers = [str(cell).strip().lower() if cell else '' for cell in (header_row or [])]
            full_name_index = next((i for i, name in enumerate(headers) if name in ('full_name', 'nom_complet', 'nom complet', 'nom')), None)
            username_index = next((i for i, name in enumerate(headers) if name in ('username', 'utilisateur', 'user_name')), None)
            email_index = next((i for i, name in enumerate(headers) if name in ('email', 'courriel')), None)
            password_index = next((i for i, name in enumerate(headers) if name in ('password', 'mot_de_passe', 'mot_de_passe', 'motdepasse')), None)

            if full_name_index is None:
                flash('Le fichier doit contenir une colonne <code>full_name</code> ou <code>nom_complet</code>.', 'danger')
                return redirect(url_for('admin.professors', school_slug=school_slug))

            created = 0
            skipped = 0
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row:
                    continue
                full_name = str(row[full_name_index]).strip() if len(row) > full_name_index and row[full_name_index] else ''
                if not full_name:
                    skipped += 1
                    continue

                username = ''
                if username_index is not None and len(row) > username_index and row[username_index]:
                    username = str(row[username_index]).strip()
                if not username:
                    username = full_name

                if User.query.filter_by(username=username).first():
                    skipped += 1
                    continue

                email = str(row[email_index]).strip() if email_index is not None and len(row) > email_index and row[email_index] else None
                password = str(row[password_index]).strip() if password_index is not None and len(row) > password_index and row[password_index] else 'prof123'
                if not password:
                    password = 'prof123'

                professor = User(
                    school_id=school_id,
                    username=username,
                    full_name=full_name,
                    email=email,
                    role='professor',
                )
                professor.set_password(password)
                db.session.add(professor)
                created += 1

            db.session.commit()
            message = f'{created} professeur(s) importé(s) depuis Excel.'
            if skipped:
                message += f' {skipped} ligne(s) ignorée(s) en raison de données manquantes ou de doublons.'
            flash(message, 'success' if created else 'warning')
            return redirect(url_for('admin.professors', school_slug=school_slug))

        username = (request.form.get('username') or '').strip()
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        if not username or not password or not full_name:
            flash('Nom d\'utilisateur, mot de passe et nom complet sont obligatoires.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà utilisé.', 'warning')
        else:
            professor = User(
                school_id=school_id,
                username=username,
                full_name=full_name,
                email=email,
                role='professor',
            )
            professor.set_password(password)
            db.session.add(professor)
            db.session.commit()
            flash('Professeur créé avec succès.', 'success')
        return redirect(url_for('admin.professors', school_slug=school_slug))

    professors_list = User.query.filter_by(school_id=school_id, role='professor').order_by(User.full_name).all()
    return render_template('admin/professors.html', professors=professors_list)


@admin_bp.route('/professors/<int:professor_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_professor(professor_id, school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    professor = User.query.filter_by(id=professor_id, school_id=school_id, role='professor').first_or_404()

    if request.method == 'POST':
        professor.full_name = request.form.get('full_name') or professor.full_name
        professor.email = request.form.get('email')
        professor.username = request.form.get('username') or professor.username
        password = request.form.get('password')
        if password:
            professor.set_password(password)
        db.session.commit()
        flash('Professeur mis à jour.', 'success')
        return redirect(url_for('admin.professors', school_slug=school_slug))

    return render_template('admin/edit_professor.html', professor=professor)


@admin_bp.route('/professors/<int:professor_id>/delete', methods=['POST'])
@login_required
def delete_professor(professor_id, school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    professor = User.query.filter_by(id=professor_id, school_id=school_id, role='professor').first_or_404()
    Course.query.filter_by(professor_id=professor.id).update({'professor_id': None})
    db.session.delete(professor)
    db.session.commit()
    flash('Professeur supprimé.', 'success')
    return redirect(url_for('admin.professors', school_slug=school_slug))


@admin_bp.route('/professors/<int:professor_id>/reset-password', methods=['POST'])
@login_required
def reset_professor_password(professor_id, school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    professor = User.query.filter_by(id=professor_id, school_id=school_id, role='professor').first_or_404()
    professor.set_password('prof123')
    if hasattr(professor, 'must_change_password'):
        professor.must_change_password = True
    db.session.commit()
    flash('Mot de passe du professeur réinitialisé à prof123.', 'success')
    return redirect(url_for('admin.professors', school_slug=school_slug))


@admin_bp.route('/professors/reset-password', methods=['POST'])
@login_required
def reset_professor_password_form(school_slug=None):
    professor_id = request.form.get('professor_id')
    if not professor_id:
        flash('Veuillez sélectionner un professeur.', 'warning')
        return redirect(url_for('admin.school_reset', school_slug=school_slug))
    return reset_professor_password(int(professor_id), school_slug=school_slug)


@admin_bp.route('/school-reset')
@login_required
def school_reset(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    if not school_id:
        flash('Aucune école associée.', 'danger')
        return redirect(url_for('admin.dashboard', school_slug=school_slug))

    sections = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level, Section.class_name).all()
    section_names = sorted({section.name for section in sections})
    sections_catalog = [
        {
            'id': section.id,
            'name': section.name,
            'level': section.level,
            'class_name': section.class_name,
        }
        for section in sections
    ]
    professors = User.query.filter_by(school_id=school_id, role='professor').order_by(User.full_name).all()
    return render_template(
        'admin/school_reset.html',
        sections_catalog=sections_catalog,
        section_names=section_names,
        professors=professors,
    )


@admin_bp.route('/attendance')
@login_required
def attendance_management(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    if not school_id:
        flash('Aucune école associée.', 'danger')
        return redirect(url_for('admin.dashboard', school_slug=school_slug))

    year = session.get('academic_year', '2025 - 2026')
    sections = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level, Section.class_name).all()
    sections_catalog = [
        {
            'id': section.id,
            'name': section.name,
            'level': section.level,
            'class_name': section.class_name,
            'label': _attendance_class_label(section),
        }
        for section in sections
    ]
    records = (
        AttendanceRecord.query.filter_by(school_id=school_id, academic_year=year)
        .order_by(AttendanceRecord.attendance_date.desc())
        .limit(100)
        .all()
    )
    records_payload = []
    for record in records:
        section = record.section or (record.course.section if record.course and record.course.section else None)
        student_name = record.student.full_name() if record.student else ''
        student_gender = record.student.gender if record.student else None
        records_payload.append({
            'id': record.id,
            'attendance_date': record.attendance_date.isoformat() if record.attendance_date else '',
            'period': record.period or '',
            'student_name': student_name,
            'gender_label': 'Masculin' if student_gender == 'M' else 'Féminin' if student_gender == 'F' else '',
            'status': record.status,
            'status_label': ATTENDANCE_STATUS_MAP.get(record.status, record.status.title() if record.status else ''),
            'class_label': _attendance_class_label(section),
            'course_title': record.course.title if record.course else '',
        })
    return render_template(
        'admin/attendance.html',
        records=records_payload,
        sections_catalog=sections_catalog,
        attendance_status_options=ATTENDANCE_STATUS_OPTIONS,
        period_options=PERIOD_OPTIONS,
        today_iso=date.today().isoformat(),
    )


@admin_bp.route('/api/attendance/class/<int:section_id>', methods=['GET'])
@login_required
def get_class_attendance(section_id, school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    if not school_id:
        return jsonify({'error': 'Aucune école associée.'}), 400

    section = db.session.get(Section, section_id)
    if not section or section.school_id != school_id:
        return jsonify({'error': 'Classe non trouvée.'}), 404

    period = (request.args.get('period') or '').strip()
    if period not in ATTENDANCE_PERIOD_VALUES:
        return jsonify({'error': 'Période invalide.'}), 400

    attendance_day = _parse_attendance_date(request.args.get('date'))
    if not attendance_day:
        return jsonify({'error': 'Date de présence invalide.'}), 400

    year = session.get('academic_year', '2025 - 2026')
    students = Student.query.filter_by(
        school_id=school_id,
        section_id=section.id,
        academic_year=year,
    ).order_by(Student.last_name, Student.first_name).all()

    course = _get_attendance_course_for_section(section, school_id, period, create=False)
    records = []
    if course:
        records = AttendanceRecord.query.filter_by(
            school_id=school_id,
            course_id=course.id,
            attendance_date=attendance_day,
            period=period,
            academic_year=year,
        ).all()
    record_by_student = {record.student_id: record for record in records}

    payload_students = []
    for student in students:
        record = record_by_student.get(student.id)
        status = record.status if record and record.status in ATTENDANCE_STATUS_MAP else 'present'
        payload_students.append({
            'student_id': student.id,
            'full_name': student.full_name(),
            'gender': student.gender,
            'gender_label': 'Masculin' if student.gender == 'M' else 'Féminin' if student.gender == 'F' else '',
            'status': status,
            'status_label': ATTENDANCE_STATUS_MAP.get(status, 'Présent'),
        })

    return jsonify({
        'section': {
            'id': section.id,
            'name': section.name,
            'level': section.level,
            'class_name': section.class_name,
            'label': _attendance_class_label(section),
        },
        'attendance_date': attendance_day.isoformat(),
        'period': period,
        'academic_year': year,
        'course_id': course.id if course else None,
        'students': payload_students,
    })


@admin_bp.route('/api/attendance/class/<int:section_id>/save', methods=['POST'])
@login_required
def save_class_attendance(section_id, school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    if not school_id:
        return jsonify({'error': 'Aucune école associée.'}), 400

    section = db.session.get(Section, section_id)
    if not section or section.school_id != school_id:
        return jsonify({'error': 'Classe non trouvée.'}), 404

    data = request.get_json() or {}
    attendance_day = _parse_attendance_date(data.get('attendance_date'))
    period = str(data.get('period') or '').strip()
    entries = data.get('entries') or []

    if not attendance_day:
        return jsonify({'error': 'Date de présence invalide.'}), 400
    if period not in ATTENDANCE_PERIOD_VALUES:
        return jsonify({'error': 'Période invalide.'}), 400
    if not isinstance(entries, list):
        return jsonify({'error': 'entries doit être une liste.'}), 400

    year = session.get('academic_year', '2025 - 2026')
    students = Student.query.filter_by(
        school_id=school_id,
        section_id=section.id,
        academic_year=year,
    ).all()
    valid_student_ids = {student.id for student in students}
    if not valid_student_ids:
        return jsonify({'error': 'Aucun élève trouvé pour cette classe.'}), 404

    course = _get_attendance_course_for_section(section, school_id, period, create=True)
    if not course:
        return jsonify({'error': 'Impossible de préparer la classe pour la présence.'}), 500

    existing_records = AttendanceRecord.query.filter_by(
        school_id=school_id,
        course_id=course.id,
        attendance_date=attendance_day,
        period=period,
        academic_year=year,
    ).all()
    existing_by_student = {record.student_id: record for record in existing_records}

    created = 0
    updated = 0
    skipped = 0

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

        status = str(item.get('status', 'present')).strip().lower()
        if status not in ATTENDANCE_STATUS_MAP:
            skipped += 1
            continue

        record = existing_by_student.get(student_id)
        if record:
            record.status = status
            record.section_id = section.id
            record.professor_id = current_user.id
            updated += 1
            continue

        db.session.add(AttendanceRecord(
            school_id=school_id,
            section_id=section.id,
            course_id=course.id,
            student_id=student_id,
            professor_id=current_user.id,
            attendance_date=attendance_day,
            period=period,
            status=status,
            academic_year=year,
        ))
        created += 1

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Présences enregistrées avec succès.',
        'attendance_date': attendance_day.isoformat(),
        'period': period,
        'class_label': _attendance_class_label(section),
        'created': created,
        'updated': updated,
        'skipped': skipped,
    })


@admin_bp.route('/exam-management')
@login_required
def exam_management(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    from models import Section
    sections = Section.query.filter_by(school_id=school_id).all() if school_id else []
    return render_template('admin/exam_management.html', sections=sections)


@admin_bp.route('/payments', methods=['GET', 'POST'])
@login_required
def payments(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    if not school_id:
        flash('Aucune école associée.', 'danger')
        return redirect(url_for('admin.dashboard', school_slug=school_slug))

    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        amount = request.form.get('amount')
        payment_date_raw = request.form.get('payment_date')
        concept = request.form.get('concept')
        if not student_id or not amount:
            flash('Élève et montant obligatoires.', 'danger')
        else:
            payment = Payment(
                school_id=school_id,
                student_id=student_id,
                amount=amount,
                payment_date=datetime.strptime(payment_date_raw, '%Y-%m-%d').date() if payment_date_raw else date.today(),
                concept=concept,
            )
            db.session.add(payment)
            db.session.commit()
            flash('Paiement enregistré avec succès.', 'success')
        return redirect(url_for('admin.payments', school_slug=school_slug))

    payments_list = Payment.query.filter_by(school_id=school_id).order_by(Payment.payment_date.desc()).all()
    students = Student.query.filter_by(school_id=school_id).order_by(Student.last_name, Student.first_name).all()
    return render_template('admin/payments.html', payments=payments_list, students=students)


@admin_bp.route('/discipline')
@admin_bp.route('/cashier')
@login_required
def discipline_redirect(school_slug=None):
    target_slug = school_slug or (current_user.school.slug if current_user.school and current_user.school.slug else None)
    if current_user.is_discipline() or current_user.role == 'cashier':
        if target_slug:
            return redirect(url_for('professor.dashboard', school_slug=target_slug))
        return redirect(url_for('auth.redirect_by_role'))
    return redirect(url_for('auth.redirect_by_role'))


@admin_bp.route('/audit-logs')
@login_required
@require_super_admin
def audit_logs(school_slug=None):
    return _render_placeholder(
        'Audit & Sécurité',
        message='Consultation des journaux d\'activité, connexions et modifications de cotes.',
    )


@admin_bp.route('/backups')
@login_required
@require_super_admin
def backups(school_slug=None):
    return _render_placeholder('Sauvegarde & Restauration')


@admin_bp.route('/communications')
@login_required
@require_super_admin
def communications(school_slug=None):
    return _render_placeholder('Communications')


@admin_bp.route('/global-reports')
@login_required
@require_super_admin
def global_reports(school_slug=None):
    return _render_placeholder('Rapports Globaux')
