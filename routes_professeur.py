from flask import Blueprint, request, jsonify, g
from models import db, Grade, Student, Teacher, Subject
from roles import professeur_required
from forms import GradeForm
from auth import token_required

professeur_bp = Blueprint('professeur', __name__)

@professeur_bp.route('/grades', methods=['POST'])
@token_required
@professeur_required
def add_grade():
    data = request.get_json()
    form = GradeForm(data=data, meta={'csrf': False})

    if form.validate():
        user = g.effective_user
        # Correction : récupérer le profil Teacher associé à l'User
        teacher_profile = Teacher.query.filter_by(user_id=user.id).first()
        if not teacher_profile:
            return jsonify({'message': 'Profil enseignant non trouvé'}), 404

        new_grade = Grade(
            student_id=form.student_id.data,
            subject_id=form.subject_id.data,
            teacher_id=teacher_profile.id, # ID de la table Teacher, pas User
            value=form.value.data,
            period=form.period.data
        )
        db.session.add(new_grade)
        db.session.commit()
        return jsonify({'message': 'Note ajoutée avec succès'}), 201
    return jsonify({'errors': form.errors}), 400

@professeur_bp.route('/my-classes', methods=['GET'])
@token_required
@professeur_required
def get_my_classes():
    user = g.effective_user
    teachers = Teacher.query.filter_by(user_id=user.id).all()
    classes = []
    for t in teachers:
        classes.append({
            'class_id': t.class_id,
            'subject_id': t.subject_id
        })
    return jsonify(classes), 200
