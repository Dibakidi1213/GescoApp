from flask import Blueprint, render_template, request, jsonify, send_file, g
from models import db, Student, Grade, Subject, Bulletin, Class, School, Teacher
from roles import secretaire_required, login_required as token_required
from pdf_generator import generate_bulletin_pdf
from dashboard_utils import DashboardUtils
import os

secretaire_bp = Blueprint('secretaire', __name__)

@secretaire_bp.route('/dashboard')
@token_required
@secretaire_required
def dashboard():
    """Rendu de la page dashboard secrétaire."""
    return render_template('dashboards/secretaire.html')

@secretaire_bp.route('/dashboard/stats', methods=['GET'])
@token_required
@secretaire_required
def get_dashboard_stats():
    """API pour les statistiques du secrétaire."""
    school_id = g.current_user.school_id
    period = request.args.get('period', '1èP')
    stats = DashboardUtils.generate_secretaire_stats(school_id, period)
    return jsonify(stats)

@secretaire_bp.route('/bulletins/generate', methods=['POST'])
@token_required
@secretaire_required
def generate_bulletins():
    data = request.get_json()
    student_id = data.get('student_id')
    period = data.get('period')

    # Récupération des données nécessaires
    student = Student.query.get(student_id)
    school = School.query.get(g.current_user.school_id)
    class_obj = Class.query.get(student.class_id)

    # On génère le PDF
    pdf_path = f"bulletins/bulletin_{student_id}_{period}.pdf"
    os.makedirs('bulletins', exist_ok=True)

    if generate_bulletin_pdf(student_id, period, pdf_path):
        # Enregistrer en DB
        bulletin = Bulletin(
            student_id=student_id,
            period=period,
            generated_by=g.current_user.id,
            pdf_path=pdf_path
        )
        db.session.add(bulletin)
        db.session.commit()
        return jsonify({'message': 'Bulletin généré', 'path': pdf_path}), 200

    return jsonify({'message': 'Erreur lors de la génération'}), 500

@secretaire_bp.route('/bulletins/download/<int:bulletin_id>')
@token_required
@secretaire_required
def download_bulletin(bulletin_id):
    bulletin = Bulletin.query.get_or_404(bulletin_id)
    return send_file(bulletin.pdf_path, as_attachment=True)

@secretaire_bp.route('/validate-grades', methods=['POST'])
@token_required
@secretaire_required
def validate_grades():
    data = request.get_json()
    grade_ids = data.get('grade_ids', [])

    Grade.query.filter(Grade.id.in_(grade_ids)).update({
        'status': 'validated',
        'validated_by': g.current_user.id
    }, synchronize_session=False)

    db.session.commit()
    return jsonify({'message': f'{len(grade_ids)} notes validées'}), 200
