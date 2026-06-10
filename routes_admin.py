from flask import Blueprint, request, jsonify, g
from models import db, School, Class, User, Subject, Teacher, Student, AuditLog
from roles import admin_required
from forms import SchoolForm, ClassForm, UserForm
from auth import token_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard/stats', methods=['GET'])
@token_required
@admin_required
def get_dashboard_stats():
    """Récupère les statistiques pour le tableau de bord admin."""
    user = g.effective_user
    school_id = user.school_id

    if not school_id:
        return jsonify({'message': 'Aucune école associée à cet utilisateur'}), 400

    student_count = Student.query.join(Class).filter(Class.school_id == school_id).count()
    class_count = Class.query.filter_by(school_id=school_id).count()
    user_count = User.query.filter_by(school_id=school_id).count()
    # On pourrait ajouter plus de stats comme le nombre d'inscriptions du jour, etc.

    return jsonify({
        'student_count': student_count,
        'class_count': class_count,
        'user_count': user_count,
        'school_id': school_id
    }), 200

@admin_bp.route('/schools', methods=['POST'])
@token_required
@admin_required
def create_school():
    data = request.get_json()
    form = SchoolForm(data=data, meta={'csrf': False})
    if form.validate():
        new_school = School(
            name=form.name.data,
            address=form.address.data,
            year_start=form.year_start.data,
            year_end=form.year_end.data
        )
        db.session.add(new_school)
        db.session.commit()
        return jsonify({'message': 'École créée avec succès', 'id': new_school.id}), 201
    return jsonify({'errors': form.errors}), 400

@admin_bp.route('/classes', methods=['POST', 'GET'])
@token_required
@admin_required
def manage_classes():
    if request.method == 'POST':
        data = request.get_json()
        form = ClassForm(data=data, meta={'csrf': False})
        if form.validate():
            new_class = Class(
                name=form.name.data,
                school_id=form.school_id.data,
                level=form.level.data,
                capacity=form.capacity.data
            )
            db.session.add(new_class)
            db.session.commit()
            return jsonify({'message': 'Classe créée', 'id': new_class.id}), 201
        return jsonify({'errors': form.errors}), 400

    # GET
    school_id = g.effective_user.school_id
    classes = Class.query.filter_by(school_id=school_id).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'level': c.level,
        'capacity': c.capacity
    } for c in classes]), 200

@admin_bp.route('/subjects', methods=['POST', 'GET'])
@token_required
@admin_required
def manage_subjects():
    if request.method == 'POST':
        data = request.get_json()
        # Validation simple manuelle ici ou via un nouveau formulaire SubjectForm
        new_subject = Subject(
            name=data.get('name'),
            coefficient=data.get('coefficient', 1.0),
            class_id=data.get('class_id')
        )
        db.session.add(new_subject)
        db.session.commit()
        return jsonify({'message': 'Matière créée', 'id': new_subject.id}), 201

    class_id = request.args.get('class_id')
    subjects = Subject.query.filter_by(class_id=class_id).all() if class_id else Subject.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'coefficient': s.coefficient,
        'class_id': s.class_id
    } for s in subjects]), 200

@admin_bp.route('/attributions', methods=['POST', 'GET'])
@token_required
@admin_required
def manage_attributions():
    """Gérer l'attribution des professeurs aux matières et classes."""
    if request.method == 'POST':
        data = request.get_json()
        new_teacher = Teacher(
            user_id=data.get('user_id'),
            subject_id=data.get('subject_id'),
            class_id=data.get('class_id')
        )
        db.session.add(new_teacher)
        db.session.commit()
        return jsonify({'message': 'Attribution réussie', 'id': new_teacher.id}), 201

    # GET - Liste des attributions pour l'école
    school_id = g.effective_user.school_id
    attributions = Teacher.query.join(User).filter(User.school_id == school_id).all()
    return jsonify([{
        'id': t.id,
        'teacher_name': t.user.username,
        'subject_name': Subject.query.get(t.subject_id).name,
        'class_name': Class.query.get(t.class_id).name
    } for t in attributions]), 200

@admin_bp.route('/audit-logs', methods=['GET'])
@token_required
@admin_required
def get_audit_logs():
    """Récupère les journaux d'audit de l'école."""
    school_id = g.effective_user.school_id
    logs = AuditLog.query.join(User).filter(User.school_id == school_id).order_by(AuditLog.timestamp.desc()).all()
    return jsonify([{
        'id': log.id,
        'user': log.user.username,
        'action': log.action,
        'details': log.details,
        'ip': log.ip_address,
        'timestamp': log.timestamp.isoformat()
    } for log in logs]), 200
