#!/bin/bash
# Script d'installation automatisée pour PythonAnywhere ou Local

echo "--- Début de l'installation ---"

# Créer l'environnement virtuel si inexistant
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[OK] Environnement virtuel créé"
fi

# Activer l'environnement
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
echo "[OK] Dépendances installées"

# Créer le dossier d'instance
mkdir -p instance
mkdir -p bulletins

# Initialiser la base de données
export FLASK_APP=app.py
flask db init 2>/dev/null || echo "Migrations déjà initialisées"
flask db migrate -m "Initial migration"
flask db upgrade

echo "--- Installation terminée avec succès ---"
