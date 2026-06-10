from flask import Flask, jsonify
from config import Config
from models import db, User, bcrypt
from flask_login import LoginManager
from auth import auth_bp
from routes_admin import admin_bp
from routes_professeur import professeur_bp
from routes_secretaire import secretaire_bp
from routes_discipline import discipline_bp
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialisation des extensions
    db.init_app(app)
    bcrypt.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Enregistrement des Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(professeur_bp, url_prefix='/api/professeur')
    app.register_blueprint(secretaire_bp, url_prefix='/api/secretaire')
    app.register_blueprint(discipline_bp, url_prefix='/api/discipline')

    # Route de base pour tester le fonctionnement
    @app.route('/')
    def index():
        return jsonify({'message': 'Bienvenue sur l\'API de gestion d\'école'})

    # Création des tables de la base de données
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
