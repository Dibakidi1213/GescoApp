#!/bin/bash
# Script d'exécution des tests avec couverture de code

echo "--- Démarrage des tests JNC_KALASI ---"

# Installation de pytest-cov si nécessaire
pip install pytest-cov coverage

# Exécution des tests
export PYTHONPATH=$PYTHONPATH:.
pytest tests/ --cov=./ --cov-report=term-missing --cov-report=html

echo "--- Rapport de couverture généré dans htmlcov/index.html ---"
