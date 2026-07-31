#!/usr/bin/env python3
"""Test du téléchargement de base de données"""

import requests
import os
from datetime import datetime

# Créer une session avec authentification
session = requests.Session()

# Connexion d'abord
print("1. Connexion...")
login_response = session.post('http://localhost:5000/login', data={
    'username': 'admin_test',
    'password': 'admin_test'
})
print(f"   Status: {login_response.status_code}")

# Essayer le téléchargement
print("\n2. Téléchargement de la DB complète...")
response = session.get('http://localhost:5000/admin/download-database')
print(f"   Status: {response.status_code}")
print(f"   Content-Type: {response.headers.get('Content-Type')}")
print(f"   Content-Disposition: {response.headers.get('Content-Disposition')}")
print(f"   File size: {len(response.content)} bytes")

# Sauvegarder le fichier
if response.status_code == 200:
    filename = f'test_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    with open(filename, 'wb') as f:
        f.write(response.content)
    print(f"   ✅ Fichier téléchargé: {filename}")
    os.system(f'dir {filename}')
else:
    print(f"   ❌ Erreur: {response.text[:200]}")

session.close()
