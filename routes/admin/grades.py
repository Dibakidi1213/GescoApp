from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user

from models import BulletinConfig, Course, DeliberationResult, Grade, Notification, Section, Student, db
from routes.admin.helpers import PERIODS, PERIOD_OPTIONS, get_school_id_for_admin_context
from routes.admin.services import build_centralization_context, build_grades_map_for_student, get_bulletin_config_for_student, compute_class_ranks, get_student_conducts, get_failed_courses_for_student
from routes.secretary import _get_section_by_hierarchy
from routes.admin import admin_bp


def get_today_formatted():
    """Retourne la date du jour au format JJ/MM/AAAA."""
    return datetime.now().strftime('%d/%m/%Y')


def get_max_for_period(period, branch):
    """Récupère le maximum pour une période donnée depuis la branche du bulletin."""
    if not branch:
        return 20  # valeur par défaut
    
    # Mapper les périodes aux champs max correspondants
def get_max_for_period(period, branch):
    """Retourne le maximum autorisé pour une période donnée."""
    # Maximum fixé pour REPECHAGE
    if period == 'REPECHAGE':
        return 100
    
    period_to_max = {
        'PERIODE 1': 'max_period_1',
        'PERIODE 2': 'max_period_2',
        'EXA1': 'max_exam_1',
        'PERIODE 3': 'max_period_3',
        'PERIODE 4': 'max_period_4',
        'EXA2': 'max_exam_2',
    }
    
    max_field = period_to_max.get(period, 'max_value')
    max_val = getattr(branch, max_field, None)
    return float(max_val) if max_val else 20


def is_student_failed_for_course(student_id, course_id, school_id, year):
    """Vérifie si un étudiant a échoué pour un cours (score annuel < 50%)."""
    course = Course.query.filter_by(id=course_id, school_id=school_id).first()
    if not course or not course.branch:
        return False
    
    # Récupérer tous les grades de l'étudiant pour ce cours (sauf REPECHAGE)
    grades = Grade.query.filter_by(
        school_id=school_id,
        student_id=student_id,
        course_id=course_id,
        academic_year=year,
    ).all()
    
    # Calculer le score annuel
    total_score = sum(float(g.value) for g in grades if g.value and g.period != 'REPECHAGE')
    
    # Calculer le maximum annuel
    branch = course.branch
    max_annual = (float(branch.max_period_1 or 0) * 2) + (float(branch.max_exam_1 or 0)) + \
                 (float(branch.max_period_1 or 0) * 2) + (float(branch.max_exam_1 or 0))
    
    if max_annual == 0:
        return False
    
    # Vérifier si l'élève a échoué (< 50%)
    return (total_score / max_annual) < 0.5


def _create_notification(*, school_id, recipient_id, title, message, notification_type, actor_id=None):
    notification = Notification(
        school_id=school_id,
        recipient_id=recipient_id,
        actor_id=actor_id,
        notification_type=notification_type,
        title=title,
        message=message,
    )
    db.session.add(notification)
    return notification


@admin_bp.route('/grades')
@login_required
def grades_management(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    if not school_id:
        flash('Aucune école associée.', 'danger')
        return redirect(url_for('admin.dashboard', school_slug=school_slug))

    year = session.get('academic_year', '2025 - 2026')
    sections = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level, Section.class_name).all()
    sections_payload = [
        {
            'id': section.id,
            'name': section.name,
            'level': section.level,
            'class_name': section.class_name,
        }
        for section in sections
    ]

    selected_section_name = request.args.get('section_name')
    selected_level = request.args.get('level')
    selected_class_name = request.args.get('class_name')
    selected_period = request.args.get('period') or PERIODS[0]
    selected_course_id = request.args.get('course_id', type=int)

    selected_section = _get_section_by_hierarchy(
        school_id,
        section_name=selected_section_name,
        level=selected_level,
        class_name=selected_class_name,
    )
    courses = []
    students = []
    grades_map = {}
    selected_course = None
    selected_course_submitted_count = 0

    if selected_section:
        courses = Course.query.filter_by(school_id=school_id, section_id=selected_section.id).order_by(Course.title).all()
        students = Student.query.filter_by(
            school_id=school_id,
            section_id=selected_section.id,
            academic_year=year,
        ).order_by(Student.last_name, Student.first_name).all()

    if selected_course_id:
        selected_course = Course.query.filter_by(id=selected_course_id, school_id=school_id).first()
        if selected_course:
            # Si c'est pour la saisie de repêchage, filtrer les élèves qui ont échoué
            if selected_period == 'REPECHAGE':
                students = [s for s in students if is_student_failed_for_course(s.id, selected_course.id, school_id, year)]
            
            grades = Grade.query.filter_by(
                school_id=school_id,
                course_id=selected_course.id,
                period=selected_period,
                academic_year=year,
            ).all()
            grades_map = {grade.student_id: float(grade.value) if grade.value is not None else '' for grade in grades}
            selected_course_submitted_count = Grade.query.filter_by(
                school_id=school_id,
                course_id=selected_course.id,
                period=selected_period,
                academic_year=year,
                submitted=True,
            ).count()

    section_name_options = sorted({section.name for section in sections}, key=lambda value: value.lower())

    # Get the maximum for the selected period and course branch
    max_for_period = 20  # default
    if selected_course and selected_course.branch:
        max_for_period = get_max_for_period(selected_period, selected_course.branch)

    return render_template(
        'admin/grades.html',
        sections_payload=sections_payload,
        section_name_options=section_name_options,
        selected_section=selected_section,
        selected_section_id=selected_section.id if selected_section else None,
        selected_section_name=selected_section_name,
        selected_level=selected_level,
        selected_class_name=selected_class_name,
        selected_period=selected_period,
        selected_course_id=selected_course_id,
        selected_course=selected_course,
        selected_course_submitted_count=selected_course_submitted_count,
        period_options=PERIOD_OPTIONS,
        courses=courses,
        students=students,
        grades_map=grades_map,
        max_for_period=max_for_period,
    )


@admin_bp.route('/grades/save', methods=['POST'])
@login_required
def save_grade_admin(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    student_id = request.form.get('student_id', type=int)
    course_id = request.form.get('course_id', type=int)
    period = request.form.get('period')
    value = request.form.get('value')
    year = session.get('academic_year', '2025 - 2026')

    if not student_id or not course_id or not period:
        flash('Données de note incomplètes.', 'danger')
        return redirect(url_for('admin.grades_management', school_slug=school_slug))

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        flash('Valeur de note invalide.', 'danger')
        return redirect(request.referrer or url_for('admin.grades_management', school_slug=school_slug))

    grade = Grade.query.filter_by(
        school_id=school_id,
        student_id=student_id,
        course_id=course_id,
        period=period,
        academic_year=year,
    ).first()
    old_value = float(grade.value) if grade and grade.value is not None else None
    if grade is None:
        grade = Grade(
            school_id=school_id,
            student_id=student_id,
            course_id=course_id,
            period=period,
            value=numeric_value,
            academic_year=year,
        )
        db.session.add(grade)
    else:
        grade.value = numeric_value

    grade.submitted = True
    grade.submitted_at = datetime.now()
    grade.submitted_by = current_user.id

    professor = grade.course.professor if grade.course else None
    if professor and old_value is not None and float(old_value) != float(numeric_value):
        student = grade.student
        student_name = student.full_name() if student else "l'eleve"
        _create_notification(
            school_id=school_id,
            recipient_id=professor.id,
            actor_id=current_user.id,
            notification_type='grade_updated_by_secretary',
            title='Cote modifiee par le secretariat',
            message=(
                f'Le secretariat a modifie la cote de {student_name} '
                f'pour {grade.course.title} ({period}) : {old_value:g} -> {numeric_value:g}.'
            ),
        )

    db.session.commit()
    flash('Cote enregistrée et finalisée.', 'success')

    redirect_args = {
        'section_name': request.form.get('section_name'),
        'level': request.form.get('level'),
        'class_name': request.form.get('class_name'),
        'course_id': course_id,
        'period': period,
        'school_slug': school_slug,
    }
    return redirect(url_for('admin.grades_management', **redirect_args))


@admin_bp.route('/grades/unlock-course/<int:course_id>', methods=['POST'])
@login_required
def unlock_course_period(course_id, school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
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
        submitted=True,
    ).all()

    professor = course.professor if course else None
    for grade in grades:
        grade.submitted = False

    if professor and grades:
        _create_notification(
            school_id=school_id,
            recipient_id=professor.id,
            actor_id=current_user.id,
            notification_type='period_unlocked_by_secretary',
            title='Période déverrouillée par le secrétariat',
            message=(
                f'Le secrétariat a déverrouillé la période {period} '
                f'pour le cours {course.title}. Vous pouvez reprendre les modifications.'
            ),
        )

    db.session.commit()
    return jsonify({
        'success': True,
        'message': f'Toutes les notes de {period} ont été déverrouillées.',
        'count': len(grades),
    })


@admin_bp.route('/secretary')
@login_required
def secretary_dashboard(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    year = session.get('academic_year', '2025 - 2026')
    student_count = Student.query.filter_by(school_id=school_id, academic_year=year).count()
    section_count = Section.query.filter_by(school_id=school_id).count()
    latest_students = Student.query.filter_by(school_id=school_id, academic_year=year).order_by(
        Student.registered_at.desc()
    ).limit(5).all()
    return render_template(
        'admin/secretary.html',
        student_count=student_count,
        section_count=section_count,
        latest_students=latest_students,
    )


@admin_bp.route('/secretary/centralization')
@login_required
def secretary_centralization(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    year = session.get('academic_year', '2025 - 2026')
    section_id = request.args.get('section_id', type=int)
    scope = request.args.get('scope') or PERIODS[0]
    context = build_centralization_context(school_id, section_id, scope, year)
    context['academic_year'] = year
    return render_template('admin/centralization.html', **context)


@admin_bp.route('/bulletins/report')
@login_required
def bulletins_report(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    year = session.get('academic_year', '2025 - 2026')
    student_id = request.args.get('student_id', type=int)
    section_id = request.args.get('section_id', type=int)
    preview = request.args.get('preview') == '1'
    embedded = request.args.get('embedded') == '1'

    # Prévisualisation de toute une section
    if section_id and preview:
        students = Student.query.filter_by(
            school_id=school_id,
            section_id=section_id,
            academic_year=year,
        ).order_by(Student.last_name, Student.first_name).all()
        section = Section.query.filter_by(id=section_id, school_id=school_id).first()

        bulletin_config = (
            get_bulletin_config_for_student(students[0], school_id, year)
            if students else None
        )


        class_ranks, total_students = compute_class_ranks(school_id, section_id, year)

        # Load annual deliberation results for the selected section
        student_ids = [student.id for student in students]
        results_by_student = {}
        if student_ids:
            results = DeliberationResult.query.filter(
                DeliberationResult.school_id == school_id,
                DeliberationResult.academic_year == year,
                DeliberationResult.period == 'ANNEE',
                DeliberationResult.student_id.in_(student_ids),
            ).all()
            results_by_student = {r.student_id: r for r in results}

        # Build a list of context dictionaries for each student's bulletin
        bulletins = []
        for student in students:
            grades_map, branches, bulletin_totals = build_grades_map_for_student(
                student, school_id, year
            )
            
            student_ranks = class_ranks.get(student.id, {})
            conducts = get_student_conducts(student.id, school_id, year)
            deliberation_result = results_by_student.get(student.id)
            failed_courses = get_failed_courses_for_student(student.id, school_id, year)

            # Append a dict with all needed variables for the batch template
            bulletins.append({
                'student': student,
                'school': student.school,
                'branches': branches,
                'grades_map': grades_map,
                'bulletin_totals': bulletin_totals,
                'config': bulletin_config,
                'student_ranks': student_ranks,
                'total_students': total_students,
                'conducts': conducts,
                'deliberation_result': deliberation_result,
                'embedded': embedded,
                'failed_courses': failed_courses,
            })
        
        return render_template(
            'admin/bulletins_batch.html',
            bulletins=bulletins,
            selected_section=section,
            embedded=embedded,
            config=bulletin_config,
            today=get_today_formatted(),
        )

    # Vue d'un seul élève
    if not student_id:
        flash('Élève non spécifié.', 'warning')
        return redirect(url_for('admin.grades_management', school_slug=school_slug))

    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()
    bulletin_config = get_bulletin_config_for_student(student, school_id, year)

    grades_map, branches, bulletin_totals = build_grades_map_for_student(
        student, school_id, year
    )
    
    class_ranks, total_students = compute_class_ranks(school_id, student.section.id, year)
    student_ranks = class_ranks.get(student.id, {})
    conducts = get_student_conducts(student.id, school_id, year)
    deliberation_result = DeliberationResult.query.filter_by(
        school_id=school_id,
        student_id=student.id,
        academic_year=year,
        period='ANNEE',
    ).first()
    failed_courses = get_failed_courses_for_student(student.id, school_id, year)

    return render_template(
        'admin/bulletin.html',
        student=student,
        school=student.school,
        branches=branches,
        grades_map=grades_map,
        bulletin_totals=bulletin_totals,
        config=bulletin_config,
        student_ranks=student_ranks,
        total_students=total_students,
        conducts=conducts,
        deliberation_result=deliberation_result,
        embedded=embedded,
        failed_courses=failed_courses,
        today=get_today_formatted(),
    )
