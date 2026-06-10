import jwt
from datetime import datetime, timedelta
from flask import current_app
from models import User

def generate_jwt(user_id, role, school_id, is_refresh=False):
    """Génère un token JWT (access ou refresh)."""
    payload = {
        'user_id': user_id,
        'role': role,
        'school_id': school_id,
        'iat': datetime.utcnow(),
    }

    if is_refresh:
        payload['exp'] = datetime.utcnow() + current_app.config['JWT_REFRESH_EXPIRATION_DELTA']
        payload['refresh'] = True
    else:
        payload['exp'] = datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA']

    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_jwt(token):
    """Vérifie un token JWT et retourne le payload si valide."""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        # Vérification si c'est un token de rafraîchissement utilisé comme accès
        if payload.get('refresh'):
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def refresh_jwt(refresh_token):
    """Rafraîchit un access token à partir d'un refresh token valide."""
    try:
        payload = jwt.decode(refresh_token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        if not payload.get('refresh'):
            return None

        # Générer un nouveau access token
        return generate_jwt(payload['user_id'], payload['role'], payload['school_id'])
    except:
        return None
