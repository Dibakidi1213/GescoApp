from flask import Blueprint, request, jsonify, g
from models import db, School, Class, User
from roles import admin_required
from forms import SchoolForm, ClassForm
from auth import token_required

admin_bp = Blueprint('admin', __name__)

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
        return jsonify({'message': 'École créée', 'id': new_school.id}), 201
    return jsonify({'errors': form.errors}), 400

@admin_bp.route('/classes', methods=['POST'])
@token_required
@admin_required
def create_class():
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

@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users():
    school_id = request.args.get('school_id')
    users = User.query.filter_by(school_id=school_id).all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'role': u.role
    } for u in users]), 200
