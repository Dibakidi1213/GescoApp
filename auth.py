import jwt
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, g
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from forms import LoginForm, UserForm
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'message': 'Token manquant'}), 401

        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user_obj = User.query.get(data['user_id'])
            if not current_user_obj:
                return jsonify({'message': 'Utilisateur non trouvé'}), 401
            # On utilise g pour stocker l'utilisateur via token pour les APIs REST
            g.current_user = current_user_obj
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401

        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    form = UserForm(data=data, meta={'csrf': False}) # Désactiver CSRF pour API
    if form.validate():
        if User.query.filter_by(username=form.username.data).first():
            return jsonify({'message': 'Utilisateur existe déjà'}), 400

        new_user = User(
            username=form.username.data,
            role=form.role.data,
            school_id=form.school_id.data
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Utilisateur créé avec succès'}), 201
    return jsonify({'errors': form.errors}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    form = LoginForm(data=data, meta={'csrf': False})
    if form.validate():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)

            token = jwt.encode({
                'user_id': user.id,
                'role': user.role,
                'exp': datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA']
            }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

            return jsonify({
                'message': 'Connexion réussie',
                'token': token,
                'role': user.role
            }), 200
        return jsonify({'message': 'Identifiants invalides'}), 401
    return jsonify({'errors': form.errors}), 400

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Déconnexion réussie'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_me():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'role': current_user.role,
        'school_id': current_user.school_id
    }), 200
