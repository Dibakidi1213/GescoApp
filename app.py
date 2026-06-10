from flask import Flask, jsonify, render_template
from config import Config
from models import db, User, bcrypt
from flask_login import LoginManager
from auth import auth_bp
from routes_admin import admin_bp
from routes_professeur import professeur_bp
from routes_secretaire import secretaire_bp
from routes_discipline import discipline_bp
from routes_mobile import mobile_bp
from middleware import limiter
from flask_mail import Mail
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialisation des extensions
    db.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    mail = Mail(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login_page'
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Routes Web simples pour les templates
    @app.route('/auth/login')
    def login_page():
        return render_template('auth/login.html')

    @app.route('/auth/reset-password')
    def reset_password_page():
        return render_template('auth/reset_password.html')

    # Enregistrement des Blueprints API
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(professeur_bp, url_prefix='/api/professeur')
    app.register_blueprint(secretaire_bp, url_prefix='/api/secretaire')
    app.register_blueprint(discipline_bp, url_prefix='/api/discipline')
    app.register_blueprint(mobile_bp, url_prefix='/api/mobile')

    @app.route('/')
    def index():
        return jsonify({'message': 'Bienvenue sur l\'API sécurisée de JNC_KALASI'})

    # Gestion des erreurs globales
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify(error="Trop de requêtes", message=str(e.description)), 429

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
