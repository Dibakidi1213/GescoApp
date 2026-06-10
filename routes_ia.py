from flask import Blueprint, jsonify, request, g
from roles import admin_required, login_required
from ia.ia_anomalies import detect_grade_anomaly, detect_cheating_pattern
from ia.ia_recommendations import recommend_soutien, generate_action_plan
from ia.ia_appreciations import generate_appreciation
from ia.ia_prediction import predict_final_result, predict_risk_of_failure
from ia.ia_incidents import cluster_student_incidents, predict_future_risks

ia_bp = Blueprint('ia', __name__)

@ia_bp.route('/anomalies/grades/<int:student_id>', methods=['GET'])
@login_required
@admin_required
def check_grade_anomalies(student_id):
    grade_val = float(request.args.get('value', 0))
    subject_id = int(request.args.get('subject_id', 0))
    is_anomaly, score = detect_grade_anomaly(student_id, grade_val, subject_id)
    return jsonify({
        'is_anomaly': is_anomaly,
        'z_score': score,
        'recommendation': 'À vérifier manuellement' if is_anomaly else 'Normal'
    })

@ia_bp.route('/recommendations/soutien/<int:student_id>', methods=['GET'])
@login_required
def get_recommendations(student_id):
    recs = recommend_soutien(student_id)
    plan = generate_action_plan(student_id)
    return jsonify({
        'subjects_needing_help': recs,
        'action_plan': plan
    })

@ia_bp.route('/appreciation/generate/<int:student_id>', methods=['GET'])
@login_required
@admin_required
def get_appreciation(student_id):
    period = request.args.get('period', '1èP')
    text, level = generate_appreciation(student_id, period)
    return jsonify({
        'appreciation': text,
        'level': level
    })

@ia_bp.route('/prediction/results/<int:student_id>', methods=['GET'])
@login_required
@admin_required
def get_prediction(student_id):
    predicted = predict_final_result(student_id)
    risk = predict_risk_of_failure(student_id)
    return jsonify({
        'predicted_final_grade': predicted,
        'failure_risk_probability': risk,
        'status': 'Risque' if risk > 0.5 else 'En bonne voie'
    })

@ia_bp.route('/incidents/risks/<int:student_id>', methods=['GET'])
@login_required
@admin_required
def get_incident_risks(student_id):
    analysis = cluster_student_incidents(student_id)
    risk_level = predict_future_risks(student_id)
    return jsonify({
        'behavior_analysis': analysis,
        'future_risk_level': risk_level
    })
