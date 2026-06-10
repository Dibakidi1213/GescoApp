import re
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, render_template, url_for, g
from flask_login import login_user, logout_user, current_user
from models import db, User
from jwt_utils import generate_jwt
from middleware import audit_logger, limiter
from roles import admin_required, login_required
import pyotp

auth_bp = Blueprint('auth', __name__)

def validate_password_complexity(password):
    """Vérifie la complexité du mot de passe (min 8 car, 1 maj, 1 min, 1 chiffre)."""
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if not re.search(r"[a-z]", password):
        return False, "Le mot de passe doit contenir au moins une minuscule."
    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une majuscule."
    if not re.search(r"[0-9]", password):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    return True, ""

@auth_bp.route('/register', methods=['POST'])
@login_required
@admin_required
def register():
    """Route d'inscription réservée aux administrateurs."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    school_id = data.get('school_id')

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'message': 'Utilisateur ou email déjà existant'}), 400

    valid, msg = validate_password_complexity(password)
    if not valid:
        return jsonify({'message': msg}), 400

    new_user = User(
        username=username,
        email=email,
        role=role,
        school_id=school_id
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    audit_logger(g.current_user.id, 'REGISTER_USER', f'Création de l\'utilisateur {username} (rôle: {role})')
    return jsonify({'message': 'Utilisateur créé avec succès', 'id': new_user.id}), 201

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per 10 minutes")
def login():
    data = request.get_json()
    identifier = data.get('username') or data.get('email')
    password = data.get('password')
    otp_token = data.get('otp_token') # Optionnel si 2FA activé

    user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()

    # Protection Brute Force
    if user and user.failed_login_attempts >= 5:
        if (datetime.utcnow() - user.last_login_attempt).seconds < 600:
            audit_logger(user.id, 'LOGIN', 'Compte bloqué temporairement (Brute Force)', False)
            return jsonify({'message': 'Compte bloqué pour 10 minutes suite à trop d\'échecs.'}), 429

    if user and user.check_password(password):
        # Vérification 2FA
        if user.is_2fa_enabled:
            if not otp_token:
                return jsonify({'message': 'Code 2FA requis', '2fa_required': True}), 206
            totp = pyotp.TOTP(user.two_factor_secret)
            if not totp.verify(otp_token):
                audit_logger(user.id, 'LOGIN', 'Échec 2FA', False)
                return jsonify({'message': 'Code 2FA invalide'}), 401

        # Réinitialiser les tentatives
        user.failed_login_attempts = 0
        user.last_login_attempt = datetime.utcnow()
        db.session.commit()

        login_user(user)
        audit_logger(user.id, 'LOGIN', f'Connexion réussie ({user.username})')

        access_token = generate_jwt(user.id, user.role, user.school_id)
        refresh_token = generate_jwt(user.id, user.role, user.school_id, is_refresh=True)

        return jsonify({
            'message': 'Connexion réussie',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'role': user.role
        }), 200

    if user:
        user.failed_login_attempts += 1
        user.last_login_attempt = datetime.utcnow()
        db.session.commit()
        audit_logger(user.id, 'LOGIN', 'Mot de passe invalide', False)

    return jsonify({'message': 'Identifiants invalides'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    if current_user.is_authenticated:
        audit_logger(current_user.id, 'LOGOUT', 'Déconnexion volontaire')
        logout_user()
    return jsonify({'message': 'Déconnexion réussie'}), 200

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    # Nécessite d'être loggé (via session ou JWT)
    # Dans un vrai cas, on utiliserait le décorateur @login_required de roles.py
    # Mais ici on va faire simple pour la démo
    if not current_user.is_authenticated:
         return jsonify({'message': 'Non authentifié'}), 401

    data = request.get_json()
    new_password = data.get('new_password')

    valid, msg = validate_password_complexity(new_password)
    if not valid:
        return jsonify({'message': msg}), 400

    current_user.set_password(new_password)
    current_user.last_password_change = datetime.utcnow()
    db.session.commit()

    audit_logger(current_user.id, 'PASSWORD_CHANGE', 'Changement de mot de passe réussi')
    return jsonify({'message': 'Mot de passe mis à jour. Veuillez vous reconnecter.'}), 200

@auth_bp.route('/reset-password-request', methods=['POST'])
def reset_password_request():
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        # Ici on enverrait un email avec un token sécurisé
        audit_logger(user.id, 'PASSWORD_RESET_REQ', 'Demande de réinitialisation envoyée')
        return jsonify({'message': 'Si cet email existe, un lien de réinitialisation a été envoyé.'}), 200
    return jsonify({'message': 'Si cet email existe, un lien de réinitialisation a été envoyé.'}), 200
