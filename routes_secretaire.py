from flask import Blueprint, request, jsonify, g
from models import db, Student, Grade, Bulletin
from roles import secretaire_required
from forms import StudentForm
from auth import token_required
from datetime import datetime

secretaire_bp = Blueprint('secretaire', __name__)

@secretaire_bp.route('/students', methods=['POST'])
@token_required
@secretaire_required
def add_student():
    data = request.get_json()
    form = StudentForm(data=data, meta={'csrf': False})
    if form.validate():
        new_student = Student(
            name=form.name.data,
            birth_date=form.birth_date.data,
            class_id=form.class_id.data,
            parent_phone=form.parent_phone.data,
            parent_email=form.parent_email.data
        )
        db.session.add(new_student)
        db.session.commit()
        return jsonify({'message': 'Étudiant ajouté', 'id': new_student.id}), 201
    return jsonify({'errors': form.errors}), 400

@secretaire_bp.route('/bulletins/generate', methods=['POST'])
@token_required
@secretaire_required
def generate_bulletin():
    data = request.get_json()
    student_id = data.get('student_id')
    period = data.get('period')

    if not student_id or not period:
        return jsonify({'message': 'ID étudiant et période requis'}), 400

    user = g.effective_user
    new_bulletin = Bulletin(
        student_id=student_id,
        period=period,
        generated_by=user.id,
        pdf_path=f"/path/to/bulletins/{student_id}_{period}.pdf"
    )
    db.session.add(new_bulletin)
    db.session.commit()

    return jsonify({'message': 'Bulletin généré', 'bulletin_id': new_bulletin.id}), 201
