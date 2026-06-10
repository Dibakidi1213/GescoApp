from flask import Blueprint, render_template, request, jsonify, g
from models import db, Grade, Student, Subject, Teacher, Class, AuditLog
from roles import professeur_required, login_required as token_required
from dashboard_utils import DashboardUtils
from datetime import datetime

professeur_bp = Blueprint('professeur', __name__)

@professeur_bp.route('/dashboard')
@token_required
@professeur_required
def dashboard():
    """Rendu de la page dashboard professeur."""
    return render_template('dashboards/professeur.html')

@professeur_bp.route('/dashboard/stats', methods=['GET'])
@token_required
@professeur_required
def get_dashboard_stats():
    """API pour les statistiques du professeur."""
    stats = DashboardUtils.generate_professeur_stats(g.current_user.id)
    return jsonify(stats)

@professeur_bp.route('/saisie-cotes')
@token_required
@professeur_required
def saisie_cotes():
    user = g.current_user
    assignments = Teacher.query.filter_by(user_id=user.id).all()

    classes = {}
    for ta in assignments:
        cls = ta.class_level
        subj = ta.subject
        if cls.id not in classes:
            classes[cls.id] = {
                'name': cls.name,
                'section': cls.section,
                'subjects': []
            }
        classes[cls.id]['subjects'].append({
            'id': subj.id,
            'name': subj.name
        })

    return render_template('professeur/saisie_cotes.html', classes=classes)

@professeur_bp.route('/api/load-grades', methods=['GET'])
@token_required
@professeur_required
def load_grades():
    class_id = request.args.get('class_id')
    subject_id = request.args.get('subject_id')

    if not class_id or not subject_id:
        return jsonify({'message': 'Paramètres manquants'}), 400

    user = g.current_user
    assignment = Teacher.query.filter_by(user_id=user.id, class_id=class_id, subject_id=subject_id).first()
    if not assignment:
        return jsonify({'message': 'Accès non autorisé'}), 403

    students = Student.query.filter_by(class_id=class_id).all()
    subject = Subject.query.get(subject_id)

    data = []
    for student in students:
        grades = Grade.query.filter_by(student_id=student.id, subject_id=subject_id).all()
        grade_map = {g.period: g.value for g in grades}
        data.append({
            'student_id': student.id,
            'student_name': student.name,
            'grades': grade_map
        })

    return jsonify({
        'students': data,
        'maxima': {
            '1èP': subject.max_1p, '2èP': subject.max_2p, 'EXA1': subject.max_exa1,
            '3èP': subject.max_3p, '4èP': subject.max_4p, 'EXA2': subject.max_exa2
        }
    }), 200

@professeur_bp.route('/api/save-grades', methods=['POST'])
@token_required
@professeur_required
def save_grades():
    data = request.get_json()
    class_id = data.get('class_id')
    subject_id = data.get('subject_id')
    period = data.get('period')
    grades_data = data.get('grades')
    is_submit = data.get('submit', False)

    user = g.current_user
    teacher_profile = Teacher.query.filter_by(user_id=user.id, class_id=class_id, subject_id=subject_id).first()

    if not teacher_profile:
        return jsonify({'message': 'Accès non autorisé'}), 403

    for item in grades_data:
        grade = Grade.query.filter_by(student_id=item['student_id'], subject_id=subject_id, period=period).first()
        if grade:
            if grade.status in ['submitted', 'validated']: continue
            grade.value = item['value']
            grade.status = 'submitted' if is_submit else 'draft'
        else:
            grade = Grade(
                student_id=item['student_id'], subject_id=subject_id, teacher_id=teacher_profile.id,
                value=item['value'], period=period, status='submitted' if is_submit else 'draft'
            )
            db.session.add(grade)

    db.session.commit()
    return jsonify({'message': 'Notes sauvegardées'}), 200
