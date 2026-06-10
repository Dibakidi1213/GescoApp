import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func, case
from models import db, User, School, Class, Student, Subject, Teacher, Grade, Attendance, Conduct, Incident, Bulletin, AuditLog

class DashboardUtils:
    """Utilitaire pour la génération de statistiques et métriques de dashboard."""

    @staticmethod
    def generate_admin_stats(school_id):
        """Génère les statistiques globales pour l'administrateur de l'école."""

        # 1. Moyennes générales école par période (graphique linéaire)
        periods = ['1èP', '2èP', 'EXA1', '3èP', '4èP', 'EXA2']
        avg_per_period = []
        for p in periods:
            avg = db.session.query(func.avg(Grade.value)).join(Student).join(Class).filter(Class.school_id == school_id, Grade.period == p).scalar()
            avg_per_period.append(round(float(avg or 0), 2))

        # 2. Taux de présence global (camembert)
        attendance_counts = db.session.query(Attendance.status, func.count(Attendance.id)).join(Class).filter(Class.school_id == school_id).group_by(Attendance.status).all()
        attendance_stats = dict(attendance_counts)

        # 3. Conduite moyenne école (barres par classe)
        conduct_by_class = db.session.query(Class.name, func.avg(Conduct.severity)).join(Student, Student.class_id == Class.id).join(Conduct, Conduct.student_id == Student.id).filter(Class.school_id == school_id).group_by(Class.name).all()
        conduct_labels = [r[0] for r in conduct_by_class]
        conduct_data = [round(float(r[1] or 0), 2) for r in conduct_by_class]

        # 4. Élèves en difficulté (Moyenne < 50%)
        # On définit le seuil à 10 pour un maxima de 20 par exemple
        struggling = db.session.query(Student.name, func.avg(Grade.value).label('avg_grade')).join(Grade).join(Class).filter(Class.school_id == school_id).group_by(Student.id).having(func.avg(Grade.value) < 10).limit(5).all()
        struggling_list = [{"name": r[0], "average": round(float(r[1]), 2)} for r in struggling]

        # 5. Incidents du mois (tendance)
        month_ago = datetime.utcnow() - timedelta(days=30)
        incident_trend = db.session.query(func.date(Incident.recorded_at), func.count(Incident.id)).join(Student).join(Class).filter(Class.school_id == school_id, Incident.recorded_at >= month_ago).group_by(func.date(Incident.recorded_at)).all()

        return {
            'period_evolution': {'labels': periods, 'data': avg_per_period},
            'attendance_dist': {'labels': list(attendance_stats.keys()), 'data': list(attendance_stats.values())},
            'conduct_by_class': {'labels': conduct_labels, 'data': conduct_data},
            'struggling_students': struggling_list,
            'incident_trend': {'labels': [str(r[0]) for r in incident_trend], 'data': [r[1] for r in incident_trend]},
            'alerts': {
                'pending_grades': Grade.query.filter_by(status='submitted').count(),
                'critical_incidents': Incident.query.filter_by(severity='Critique').count()
            }
        }

    @staticmethod
    def generate_secretaire_stats(school_id, period='1èP'):
        """Statistiques pour le secrétaire."""
        # 1. Notes soumises vs non soumises par classe
        stats_saisie = db.session.query(
            Class.name,
            func.count(Grade.id).filter(Grade.period == period).label('count')
        ).join(Student).join(Grade).filter(Class.school_id == school_id).group_by(Class.name).all()

        # 2. Moyennes par classe
        class_avgs = db.session.query(Class.name, func.avg(Grade.value)).join(Student).join(Grade).filter(Class.school_id == school_id, Grade.period == period).group_by(Class.name).all()

        return {
            'submission_by_class': {'labels': [r[0] for r in stats_saisie], 'data': [r[1] for r in stats_saisie]},
            'class_averages': {'labels': [r[0] for r in class_avgs], 'data': [round(float(r[1] or 0), 2) for r in class_avgs]},
            'bulletin_stats': {
                'generated': Bulletin.query.join(Student).join(Class).filter(Class.school_id == school_id).count(),
                'total': Student.query.join(Class).filter(Class.school_id == school_id).count()
            }
        }

    @staticmethod
    def generate_professeur_stats(user_id):
        """Statistiques pour un professeur."""
        teacher_assignments = Teacher.query.filter_by(user_id=user_id).all()

        subject_data = []
        for ta in teacher_assignments:
            grades = Grade.query.filter_by(subject_id=ta.subject_id, teacher_id=ta.id).all()
            values = [g.value for g in grades]
            subject_data.append({
                'label': f"{ta.subject.name} ({ta.class_level.name})",
                'avg': round(float(np.mean(values) if values else 0), 2),
                'count': len(values)
            })

        return {
            'subjects': subject_data,
            'pending_submissions': Grade.query.filter_by(teacher_id=user_id, status='draft').count()
        }

    @staticmethod
    def generate_discipline_stats(school_id):
        """Statistiques pour la discipline."""
        incident_types = db.session.query(Incident.category, func.count(Incident.id)).join(Student).join(Class).filter(Class.school_id == school_id).group_by(Incident.category).all()

        # Heatmap Absences par jour (Données brutes pour JS)
        absences = db.session.query(func.extract('dow', Attendance.date).label('day'), Class.name, func.count(Attendance.id)).join(Class).filter(Class.school_id == school_id, Attendance.status == 'absent').group_by('day', Class.name).all()

        return {
            'incident_types': {'labels': [r[0] for r in incident_types], 'data': [r[1] for r in incident_types]},
            'absences_heatmap': [{'day': int(r[0]), 'class': r[1], 'count': r[2]} for r in absences]
        }
