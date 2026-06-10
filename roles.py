from functools import wraps
from flask import abort, request, g, session
from flask_login import current_user
from jwt_utils import verify_jwt
from models import db, User

def login_required(f):
    """Décorateur combiné supportant Session et JWT."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Vérification JWT (Header Authorization)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
            payload = verify_jwt(token)
            if payload:
                user = db.session.get(User, payload['user_id'])
                if user:
                    # Sécurité: Vérifier si le mot de passe a été changé après l'émission du token
                    iat = payload.get('iat')
                    if iat and user.last_password_change.timestamp() > iat + 1: # Marge de 1s
                        abort(401, description="Token invalide suite au changement de mot de passe.")
                    g.current_user = user
                    return f(*args, **kwargs)
            abort(401, description="JWT Token invalide ou expiré.")

        # 2. Vérification Session (Flask-Login)
        if current_user.is_authenticated:
            g.current_user = current_user
            return f(*args, **kwargs)

        abort(401, description="Authentification requise.")
    return decorated_function

def role_required(roles):
    """Décorateur pour restreindre l'accès par rôle (unique ou liste)."""
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        @login_required # S'assure que l'utilisateur est loggé d'abord
        def decorated_function(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if not user or user.role not in roles:
                abort(403, description="Accès interdit : rôle insuffisant.")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Raccourcis pratiques
def admin_required(f):
    return role_required('admin')(f)

def secretaire_required(f):
    return role_required('secretaire')(f)

def professeur_required(f):
    return role_required('professeur')(f)

def discipline_required(f):
    return role_required('discipline')(f)
