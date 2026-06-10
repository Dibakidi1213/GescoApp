from flask import Blueprint, request, jsonify, g
from models import db, Attendance, Conduct, Incident
from roles import discipline_required
from forms import AttendanceForm, ConductForm, IncidentForm
from auth import token_required

discipline_bp = Blueprint('discipline', __name__)

@discipline_bp.route('/attendance', methods=['POST'])
@token_required
@discipline_required
def record_attendance():
    data = request.get_json()
    form = AttendanceForm(data=data, meta={'csrf': False})
    if form.validate():
        user = g.effective_user
        new_attendance = Attendance(
            student_id=form.student_id.data,
            class_id=form.class_id.data,
            date=form.date.data,
            status=form.status.data,
            recorded_by=user.id
        )
        db.session.add(new_attendance)
        db.session.commit()
        return jsonify({'message': 'Présence enregistrée'}), 201
    return jsonify({'errors': form.errors}), 400

@discipline_bp.route('/conduct', methods=['POST'])
@token_required
@discipline_required
def record_conduct():
    data = request.get_json()
    form = ConductForm(data=data, meta={'csrf': False})
    if form.validate():
        user = g.effective_user
        new_conduct = Conduct(
            student_id=form.student_id.data,
            type=form.type.data,
            severity=form.severity.data,
            description=form.description.data,
            recorded_by=user.id
        )
        db.session.add(new_conduct)
        db.session.commit()
        return jsonify({'message': 'Note de conduite enregistrée'}), 201
    return jsonify({'errors': form.errors}), 400

@discipline_bp.route('/incident', methods=['POST'])
@token_required
@discipline_required
def record_incident():
    data = request.get_json()
    form = IncidentForm(data=data, meta={'csrf': False})
    if form.validate():
        user = g.effective_user
        new_incident = Incident(
            student_id=form.student_id.data,
            category=form.category.data,
            description=form.description.data,
            severity=form.severity.data,
            recorded_by=user.id
        )
        db.session.add(new_incident)
        db.session.commit()
        return jsonify({'message': 'Incident enregistré'}), 201
    return jsonify({'errors': form.errors}), 400
