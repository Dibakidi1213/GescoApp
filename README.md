# JNC_KALASI - Plateforme de Gestion Scolaire

Plateforme complète de gestion scolaire développée avec Flask, incluant la gestion des notes, de la discipline, des bulletins officiels (RDC) et des analyses par IA.

## 🚀 Fonctionnalités
- **RBAC (Role Based Access Control)**: Admin, Secrétaire, Professeur, Discipline, Parent.
- **Gestion des Notes**: Saisie par les profs, validation par le secrétariat.
- **Bulletins PDF**: Génération conforme aux modèles officiels (EB/CTEB et Humanités).
- **IA Intégrée**: Détection d'anomalies de cotes et prédiction de comportement.
- **Sécurité**: 2FA (TOTP), JWT pour mobile, Rate limiting, Audit logs.
- **API Mobile**: Support pour application React Native avec mode hors-ligne.

## 🛠️ Installation Locale

1. **Cloner le repository**
   ```bash
   git clone https://github.com/votre-user/JNC_KALASI.git
   cd jnc_kalasi
   ```

2. **Lancer le script de setup**
   ```bash
   bash scripts/setup.sh
   ```

3. **Lancer l'application**
   ```bash
   source venv/bin/activate
   flask run
   ```

## 🌍 Déploiement (PythonAnywhere)

Voir le fichier [DEPLOY.md](./DEPLOY.md) pour les instructions détaillées étape par étape.

## 🧪 Tests
```bash
pytest tests/
```

## 📄 Licence
Propriété de JNC Services.
