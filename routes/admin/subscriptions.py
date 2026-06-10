from datetime import date, datetime

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import (
    RemoteSupportTicket,
    School,
    SchoolSubscription,
    SchoolSubscriptionPayment,
    db,
    sync_school_activation_with_subscription,
)
from routes.admin.helpers import build_subscription_snapshots, get_subscription_stats, require_super_admin
from routes.admin import admin_bp


@admin_bp.route('/subscriptions', methods=['GET', 'POST'])
@login_required
@require_super_admin
def subscriptions_management(school_slug=None):
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'subscription':
            school_id = request.form.get('school_id', type=int)
            if not school_id:
                flash('Veuillez sélectionner une école.', 'warning')
                return redirect(url_for('admin.subscriptions_management', school_slug=school_slug))

            subscription = SchoolSubscription(
                school_id=school_id,
                plan_name=request.form.get('plan_name'),
                billing_cycle=request.form.get('billing_cycle') or 'monthly',
                amount=request.form.get('amount') or 0,
                currency=request.form.get('currency') or 'USD',
                start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date(),
                status=request.form.get('status') or 'pending_payment',
                auto_renew=bool(request.form.get('auto_renew')),
                notes=request.form.get('notes'),
                created_by_user_id=current_user.id,
            )
            if subscription.status == 'active':
                subscription.activated_at = datetime.now()
            db.session.add(subscription)
            db.session.commit()

            school = School.query.get(school_id)
            if school:
                sync_school_activation_with_subscription(school)
                db.session.commit()
            flash('Abonnement enregistré avec succès.', 'success')

        elif form_type == 'support':
            ticket = RemoteSupportTicket(
                school_id=request.form.get('school_id', type=int),
                request_type=request.form.get('request_type') or 'maintenance',
                subject=request.form.get('subject'),
                description=request.form.get('description'),
                preferred_contact=request.form.get('preferred_contact'),
                remote_tool=request.form.get('remote_tool'),
                status='open',
                created_by_user_id=current_user.id,
            )
            scheduled_at = request.form.get('scheduled_at')
            if scheduled_at:
                ticket.scheduled_at = datetime.fromisoformat(scheduled_at)
            db.session.add(ticket)
            db.session.commit()
            flash('Ticket d\'assistance créé.', 'success')

        return redirect(url_for('admin.subscriptions_management', school_slug=school_slug))

    schools = School.query.order_by(School.name).all()
    stats = get_subscription_stats()
    subscriptions = SchoolSubscription.query.order_by(SchoolSubscription.created_at.desc()).all()
    recent_payments = (
        SchoolSubscriptionPayment.query.order_by(SchoolSubscriptionPayment.paid_on.desc())
        .limit(20)
        .all()
    )
    support_tickets = RemoteSupportTicket.query.order_by(RemoteSupportTicket.created_at.desc()).all()
    snapshots = build_subscription_snapshots(schools)

    return render_template(
        'admin/subscriptions.html',
        schools=schools,
        subscriptions=subscriptions,
        recent_payments=recent_payments,
        support_tickets=support_tickets,
        subscription_snapshots=snapshots,
        active_subscription_count=stats['active_subscription_count'],
        pending_subscription_count=stats['pending_subscription_count'],
        open_support_count=stats['open_support_count'],
    )


@admin_bp.route('/subscriptions/<int:subscription_id>/status', methods=['POST'])
@login_required
@require_super_admin
def update_subscription_status(subscription_id, school_slug=None):
    subscription = SchoolSubscription.query.get_or_404(subscription_id)
    subscription.status = request.form.get('status') or subscription.status
    if subscription.status == 'active' and not subscription.activated_at:
        subscription.activated_at = datetime.now()
    db.session.commit()

    if subscription.school:
        sync_school_activation_with_subscription(subscription.school)
        db.session.commit()
    flash('Statut de l\'abonnement mis à jour.', 'success')
    return redirect(url_for('admin.subscriptions_management', school_slug=school_slug))


@admin_bp.route('/subscriptions/<int:subscription_id>/payments', methods=['POST'])
@login_required
@require_super_admin
def add_subscription_payment(subscription_id, school_slug=None):
    subscription = SchoolSubscription.query.get_or_404(subscription_id)
    paid_on_raw = request.form.get('paid_on')
    paid_on = datetime.strptime(paid_on_raw, '%Y-%m-%d').date() if paid_on_raw else date.today()

    payment = SchoolSubscriptionPayment(
        school_id=subscription.school_id,
        subscription_id=subscription.id,
        amount=request.form.get('amount') or subscription.amount or 0,
        currency=subscription.currency,
        paid_on=paid_on,
        reference=request.form.get('reference'),
        status=request.form.get('payment_status') or 'confirmed',
        confirmed_by_user_id=current_user.id,
        confirmed_at=datetime.now(),
    )
    db.session.add(payment)

    if payment.status == 'confirmed' and subscription.status == 'pending_payment':
        subscription.status = 'active'
        subscription.activated_at = datetime.now()

    db.session.commit()
    if subscription.school:
        sync_school_activation_with_subscription(subscription.school)
        db.session.commit()

    flash('Paiement d\'abonnement enregistré.', 'success')
    return redirect(url_for('admin.subscriptions_management', school_slug=school_slug))


@admin_bp.route('/support-tickets/<int:ticket_id>/status', methods=['POST'])
@login_required
@require_super_admin
def update_support_ticket_status(ticket_id, school_slug=None):
    ticket = RemoteSupportTicket.query.get_or_404(ticket_id)
    status = request.form.get('status')
    if status:
        ticket.status = status
        if status == 'resolved':
            ticket.resolved_at = datetime.now()
            ticket.handled_by_user_id = current_user.id
    remote_tool = request.form.get('remote_tool')
    if remote_tool is not None:
        ticket.remote_tool = remote_tool
    resolution_notes = request.form.get('resolution_notes')
    if resolution_notes:
        ticket.resolution_notes = resolution_notes
    db.session.commit()
    flash('Ticket d\'assistance mis à jour.', 'success')
    return redirect(url_for('admin.subscriptions_management', school_slug=school_slug))
