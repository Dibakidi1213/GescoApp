from types import SimpleNamespace

from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from models import AcademicYear, School, Section, Student, db
from routes.admin.helpers import get_school_id_for_admin_context, group_sections_for_display, require_super_admin
from routes.admin.services import apply_section_hierarchy_config
from routes.admin import admin_bp


@admin_bp.route('/academic-years', methods=['GET', 'POST'])
@login_required
@require_super_admin
def academic_years(school_slug=None):
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if not name:
            flash('Le nom de l\'année scolaire est obligatoire.', 'danger')
        elif AcademicYear.query.filter_by(name=name).first():
            flash('Cette année scolaire existe déjà.', 'warning')
        else:
            year = AcademicYear(name=name, is_active=bool(request.form.get('is_active')))
            if year.is_active:
                AcademicYear.query.update({'is_active': False})
            db.session.add(year)
            db.session.commit()
            flash('Année scolaire créée avec succès.', 'success')
        return redirect(url_for('admin.academic_years', school_slug=school_slug))

    years = AcademicYear.query.order_by(AcademicYear.name.desc()).all()
    return render_template('admin/academic_years.html', years=years)


@admin_bp.route('/academic-years/<int:year_id>/toggle', methods=['POST'])
@login_required
@require_super_admin
def toggle_academic_year_active(year_id, school_slug=None):
    year = AcademicYear.query.get_or_404(year_id)
    if not year.is_active:
        AcademicYear.query.update({'is_active': False})
        year.is_active = True
        session['academic_year'] = year.name
        flash(f"L'année scolaire {year.name} est maintenant active.", 'success')
    else:
        year.is_active = False
        flash(f"L'année scolaire {year.name} a été désactivée.", 'info')
    db.session.commit()
    return redirect(url_for('admin.academic_years', school_slug=school_slug))


@admin_bp.route('/academic-years/<int:year_id>/delete', methods=['POST'])
@login_required
@require_super_admin
def delete_academic_year(year_id, school_slug=None):
    year = AcademicYear.query.get_or_404(year_id)
    if year.is_active:
        flash('Impossible de supprimer l\'année scolaire active.', 'warning')
        return redirect(url_for('admin.academic_years', school_slug=school_slug))
    db.session.delete(year)
    db.session.commit()
    flash('Année scolaire supprimée.', 'success')
    return redirect(url_for('admin.academic_years', school_slug=school_slug))


@admin_bp.route('/sections', methods=['GET', 'POST'])
@login_required
def sections(school_slug=None):
    school_id = get_school_id_for_admin_context()
    schools = []
    selected_school_id = request.args.get('school_id', type=int)

    if current_user.is_super_admin() and not school_id:
        schools = School.query.order_by(School.name).all()
        if selected_school_id:
            school_id = selected_school_id

    if request.method == 'POST' and current_user.is_super_admin() and not school_id:
        school_id = request.form.get('school_id', type=int) or selected_school_id

    if not school_id:
        flash('Veuillez sélectionner une école pour gérer les sections.', 'info')
        return redirect(url_for('admin.dashboard', school_slug=school_slug))

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if request.is_json:
            data = request.get_json() or {}
            rows = data.get('rows') or []
        else:
            levels = request.form.getlist('level') or request.form.getlist('level[]')
            classes = request.form.getlist('class_name') or request.form.getlist('class_name[]')
            rows = list(zip(levels, classes)) if levels and classes else []

        if not name:
            flash('Le nom de section est obligatoire.', 'danger')
        else:
            if not rows:
                rows = [('1', 'A')]

            created = 0
            for level, class_name in rows:
                level = (level or '1').strip() or '1'
                class_name = (class_name or 'A').strip() or 'A'
                exists = Section.query.filter_by(
                    school_id=school_id,
                    name=name,
                    level=level,
                    class_name=class_name,
                ).first()
                if exists:
                    continue
                section = Section(
                    school_id=school_id,
                    name=name,
                    level=level,
                    class_name=class_name,
                )
                db.session.add(section)
                created += 1

            if created > 0:
                db.session.commit()
                flash('Section créée avec succès.', 'success')
            else:
                flash('Aucun nouvel enregistrement à créer. La structure existe déjà.', 'warning')
        return redirect(url_for('admin.sections', school_slug=school_slug))

    sections_query = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level, Section.class_name)
    section_groups = group_sections_for_display(sections_query.all())
    return render_template(
        'admin/sections.html',
        sections=section_groups,
        schools=schools,
        selected_school_id=school_id,
    )


@admin_bp.route('/sections/config/save', methods=['POST'])
@login_required
def save_section_config(school_slug=None):
    school_id = get_school_id_for_admin_context()
    if not school_id:
        return jsonify({'success': False, 'error': 'École non spécifiée.'}), 400

    data = request.get_json() or {}
    section_id = data.get('section_id')
    config = data.get('config') or {}
    section = Section.query.filter_by(id=section_id, school_id=school_id).first()
    if not section:
        return jsonify({'success': False, 'error': 'Section introuvable.'}), 404

    try:
        apply_section_hierarchy_config(school_id, section.name, config, replace_existing=True)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as exc:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(exc)}), 500


@admin_bp.route('/sections/<int:section_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_section(section_id, school_slug=None):
    section = Section.query.get_or_404(section_id)
    school_id = get_school_id_for_admin_context() or section.school_id
    if not current_user.is_super_admin() and section.school_id != current_user.school_id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('admin.sections', school_slug=school_slug))

    if request.method == 'POST' and request.is_json:
        data = request.get_json() or {}
        section_name = (data.get('name') or section.name).strip()
        config = data.get('config') or {}
        try:
            apply_section_hierarchy_config(section.school_id, section_name, config, replace_existing=True)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as exc:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(exc)}), 500

    related_sections = Section.query.filter_by(school_id=section.school_id, name=section.name).all()
    config = {}
    for item in related_sections:
        config.setdefault(item.level, [])
        if item.class_name not in config[item.level]:
            config[item.level].append(item.class_name)

    available_levels = [str(i) for i in range(1, 9)]
    return render_template(
        'admin/edit_section.html',
        section=section,
        section_config=config,
        available_levels=available_levels,
    )


@admin_bp.route('/sections/<int:section_id>/delete', methods=['POST'])
@login_required
def delete_section(section_id, school_slug=None):
    section = Section.query.get_or_404(section_id)
    if not current_user.is_super_admin() and section.school_id != current_user.school_id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('admin.sections', school_slug=school_slug))

    Section.query.filter_by(school_id=section.school_id, name=section.name).delete(synchronize_session=False)
    db.session.commit()
    flash('Section supprimée.', 'success')
    return redirect(url_for('admin.sections', school_slug=school_slug))


@admin_bp.route('/class-promotion', methods=['GET', 'POST'])
@login_required
def class_promotion(school_slug=None):
    school_id = get_school_id_for_admin_context() or current_user.school_id
    if not school_id:
        flash('Aucune école associée.', 'danger')
        return redirect(url_for('admin.dashboard', school_slug=school_slug))

    current_year = session.get('academic_year', '2025 - 2026')
    years = AcademicYear.query.order_by(AcademicYear.name.desc()).all()
    prev_year = None
    for index, year in enumerate(years):
        if year.name == current_year and index + 1 < len(years):
            prev_year = SimpleNamespace(year=years[index + 1].name, obj=years[index + 1])
            break

    prev_students = []
    dest_sections = Section.query.filter_by(school_id=school_id).order_by(Section.name, Section.level, Section.class_name).all()
    if prev_year:
        prev_students = Student.query.filter_by(school_id=school_id, academic_year=prev_year.year).order_by(Student.last_name).all()

    if request.method == 'POST':
        student_ids = request.form.getlist('student_ids')
        dest_section_id = request.form.get('dest_section_id', type=int)
        if not student_ids or not dest_section_id:
            flash('Sélectionnez des élèves et une classe de destination.', 'warning')
            return redirect(url_for('admin.class_promotion', school_slug=school_slug))

        promoted = 0
        for student_id in student_ids:
            student = Student.query.filter_by(id=student_id, school_id=school_id).first()
            if not student:
                continue
            student.section_id = dest_section_id
            student.academic_year = current_year
            promoted += 1
        db.session.commit()
        flash(f'{promoted} élève(s) promu(s) vers la nouvelle année scolaire.', 'success')
        return redirect(url_for('admin.class_promotion', school_slug=school_slug))

    return render_template(
        'admin/class_promotion.html',
        prev_year=prev_year,
        prev_students=prev_students,
        dest_sections=dest_sections,
    )
