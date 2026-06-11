from flask import Blueprint, request, jsonify, g
from flask_restful import Api, Resource
from models import db, Student, Grade, Attendance, Conduct, Teacher, Subject, Message, User
from roles import login_required, role_required
from datetime import datetime
from middleware import limiter

mobile_bp = Blueprint('mobile', __name__)
api = Api(mobile_bp)

# Application du Rate Limiting spécifique à l'API mobile
@mobile_bp.before_request
@limiter.limit("100 per hour")
def limit_mobile_api():
    pass

class ProfSubjects(Resource):
    @login_required
    @role_required('professeur')
    def get(self):
        user = g.current_user
        subjects = Teacher.query.filter_by(user_id=user.id).all()
        return [{
            'id': s.subject_id,
            'name': s.subject.name,
            'coefficient': s.subject.coefficient,
            'class_id': s.class_id,
            'class_name': s.class_level.name
        } for s in subjects], 200

class ProfGrades(Resource):
    @login_required
    @role_required('professeur')
    def post(self):
        data = request.get_json()
        student_id = data.get('student_id')
        subject_id = data.get('subject_id')
        value = data.get('value')
        period = data.get('period')

        # Vérification attribution
        teacher = Teacher.query.filter_by(user_id=g.current_user.id, subject_id=subject_id).first()
        if not teacher:
            return {'message': 'Non autorisé pour cette matière'}, 403

        grade = Grade(
            student_id=student_id,
            subject_id=subject_id,
            teacher_id=teacher.id,
            value=value,
            period=period,
            status='submitted'
        )
        db.session.add(grade)
        db.session.commit()
        return {'message': 'Note enregistrée'}, 201

class ParentChildren(Resource):
    @login_required
    @role_required('parent')
    def get(self):
        # On suppose que le rôle 'parent' a été ajouté au User
        children = g.current_user.children.all()
        return [{
            'id': c.id,
            'name': c.name,
            'class': c.current_class.name if c.current_class else 'N/A'
        } for c in children], 200

class ChildDetails(Resource):
    @login_required
    @role_required('parent')
    def get(self, child_id):
        child = Student.query.get_or_404(child_id)
        # Sécurité : vérifier que c'est bien son enfant
        if g.current_user not in child.parents:
            return {'message': 'Accès non autorisé'}, 403

        grades = Grade.query.filter_by(student_id=child_id).all()
        attendance = Attendance.query.filter_by(student_id=child_id).all()
        conduct = Conduct.query.filter_by(student_id=child_id).all()

        return {
            'grades': [{'subject': g.subject.name, 'value': g.value, 'period': g.period} for g in grades],
            'attendance': [{'date': a.date.isoformat(), 'status': a.status} for a in attendance],
            'conduct': [{'date': c.recorded_at.isoformat(), 'type': c.type, 'severity': c.severity} for c in conduct]
        }, 200

class Messaging(Resource):
    @login_required
    def post(self):
        data = request.get_json()
        msg = Message(
            sender_id=g.current_user.id,
            receiver_id=data.get('receiver_id'),
            content=data.get('content')
        )
        db.session.add(msg)
        db.session.commit()
        return {'message': 'Message envoyé'}, 201

api.add_resource(ProfSubjects, '/professeur/subjects')
api.add_resource(ProfGrades, '/professeur/grades')
api.add_resource(ParentChildren, '/parent/children')
api.add_resource(ChildDetails, '/parent/child/<int:child_id>')
api.add_resource(Messaging, '/messages')
