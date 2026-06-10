from flask import Blueprint, request, jsonify, g, render_template
from flask_login import current_user
from models import db, Grade, Student, Teacher, Subject, Class, AuditLog
from roles import professeur_required
from forms import GradeForm
from auth import token_required

professeur_bp = Blueprint('professeur', __name__)

@professeur_bp.route('/saisie-cotes')
@professeur_required
def saisie_cotes_page():
    # Récupérer les données pour les filtres
    user = current_user
    teacher_assignments = Teacher.query.filter_by(user_id=user.id).all()

    classes = {}
    for t in teacher_assignments:
        cls = Class.query.get(t.class_id)
        subj = Subject.query.get(t.subject_id)
        if cls.id not in classes:
            classes[cls.id] = {
                'id': cls.id,
                'name': cls.name,
                'level': cls.level,
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

    # SÉCURITÉ: Vérifier que le professeur est bien assigné à cette classe/matière
    user = g.effective_user
    assignment = Teacher.query.filter_by(user_id=user.id, class_id=class_id, subject_id=subject_id).first()
    if not assignment:
        return jsonify({'message': 'Accès non autorisé à ce cours'}), 403

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
            '1èP': subject.max_1p,
            '2èP': subject.max_2p,
            'EXA1': subject.max_exa1,
            '3èP': subject.max_3p,
            '4èP': subject.max_4p,
            'EXA2': subject.max_exa2
        }
    }), 200

@professeur_bp.route('/api/save-grades', methods=['POST'])
@token_required
@professeur_required
def save_grades():
    data = request.get_json()
    # data format: { class_id, subject_id, period, grades: [{student_id, value}] , submit: bool }

    class_id = data.get('class_id')
    subject_id = data.get('subject_id')
    period = data.get('period')
    grades_data = data.get('grades')
    is_submit = data.get('submit', False)

    user = g.effective_user
    teacher_profile = Teacher.query.filter_by(user_id=user.id, class_id=class_id, subject_id=subject_id).first()

    if not teacher_profile:
        return jsonify({'message': 'Accès non autorisé à ce cours/classe'}), 403

    for item in grades_data:
        grade = Grade.query.filter_by(
            student_id=item['student_id'],
            subject_id=subject_id,
            period=period
        ).first()

        if grade:
            # SÉCURITÉ: Ne pas modifier si déjà soumis par le prof ou validé par le secrétaire
            if grade.status == 'submitted' or grade.status == 'validated':
                 continue
            grade.value = item['value']
            grade.status = 'submitted' if is_submit else 'draft'
        else:
            grade = Grade(
                student_id=item['student_id'],
                subject_id=subject_id,
                teacher_id=teacher_profile.id,
                value=item['value'],
                period=period,
                status='submitted' if is_submit else 'draft'
            )
            db.session.add(grade)

    db.session.commit()

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action='SAVE_GRADES',
        details=f"Sauvegarde des notes pour class_id={class_id}, subject_id={subject_id}, période={period}",
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({'message': 'Notes sauvegardées avec succès'}), 200
