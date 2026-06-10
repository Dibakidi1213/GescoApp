from models import db, Grade, Student, Subject, Attendance

def recommend_soutien(student_id):
    """
    Identifie les matières nécessitant un soutien basé sur les performances.
    """
    recent_grades = Grade.query.filter_by(student_id=student_id).order_by(Grade.submitted_at.desc()).limit(20).all()

    # Calculer la moyenne par matière
    subject_stats = {}
    for g in recent_grades:
        if g.subject_id not in subject_stats:
            subject_stats[g.subject_id] = []
        subject_stats[g.subject_id].append(g.value)

    recommendations = []
    for sub_id, vals in subject_stats.items():
        avg = sum(vals) / len(vals)
        if avg < 10: # Seuil critique
            subject = Subject.query.get(sub_id)
            recommendations.append({
                'subject': subject.name,
                'average': avg,
                'priority': 'High' if avg < 7 else 'Medium'
            })

    return recommendations

def generate_action_plan(student_id):
    """
    Génère un plan d'action personnalisé.
    """
    recs = recommend_soutien(student_id)
    attendance = Attendance.query.filter_by(student_id=student_id).all()

    absences = [a for a in attendance if a.status == 'absent']

    plan = {
        'status': 'Alerte' if recs else 'Normal',
        'steps': [],
        'observations': []
    }

    if recs:
        plan['steps'].append(f"Suivre des cours de remédiation en : {', '.join([r['subject'] for r in recs])}")

    if len(absences) > 3:
        plan['observations'].append("Le taux d'absence élevé impacte probablement les résultats.")
        plan['steps'].append("Entretien avec le conseiller de discipline pour justifier les absences.")

    if not plan['steps']:
        plan['steps'].append("Continuer sur cette lancée.")

    return plan
