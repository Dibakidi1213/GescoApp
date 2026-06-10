from flask import Blueprint, request, jsonify, g, send_file, Response
from models import db, Student, Grade, Bulletin, Class, Subject, User, AuditLog
from roles import secretaire_required
from forms import StudentForm
from roles import login_required as token_required
from pdf_generator import PDFGenerator
import io
import zipfile
from datetime import datetime
import os

secretaire_bp = Blueprint('secretaire', __name__)

@secretaire_bp.route('/dashboard', methods=['GET'])
@token_required
@secretaire_required
def dashboard():
    """Statistiques pour le tableau de bord secrétaire."""
    school_id = g.current_user.school_id
    total_students = Student.query.join(Class).filter(Class.school_id == school_id).count()
    pending_grades = Grade.query.filter_by(status='submitted').count()

    return jsonify({
        'total_students': total_students,
        'pending_grades_to_validate': pending_grades
    }), 200

@secretaire_bp.route('/students', methods=['GET', 'POST'])
@token_required
@secretaire_required
def manage_students():
    if request.method == 'POST':
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

    school_id = g.current_user.school_id
    students = Student.query.join(Class).filter(Class.school_id == school_id).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'class_name': s.current_class.name if s.current_class else 'N/A',
        'parent_phone': s.parent_phone
    } for s in students]), 200

@secretaire_bp.route('/grades/validate', methods=['POST'])
@token_required
@secretaire_required
def validate_grades():
    """Validation par le secrétaire des notes soumises par les professeurs."""
    data = request.get_json()
    grade_ids = data.get('grade_ids', [])

    user = g.current_user
    grades = Grade.query.filter(Grade.id.in_(grade_ids)).all()
    for grade in grades:
        grade.status = 'validated'
        grade.validated_by = user.id

    db.session.commit()

    audit = AuditLog(
        user_id=user.id,
        action='VALIDATE_GRADES',
        details=f"{len(grades)} notes validées",
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({'message': f'{len(grades)} notes validées'}), 200

@secretaire_bp.route('/bulletins/generate-official', methods=['POST'])
@token_required
@secretaire_required
def generate_official_bulletin():
    """Génère le bulletin officiel RDC au format PDF."""
    data = request.get_json()
    student_id = data.get('student_id')

    student = Student.query.get_or_404(student_id)
    class_obj = student.current_class
    school = class_obj.school
    subjects = Subject.query.filter_by(class_id=class_obj.id).all()
    grades = Grade.query.filter_by(student_id=student.id).all()

    pdf_content = PDFGenerator.generate_bulletin(student, subjects, grades, school, class_obj)

    if not pdf_content:
        return jsonify({'error': 'Erreur lors de la génération du PDF'}), 500

    # Sauvegarde optionnelle sur le serveur
    filename = f"bulletin_officiel_{student_id}.pdf"
    filepath = PDFGenerator.save_pdf(pdf_content, filename)

    # Enregistrement dans la base de données
    bulletin = Bulletin(
        student_id=student.id,
        period="Année Complète",
        generated_by=g.current_user.id,
        pdf_path=filepath
    )
    db.session.add(bulletin)
    db.session.commit()

    return Response(pdf_content, mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment;filename={filename}'})

@secretaire_bp.route('/bulletins/export-class/<int:class_id>', methods=['GET'])
@token_required
@secretaire_required
def export_class_bulletins(class_id):
    """Exporte tous les bulletins d'une classe dans un fichier ZIP."""
    class_obj = Class.query.get_or_404(class_id)
    students = class_obj.students
    school = class_obj.school
    subjects = Subject.query.filter_by(class_id=class_id).all()

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for student in students:
            grades = Grade.query.filter_by(student_id=student.id).all()
            pdf_content = PDFGenerator.generate_bulletin(student, subjects, grades, school, class_obj)
            if pdf_content:
                zf.writestr(f"bulletin_{student.name.replace(' ', '_')}.pdf", pdf_content)

    memory_file.seek(0)
    return send_file(memory_file, download_name=f"bulletins_{class_obj.name}.zip", as_attachment=True)
