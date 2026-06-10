from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, g
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from models import (
    Course,
    Grade,
    Payment,
    School,
    Section,
    Student,
    User,
    db,
    slugify,
    sync_school_activation_with_subscription,
)
from routes.admin.helpers import (
    build_subscription_snapshots,
    get_school_id_for_admin_context,
    require_super_admin,
    save_uploaded_logo,
)
from routes.admin import admin_bp


@admin_bp.route('/schools', methods=['GET', 'POST'])
@login_required
@require_super_admin
def schools(school_slug=None):
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if not name:
            flash('Le nom de l\'école est obligatoire.', 'danger')
            return redirect(url_for('admin.schools', school_slug=school_slug))

        school = School(
            name=name,
            slug=slugify(name),
            address=request.form.get('address'),
            province=request.form.get('province'),
            city=request.form.get('city'),
            commune=request.form.get('commune'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            bulletin_school_name=request.form.get('bulletin_school_name') or name,
            school_code=request.form.get('school_code'),
            slogan=request.form.get('slogan'),
            study_prefect_name=request.form.get('study_prefect_name'),
            ministry=request.form.get('ministry'),
            is_active=True,
        )
        db.session.add(school)
        db.session.flush()

        logo_url = request.form.get('logo')
        if request.files.get('logo_file'):
            try:
                logo_url = save_uploaded_logo(request.files.get('logo_file'), school=school)
            except ValueError as exc:
                flash(str(exc), 'warning')
        if logo_url:
            school.logo = logo_url

        try:
            db.session.commit()
            flash(f"L'école {name} a été créée avec succès.", 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Impossible de créer l\'école : slug ou nom déjà utilisé.', 'danger')
        return redirect(url_for('admin.schools', school_slug=school_slug))

    all_schools = School.query.order_by(School.name).all()
    snapshots = build_subscription_snapshots(all_schools)
    return render_template(
        'admin/schools.html',
        schools=all_schools,
        subscription_snapshots=snapshots,
    )


@admin_bp.route('/schools/<int:school_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_school(school_id, school_slug=None):
    school = School.query.get_or_404(school_id)
    if not current_user.is_super_admin() and current_user.school_id != school.id:
        flash('Accès non autorisé à cette école.', 'danger')
        return redirect(url_for('admin.dashboard', school_slug=school_slug))

    if request.method == 'POST':
        school.name = request.form.get('name') or school.name
        school.address = request.form.get('address')
        school.province = request.form.get('province')
        school.city = request.form.get('city')
        school.commune = request.form.get('commune')
        school.phone = request.form.get('phone')
        school.email = request.form.get('email')
        school.bulletin_school_name = request.form.get('bulletin_school_name') or school.name
        school.school_code = request.form.get('school_code')
        school.slogan = request.form.get('slogan')
        school.study_prefect_name = request.form.get('study_prefect_name')
        school.ministry = request.form.get('ministry') or school.ministry

        logo_url = request.form.get('logo')
        if request.files.get('logo_file'):
            try:
                logo_url = save_uploaded_logo(request.files.get('logo_file'), school=school)
            except ValueError as exc:
                flash(str(exc), 'warning')
        if logo_url:
            school.logo = logo_url

        db.session.commit()
        flash('Informations de l\'école mises à jour.', 'success')
        return redirect(url_for('admin.edit_school', school_id=school.id, school_slug=school_slug))

    return render_template('admin/edit_school.html', school=school)


@admin_bp.route('/schools/<int:school_id>/toggle', methods=['POST'])
@login_required
@require_super_admin
def toggle_school_active(school_id, school_slug=None):
    school = School.query.get_or_404(school_id)
    school.is_active = not school.is_active
    db.session.commit()
    status = 'activée' if school.is_active else 'désactivée'
    flash(f"L'école {school.name} a été {status}.", 'success')
    return redirect(url_for('admin.schools', school_slug=school_slug))


@admin_bp.route('/schools/<int:school_id>/delete', methods=['POST'])
@login_required
@require_super_admin
def delete_school(school_id, school_slug=None):
    school = School.query.get_or_404(school_id)
    school_name = school.name

    Grade.query.filter_by(school_id=school.id).delete(synchronize_session=False)
    Payment.query.filter_by(school_id=school.id).delete(synchronize_session=False)
    Student.query.filter_by(school_id=school.id).delete(synchronize_session=False)
    Course.query.filter_by(school_id=school.id).delete(synchronize_session=False)
    Section.query.filter_by(school_id=school.id).delete(synchronize_session=False)
    User.query.filter_by(school_id=school.id).delete(synchronize_session=False)
    db.session.delete(school)
    db.session.commit()
    flash(f"L'école {school_name} et ses données associées ont été supprimées.", 'success')
    return redirect(url_for('admin.schools', school_slug=school_slug))
