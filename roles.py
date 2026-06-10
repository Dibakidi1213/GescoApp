from functools import wraps
from flask import abort, g
from flask_login import current_user

def role_required(roles):
    """
    Décorateur pour restreindre l'accès aux routes en fonction du rôle de l'utilisateur.
    Supporte à la fois Flask-Login (session) et JWT (via g.current_user).
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Priorité à l'utilisateur authentifié par token (API)
            user = getattr(g, 'current_user', None)

            # Sinon on regarde la session
            if not user and current_user.is_authenticated:
                user = current_user

            if not user:
                abort(401) # Non autorisé

            if user.role not in roles:
                abort(403) # Interdit

            # Mettre l'utilisateur effectif dans g pour accès facile dans les routes
            g.effective_user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Raccourcis
def admin_required(f):
    return role_required('admin')(f)

def secretaire_required(f):
    return role_required('secretaire')(f)

def professeur_required(f):
    return role_required('professeur')(f)

def discipline_required(f):
    return role_required('discipline')(f)
