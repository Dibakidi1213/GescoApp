from flask import render_template, session, url_for, g
from flask_login import login_required, current_user

from models import (
    Grade,
    RemoteSupportTicket,
    School,
    SchoolSubscription,
    Student,
    User,
    db,
    sync_school_activation_with_subscription,
)
from routes.admin.helpers import (
    build_subscription_snapshots,
    get_recent_activity_for_school,
    get_subscription_stats,
    secretary_grades_url_for_user,
    sum_payments_for_school,
)
from routes.admin import admin_bp


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard(school_slug=None):
    year = session.get('academic_year', '2025 - 2026')
    is_super_admin = current_user.is_super_admin()
    secretary_grades_url = secretary_grades_url_for_user()
    schools = School.query.order_by(School.name).all() if is_super_admin else None

    if is_super_admin and not getattr(g, 'school_slug', None):
        stats = get_subscription_stats()
        school_count = School.query.count()
        school_admin_count = User.query.filter_by(role='school_admin').count()
        total_students = Student.query.count()
        total_enrollments = Student.query.filter_by(academic_year=year).count()
        total_professors_count = User.query.filter_by(role='professor').count()
        total_grades_count = Grade.query.count()
        usage_rate = round((total_grades_count / max(total_students, 1)) * 10, 1)
        usage_rate = min(usage_rate, 100)

        return render_template(
            'admin/dashboard.html',
            is_super_admin=True,
            school=None,
            schools=schools,
            school_count=school_count,
            school_admin_count=school_admin_count,
            total_students=total_students,
            total_enrollments=total_enrollments,
            active_subscription_school_count=stats['active_subscription_count'],
            pending_subscription_count=stats['pending_subscription_count'],
            open_support_count=stats['open_support_count'],
            total_professors_count=total_professors_count,
            total_grades_count=total_grades_count,
            usage_rate=usage_rate,
            secretary_grades_url=secretary_grades_url,
        )

    target_school = g.school if is_super_admin and getattr(g, 'school', None) else current_user.school
    target_school_id = target_school.id if target_school else current_user.school_id
    if not target_school_id:
        return render_template(
            'admin/dashboard.html',
            is_super_admin=is_super_admin,
            school=None,
            schools=schools,
            secretary_grades_url=secretary_grades_url,
        )

    if target_school:
        sync_school_activation_with_subscription(target_school)
        db.session.commit()

    student_count = Student.query.filter_by(school_id=target_school_id, academic_year=year).count()
    enrollment_count = student_count
    section_count = db.session.query(db.func.count(db.distinct(Student.section_id))).filter(
        Student.school_id == target_school_id,
        Student.academic_year == year,
    ).scalar() or 0
    user_count = User.query.filter_by(school_id=target_school_id).count()
    snapshots = build_subscription_snapshots([target_school] if target_school else [])
    subscription_snapshot = snapshots.get(target_school_id)
    support_open_count = RemoteSupportTicket.query.filter(
        RemoteSupportTicket.school_id == target_school_id,
        RemoteSupportTicket.status.in_(['open', 'in_progress']),
    ).count()

    return render_template(
        'admin/dashboard.html',
        is_super_admin=is_super_admin,
        school=target_school,
        schools=schools,
        student_count=student_count,
        enrollment_count=enrollment_count,
        section_count=section_count,
        user_count=user_count,
        subscription_snapshot=subscription_snapshot,
        support_open_count=support_open_count,
        payment_total=sum_payments_for_school(target_school_id),
        secretary_grades_url=secretary_grades_url,
    )
