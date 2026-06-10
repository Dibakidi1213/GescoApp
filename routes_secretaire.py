from flask import Blueprint, request, jsonify, g, send_file
from models import db, Student, Grade, Bulletin, Class, Subject, User, AuditLog
from roles import secretaire_required
from forms import StudentForm
from auth import token_required
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

secretaire_bp = Blueprint('secretaire', __name__)

@secretaire_bp.route('/dashboard', methods=['GET'])
@token_required
@secretaire_required
def dashboard():
    """Statistiques pour le tableau de bord secrétaire."""
    school_id = g.effective_user.school_id
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

    school_id = g.effective_user.school_id
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

    user = g.effective_user
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

@secretaire_bp.route('/bulletins/generate', methods=['POST'])
@token_required
@secretaire_required
def generate_bulletin():
    """Génération réelle d'un bulletin PDF avec ReportLab."""
    data = request.get_json()
    student_id = data.get('student_id')
    period = data.get('period')

    student = Student.query.get_or_404(student_id)
    school = student.current_class.school

    # Création du dossier si inexistant
    upload_dir = 'uploads/bulletins'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    filename = f"bulletin_{student_id}_{period}.pdf"
    filepath = os.path.join(upload_dir, filename)

    # Logique ReportLab
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 50, school.name.upper())
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 70, school.address or "")

    c.line(50, height - 80, width - 50, height - 80)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 120, f"BULLETIN DE NOTES - {period}")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 140, f"Élève: {student.name}")
    c.drawString(50, height - 160, f"Classe: {student.current_class.name}")

    # Tableau des notes
    y = height - 200
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "MATIÈRE")
    c.drawString(300, y, "NOTE")
    c.drawString(400, y, "MAXIMA")
    c.line(50, y-5, width-50, y-5)

    y -= 20
    subjects = Subject.query.filter_by(class_id=student.class_id).all()
    total_obtained = 0
    total_max = 0

    c.setFont("Helvetica", 10)
    for sub in subjects:
        grade = Grade.query.filter_by(student_id=student.id, subject_id=sub.id, period=period).first()
        val = grade.value if grade else 0

        # Maxima dynamique selon période
        max_attr = f"max_{period.lower().replace('è', '')}"
        max_val = getattr(sub, max_attr, 10.0)

        c.drawString(50, y, sub.name)
        c.drawString(300, y, str(val))
        c.drawString(400, y, str(max_val))

        total_obtained += val
        total_max += max_val
        y -= 15
        if y < 50: # Nouvelle page simplifiée
            c.showPage()
            y = height - 50

    c.line(50, y, width-50, y)
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "TOTAL")
    c.drawString(300, y, f"{total_obtained} / {total_max}")
    percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
    c.drawString(450, y, f"{percentage:.2f}%")

    c.save()

    # Enregistrer dans la DB
    new_bulletin = Bulletin(
        student_id=student_id,
        period=period,
        generated_by=g.effective_user.id,
        pdf_path=filepath
    )
    db.session.add(new_bulletin)

    audit = AuditLog(
        user_id=g.effective_user.id,
        action='GENERATE_BULLETIN',
        details=f"Bulletin généré pour l'élève ID {student_id}, période {period}",
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({'message': 'Bulletin généré', 'url': f'/api/secretaire/bulletins/download/{new_bulletin.id}'}), 201

@secretaire_bp.route('/bulletins/download/<int:bulletin_id>', methods=['GET'])
@token_required
@secretaire_required
def download_bulletin(bulletin_id):
    bulletin = Bulletin.query.get_or_404(bulletin_id)
    return send_file(bulletin.pdf_path, as_attachment=True)
