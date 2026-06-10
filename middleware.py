from flask import request, g, session, abort
from datetime import datetime
from models import db, AuditLog
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialisation du Limiter (sera configuré dans app.py)
limiter = Limiter(key_func=get_remote_address)

def audit_logger(user_id, action, details, success=True):
    """Enregistre un événement dans le journal d'audit."""
    status = "SUCCESS" if success else "FAILURE"
    log = AuditLog(
        user_id=user_id,
        action=f"{action} [{status}]",
        details=details,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

def session_timeout_middleware(app):
    """Middleware pour gérer le timeout de session par inactivité."""
    @app.before_request
    def check_session_timeout():
        session.permanent = True
        # Flask-Login gère déjà une partie de cela via PERMANENT_SESSION_LIFETIME
        # mais on peut forcer des vérifications personnalisées ici si besoin.
        pass
