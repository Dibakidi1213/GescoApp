from flask import Blueprint, request, jsonify, g
from models import db, Attendance, Conduct, Incident, Class, Student
from roles import discipline_required
from forms import AttendanceForm, ConductForm, IncidentForm
from auth import token_required
from datetime import datetime

discipline_bp = Blueprint('discipline', __name__)

@discipline_bp.route('/sections', methods=['GET'])
@token_required
@discipline_required
def get_sections():
    """Récupère les sections uniques de l'école."""
    school_id = g.effective_user.school_id
    sections = db.session.query(Class.section).filter_by(school_id=school_id).distinct().all()
    return jsonify([s.section for s in sections if s.section]), 200

@discipline_bp.route('/levels', methods=['GET'])
@token_required
@discipline_required
def get_levels():
    """Récupère les niveaux pour une section donnée."""
    school_id = g.effective_user.school_id
    section = request.args.get('section')
    query = db.session.query(Class.level).filter_by(school_id=school_id)
    if section:
        query = query.filter_by(section=section)
    levels = query.distinct().all()
    return jsonify([l.level for l in levels if l.level]), 200

@discipline_bp.route('/classes', methods=['GET'])
@token_required
@discipline_required
def get_classes():
    """Récupère les classes pour une section et un niveau donnés."""
    school_id = g.effective_user.school_id
    section = request.args.get('section')
    level = request.args.get('level')
    query = Class.query.filter_by(school_id=school_id)
    if section:
        query = query.filter_by(section=section)
    if level:
        query = query.filter_by(level=level)
    classes = query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in classes]), 200

@discipline_bp.route('/students', methods=['GET'])
@token_required
@discipline_required
def get_students_by_class():
    """Récupère la liste des élèves d'une classe pour la prise de présence."""
    class_id = request.args.get('class_id')
    if not class_id:
        return jsonify({'message': 'class_id requis'}), 400

    students = Student.query.filter_by(class_id=class_id).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'gender': s.gender
    } for s in students]), 200

@discipline_bp.route('/attendance/bulk', methods=['POST'])
@token_required
@discipline_required
def record_bulk_attendance():
    """Enregistre les présences en masse pour une classe et une date donnée."""
    data = request.get_json()
    class_id = data.get('class_id')
    date_str = data.get('date')
    attendances = data.get('attendances') # Liste de {student_id, status}

    if not all([class_id, date_str, attendances]):
        return jsonify({'message': 'Données incomplètes'}), 400

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Format de date invalide (AAAA-MM-JJ)'}), 400

    user = g.effective_user
    for att in attendances:
        # On met à jour si ça existe déjà pour cet élève et cette date
        record = Attendance.query.filter_by(
            student_id=att['student_id'],
            date=date_obj
        ).first()

        if record:
            record.status = att['status']
            record.recorded_by = user.id
        else:
            new_att = Attendance(
                student_id=att['student_id'],
                class_id=class_id,
                date=date_obj,
                status=att['status'],
                recorded_by=user.id
            )
            db.session.add(new_att)

    db.session.commit()
    return jsonify({'message': 'Présences enregistrées avec succès'}), 201

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
