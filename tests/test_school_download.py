#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier les téléchargements de base de données par école
"""
import requests
import os
from datetime import datetime

# Configuration
BASE_URL = 'http://localhost:5000'
ADMIN_USERNAME = 'admin_test'
ADMIN_PASSWORD = 'admin_test'

def test_downloads():
    """Tester les deux types de téléchargement"""
    session = requests.Session()
    
    # 1. Connexion
    print("1. Connexion...")
    login_response = session.post(f'{BASE_URL}/login', data={
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD
    })
    print(f"   Status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"   ❌ Erreur de connexion")
        return
    
    # 2. Télécharger la DB complète du système
    print("\n2. Téléchargement de la DB complète...")
    response = session.get(f'{BASE_URL}/admin/download-database')
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")
    print(f"   Content-Disposition: {response.headers.get('Content-Disposition')}")
    print(f"   File size: {len(response.content)} bytes")
    
    if response.status_code == 200:
        # Sauvegarder le fichier
        filename = f"test_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"   ✅ Fichier téléchargé: {filename}")
        os.system(f'dir "{filename}"')
    else:
        print(f"   ❌ Erreur: {response.text[:200]}")
    
    # 3. Récupérer la page des années pour avoir les IDs des écoles et années
    print("\n3. Récupération de la page des années scolaires...")
    page_response = session.get(f'{BASE_URL}/admin/academic-years')
    if page_response.status_code != 200:
        print(f"   ❌ Impossible de récupérer la page: {page_response.status_code}")
        return
    
    # Parser le HTML pour trouver les links de téléchargement par école
    from html.parser import HTMLParser
    
    class LinkExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.school_year_links = []
        
        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                attrs_dict = dict(attrs)
                href = attrs_dict.get('href', '')
                if '/download-school-database/' in href:
                    self.school_year_links.append(href)
    
    extractor = LinkExtractor()
    extractor.feed(page_response.text)
    
    print(f"   Trouvé {len(extractor.school_year_links)} liens de téléchargement par école")
    
    # 4. Tester les téléchargements par école
    if extractor.school_year_links:
        print("\n4. Téléchargement par école...")
        for i, link in enumerate(extractor.school_year_links[:2], 1):  # Tester les 2 premiers
            print(f"\n   {i}. Téléchargement: {link}")
            school_response = session.get(f'{BASE_URL}{link}')
            print(f"      Status: {school_response.status_code}")
            print(f"      File size: {len(school_response.content)} bytes")
            
            if school_response.status_code == 200:
                filename_header = school_response.headers.get('Content-Disposition', '')
                # Extraire le nom du fichier
                if 'filename=' in filename_header:
                    filename = filename_header.split('filename="')[-1].rstrip('"')
                else:
                    filename = f"test_school_backup_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                
                with open(filename, 'wb') as f:
                    f.write(school_response.content)
                print(f"      ✅ Fichier téléchargé: {filename}")
            else:
                print(f"      ❌ Erreur: {school_response.text[:200]}")

if __name__ == '__main__':
    print("=" * 60)
    print("Test des téléchargements de base de données")
    print("=" * 60)
    test_downloads()
    print("\n" + "=" * 60)
    print("Tests terminés")
    print("=" * 60)
