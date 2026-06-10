from flask import Blueprint, render_template, request, jsonify, g
from models import db, Attendance, Conduct, Incident, Class, Student, AuditLog
from roles import discipline_required, login_required as token_required
from dashboard_utils import DashboardUtils
from forms import AttendanceForm, ConductForm, IncidentForm
from datetime import datetime

discipline_bp = Blueprint('discipline', __name__)

@discipline_bp.route('/dashboard')
@token_required
@discipline_required
def dashboard():
    """Rendu de la page dashboard discipline."""
    return render_template('dashboards/discipline.html')

@discipline_bp.route('/dashboard/stats', methods=['GET'])
@token_required
@discipline_required
def get_dashboard_stats():
    """API pour les statistiques de discipline."""
    stats = DashboardUtils.generate_discipline_stats(g.current_user.school_id)
    return jsonify(stats)

@discipline_bp.route('/attendance/bulk', methods=['POST'])
@token_required
@discipline_required
def record_bulk_attendance():
    data = request.get_json()
    class_id = data.get('class_id')
    date_str = data.get('date')
    attendances = data.get('attendances')

    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    user = g.current_user
    for att in attendances:
        record = Attendance.query.filter_by(student_id=att['student_id'], date=date_obj).first()
        if record:
            record.status = att['status']
            record.recorded_by = user.id
        else:
            db.session.add(Attendance(
                student_id=att['student_id'], class_id=class_id, date=date_obj,
                status=att['status'], recorded_by=user.id
            ))
    db.session.commit()
    return jsonify({'message': 'Présences enregistrées'}), 201

@discipline_bp.route('/incident', methods=['POST'])
@token_required
@discipline_required
def record_incident():
    data = request.get_json()
    form = IncidentForm(data=data, meta={'csrf': False})
    if form.validate():
        db.session.add(Incident(
            student_id=form.student_id.data, category=form.category.data,
            description=form.description.data, severity=form.severity.data,
            recorded_by=g.current_user.id
        ))
        db.session.commit()
        return jsonify({'message': 'Incident enregistré'}), 201
    return jsonify({'errors': form.errors}), 400
