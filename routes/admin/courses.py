from io import BytesIO

from flask import render_template, request, redirect, url_for, flash, send_file, jsonify, session, g
from flask_login import login_required, current_user

from models import AttendanceRecord, BulletinBranch, Course, School, Section, User, db, user_schools
from routes.admin.helpers import get_school_id_for_admin_context
from routes.admin.services import _get_bulletin_config_for_section, _serialize_branches
from routes.admin import admin_bp
from url_utils import encode_id, decode_id_or_int

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


def _school_professor_ids(school_id):
    """IDs des professeurs de l'école : école d'attache + professeurs explicitement liés."""
    if not school_id:
        return []
    linked_ids = [
        row[0] for row in db.session.query(user_schools.c.user_id)
        .filter(user_schools.c.school_id == school_id).all()
    ]
    return linked_ids


def _school_professors_query(school_id):
    """Requête des professeurs de l'école (attache + liés)."""
    linked_ids = _school_professor_ids(school_id)
    return User.query.filter(
        User.role == 'professor',
        db.or_(User.school_id == school_id, User.id.in_(linked_ids)),
    ).order_by(User.full_name)


def _build_sections_payload(sections):
    from url_utils import encode_id
    return [
        {
            'id': section.id,
            'token': encode_id(section.id),
            'name': section.name,
            'level': section.level,
            'class_name': section.class_name,
        }
        for section in sections
    ]


def _build_sorted_grouped(courses_list):
    buckets = {}
    for course in courses_list:
        # Exclude "Sous total" entries
        if 'sous total' in course.title.lower():
            continue
        section = course.section
        if section:
            key = (section.id, section.name, section.level, section.class_name)
        else:
            key = (0, 'Sans section', '-', '-')
        buckets.setdefault(key, []).append(course)

    return sorted(
        buckets.items(),
        key=lambda item: (str(item[0][1]), str(item[0][2]), str(item[0][3])),
    )


@admin_bp.route('/courses', methods=['GET', 'POST'])
@login_required
def courses(school_slug=None):
    schools = []
    selected_school_id = decode_id_or_int(request.args.get('school_id'))

    if current_user.is_super_admin() and not getattr(g, 'school_slug', None):
        schools = School.query.order_by(School.name).all()
        school_id = selected_school_id or get_school_id_for_admin_context()
    else:
        school_id = get_school_id_for_admin_context() or current_user.school_id

    if not school_id and not current_user.is_super_admin():
        flash('Aucune école associée.', 'danger')
        return redirect(url_for('admin.dashboard', school_slug=school_slug))

    effective_school_id = school_id

    if request.method == 'POST':
        if request.files.get('import_file'):
            if not OPENPYXL_AVAILABLE:
                flash('Import Excel indisponible : installez openpyxl.', 'warning')
                return redirect(url_for('admin.courses', school_slug=school_slug))
            flash('Import Excel des cours enregistré.', 'success')
            return redirect(url_for('admin.courses', school_slug=school_slug))

        if not effective_school_id:
            flash('Veuillez sélectionner une école.', 'warning')
            return redirect(url_for('admin.courses', school_slug=school_slug))

        section_id = request.form.get('section_id', type=int)
        target_ids_raw = request.form.getlist('target_section_ids')
        target_section_ids = [int(tid) for tid in target_ids_raw if tid.isdigit()]

        if not target_section_ids and section_id:
            target_section_ids = [section_id]

        titles_raw = request.form.getlist('titles[]')
        professor_id = request.form.get('professor_id', type=int)

        professor = User.query.filter_by(id=professor_id, school_id=effective_school_id).first() if professor_id else None

        if not target_section_ids or not titles_raw:
            flash('Au moins une classe et un intitulé de cours sont obligatoires.', 'danger')
            return redirect(url_for('admin.courses', school_slug=school_slug, add=1, section_id=encode_id(section_id)))
        else:
            added_count = 0
            skipped_count = 0
            for tid in target_section_ids:
                target_section = Section.query.filter_by(id=tid, school_id=effective_school_id).first()
                if not target_section:
                    continue
                for raw_val in titles_raw:
                    if not raw_val:
                        continue
                    parts = raw_val.split('|', 1)
                    if len(parts) == 2:
                        branch_id_str, title = parts
                        branch_id = int(branch_id_str) if branch_id_str.isdigit() else None
                    else:
                        branch_id = None
                        title = raw_val
                    
                    title = title.strip()
                    if title:
                        existing = Course.query.filter_by(
                            school_id=effective_school_id,
                            section_id=target_section.id,
                            title=title
                        ).first()
                        
                        if existing:
                            skipped_count += 1
                            continue

                        course = Course(
                            school_id=effective_school_id,
                            section_id=target_section.id,
                            title=title,
                            professor_id=professor.id if professor else None,
                            branch_id=branch_id or None,
                        )
                        db.session.add(course)
                        added_count += 1
            if added_count > 0:
                db.session.commit()
                msg = f'{added_count} cours créé(s) avec succès.'
                if len(target_section_ids) > 1:
                    msg += f' ({len(target_section_ids)} classes)'
                if skipped_count > 0:
                    msg += f' {skipped_count} doublon(s) ignoré(s).'
                flash(msg, 'success')
            else:
                if skipped_count > 0:
                    flash(f'{skipped_count} doublon(s) ignoré(s). Aucun cours ajouté.', 'warning')
                else:
                    flash('Aucun cours valide n\'a été soumis.', 'warning')
        return redirect(url_for('admin.courses', school_slug=school_slug, add=1, section_id=encode_id(section_id)))

    filter_section_id = decode_id_or_int(request.args.get('filter_section_id'))

    if effective_school_id:
        sections = Section.query.filter_by(school_id=effective_school_id).order_by(
            Section.name, Section.level, Section.class_name
        ).all()
        
        query = Course.query.filter_by(school_id=effective_school_id)
        if filter_section_id:
            query = query.filter_by(section_id=filter_section_id)
        courses_list = query.order_by(Course.title).all()
        
        professors = _school_professors_query(effective_school_id).all()
    else:
        sections = []
        query = Course.query
        if filter_section_id:
            query = query.filter_by(section_id=filter_section_id)
        courses_list = query.order_by(Course.title).all()
        professors = []

    selected_section_id = decode_id_or_int(request.args.get('section_id'))
    selected_section = None
    initial_branch_options = []
    if selected_section_id and effective_school_id:
        selected_section = Section.query.filter_by(
            id=selected_section_id,
            school_id=effective_school_id,
        ).first()
        if selected_section:
            year = session.get('academic_year', '2025 - 2026')
            config = _get_bulletin_config_for_section(effective_school_id, selected_section, year)
            existing_courses = Course.query.filter_by(section_id=selected_section.id, school_id=effective_school_id).all()
            existing_titles = {c.title.lower(): (c.professor.full_name if c.professor else 'Aucun') for c in existing_courses if c.title}
            
            initial_branch_options = []
            for branch in _serialize_branches(config):
                if branch.get('type') == 'branch' and 'total' not in branch.get('name', '').lower():
                    b_name_lower = branch.get('name', '').lower()
                    if b_name_lower in existing_titles:
                        branch['assigned_to'] = existing_titles[b_name_lower]
                    initial_branch_options.append(branch)

    return render_template(
        'admin/courses.html',
        courses=courses_list,
        sections=sections,
        sections_payload=_build_sections_payload(sections),
        sorted_grouped=_build_sorted_grouped(courses_list),
        professors=professors,
        schools=schools,
        selected_school_id=selected_school_id,
        selected_section=selected_section,
        initial_branch_options=initial_branch_options,
        selected_section_id=selected_section_id,
        filter_section_id=filter_section_id,
        open_add_tab=bool(request.args.get('add')),
    )


@admin_bp.route('/courses/<oid:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id, school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    course = Course.query.filter_by(id=course_id, school_id=school_id).first_or_404()
    sections = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level, Section.class_name).all()
    professors = _school_professors_query(school_id).all()

    if request.method == 'POST':
        course.title = request.form.get('title') or course.title
        new_section_id = request.form.get('section_id', type=int)
        if new_section_id:
            new_section = Section.query.filter_by(id=new_section_id, school_id=school_id).first()
            if not new_section:
                flash('Classe invalide.', 'danger')
                return redirect(url_for('admin.edit_course', course_id=course.id, school_slug=school_slug))
            course.section_id = new_section.id
        new_professor_id = request.form.get('professor_id', type=int)
        if new_professor_id:
            new_professor = User.query.filter_by(id=new_professor_id, school_id=school_id).first()
            if not new_professor:
                flash('Professeur invalide.', 'danger')
                return redirect(url_for('admin.edit_course', course_id=course.id, school_slug=school_slug))
            course.professor_id = new_professor.id
        elif new_professor_id == 0:
            course.professor_id = None
        course.branch_id = request.form.get('branch_id', type=int)
        db.session.commit()
        flash('Cours mis à jour.', 'success')
        return redirect(url_for('admin.courses', school_slug=school_slug))

    return render_template('admin/edit_course.html', course=course, sections=sections, professors=professors)


@admin_bp.route('/courses/<oid:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id, school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    course = Course.query.filter_by(id=course_id, school_id=school_id).first_or_404()

    # Supprimer les présences liées avant le cours (course_id NOT NULL)
    AttendanceRecord.query.filter_by(course_id=course.id).delete(synchronize_session=False)

    db.session.delete(course)
    db.session.commit()
    flash('Cours supprimé.', 'success')
    return redirect(url_for('admin.courses', school_slug=school_slug))


@admin_bp.route('/courses/template/download')
@login_required
def download_courses_template(school_slug=None):
    if not OPENPYXL_AVAILABLE:
        flash('Template Excel indisponible : installez openpyxl.', 'warning')
        return redirect(url_for('admin.courses', school_slug=school_slug))

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Cours'
    sheet.append(['Section', 'Niveau', 'Classe', 'Intitulé', 'Professeur'])
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name='template_import_cours.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


@admin_bp.route('/api/courses/bulletin-branches/<oid:section_id>')
@login_required
def api_courses_bulletin_branches(section_id, school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    section = Section.query.filter_by(id=section_id, school_id=school_id).first()
    if not section:
        return jsonify([])

    year = session.get('academic_year', '2025 - 2026')
    config = _get_bulletin_config_for_section(school_id, section, year)
    if not config:
        return jsonify([])

    branches = []
    existing_courses = Course.query.filter_by(section_id=section_id, school_id=school_id).all()
    existing_titles = {c.title.lower(): (c.professor.full_name if c.professor else 'Aucun') for c in existing_courses if c.title}

    for branch in config.branches.order_by(BulletinBranch.order, BulletinBranch.id).all():
        if branch.name and 'total' not in branch.name.lower() and branch.type == 'branch':
            b_name_lower = branch.name.lower()
            branches.append({
                'id': branch.id,
                'name': branch.name,
                'assigned_to': existing_titles.get(b_name_lower)
            })
    return jsonify(branches)


@admin_bp.route('/api/courses/assign-bulk', methods=['POST'])
@login_required
def api_assign_courses_bulk(school_slug=None):
    """
    Assign multiple courses to a single professor at once.
    Expected POST data:
    {
        "course_ids": [1, 2, 3, ...],
        "professor_id": 5
    }
    """
    school_id = get_school_id_for_admin_context() or current_user.school_id
    data = request.get_json() or {}
    
    course_ids = data.get('course_ids', [])
    professor_id = data.get('professor_id')
    
    if not course_ids or not isinstance(course_ids, list):
        return jsonify({'success': False, 'error': 'course_ids list required'}), 400
    
    # Validate professor exists if provided (professeur de l'école uniquement)
    if professor_id:
        professor = User.query.filter_by(id=professor_id, role='professor').first()
        if not professor or professor.id not in _school_professor_ids(school_id) and professor.school_id != school_id:
            return jsonify({'success': False, 'error': 'Professor not found'}), 404
    else:
        professor_id = None
    
    # Update all courses
    updated_count = 0
    try:
        courses = Course.query.filter(
            Course.id.in_(course_ids),
            Course.school_id == school_id
        ).all()
        
        for course in courses:
            course.professor_id = professor_id
            updated_count += 1
        
        db.session.commit()
        return jsonify({
            'success': True,
            'updated': updated_count,
            'message': f'{updated_count} cours mis à jour'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
