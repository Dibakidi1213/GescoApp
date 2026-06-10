# GescoApp

Application de gestion scolaire Flask + MySQL avec architecture multi-niveaux.

## Architecture des rôles

L'application utilise une architecture à **trois niveaux d'administration** :

### 🔴 **Super Administrateur** (`super_admin`)
- **Rôle global** : Gestion de toute l'application
- **Permissions** :
  - Créer et gérer toutes les écoles
  - Créer tous types d'utilisateurs pour toutes les écoles
  - Accès à toutes les fonctionnalités
- **Dashboard** : Vue d'ensemble globale (stats écoles, utilisateurs totaux)

### 🟡 **Administrateur d'école** (`school_admin`)
- **Rôle par école** : Gestion d'une école spécifique
- **Permissions** :
  - Modifier les informations de son école (nom, adresse, contact)
  - Créer des secrétaires et professeurs pour son école
  - Gérer les élèves, paiements, sections de son école
- **Dashboard** : Vue de son école avec lien de modification

### 🟢 **Discipline** (`discipline`)
- **Rôle financier** : Gestion des paiements de l'école
- **Permissions** :
  - Enregistrer les paiements des frais scolaires
  - Voir l'historique des paiements
  - Accès aux données de l'école liées aux paiements

### 🔵 **Secrétaire** (`secretary`)
- **Rôle opérationnel** : Support administratif et gestion des notes
- **Permissions** :
  - Inscription des élèves
  - Centralise les cotes saisis par les professeurs
  - Saisie des cotes des élèves par classe, niveau et cours
  - Visualisation des cotes globales par classe et par période (4 périodes pour secondaires, 6 pour primaires)
  - Impression des bulletins des élèves
  - Accès en lecture aux données de l'école

### 🔵 **Professeur** (`professor`)
- **Rôle pédagogique** : Saisie des notes
- **Permissions** :
  - Voir ses cours et élèves
  - Saisir les notes via interface AJAX

## Paramétrisation par école

Chaque école est **complètement isolée** :
- Données propres (élèves, sections, cours, utilisateurs, paiements)
- Paramétrage indépendant des informations de l'école
- Gestion autonome par les administrateurs d'école

## Installation

1. **Base de données** :
   ```bash
   mysql -u root -p < schema.sql
   ```

2. **Migration des rôles** (si base existante) :
   ```bash
   mysql -u root -p gescoapp < migration_roles.sql
   ```

3. **Environnement virtuel** :
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration initiale** :
   ```bash
   python setup.py
   ```
   Ce script crée automatiquement :
   - Un super administrateur (`superadmin` / `super123`)
   - Une école de démonstration
   - Un administrateur d'école (`admin_demo` / `admin123`)

5. **Configuration** (optionnel) :
   - Modifier `config.py` avec vos paramètres MySQL

6. **Lancement** :
   ```bash
   python app.py
   ```

## Premiers pas

Après installation, connectez-vous avec :

- **Super Admin** : `superadmin` / `super123`
  - Créez de nouvelles écoles
  - Gérez les administrateurs d'écoles

- **Admin École Démo** : `admin_demo` / `admin123`
  - Modifiez les informations de l'école
  - Créez des secrétaires et professeurs
  - Gérez les élèves et paiements

## Structure du projet

```
GescoApp/
├── app.py                    # Application Flask
├── config.py                 # Configuration DB
├── models/__init__.py        # Modèles SQLAlchemy avec isolation école
├── routes/
│   ├── auth.py              # Authentification et redirection par rôle
│   ├── admin.py             # Routes admin avec permissions granulaires
│   └── professor.py         # Interface professeur
├── templates/
│   ├── admin/
│   │   ├── dashboard.html   # Dashboard adaptatif selon rôle
│   │   ├── schools.html     # Gestion écoles (super_admin)
│   │   ├── edit_school.html # Modification école (school_admin)
│   │   └── register_user.html # Création utilisateur avec écoles
│   └── ...
├── static/
├── schema.sql               # Création tables avec nouveaux rôles
├── migration_roles.sql      # Migration rôles existants
└── README.md
```

## Fonctionnalités principales

- ✅ **Authentification multi-rôles** avec redirection automatique
- ✅ **Isolation complète par école** (données, utilisateurs)
- ✅ **Gestion écoles** (super_admin uniquement)
- ✅ **Paramétrage écoles** (school_admin de chaque école)
- ✅ **Gestion des paiements** assurée par le caissier
- ✅ **Gestion élèves/paiements** par école
- ✅ **Interface professeur** avec saisie notes AJAX
- ✅ **Bulletins PDF** avec nom d'école (optionnel)

## Workflow de démarrage

1. **Créer un super administrateur** via SQL ou interface
2. **Se connecter** et créer les écoles
3. **Pour chaque école** : créer un administrateur d'école
4. **Chaque admin d'école** configure son école et crée les utilisateurs
5. **Utilisation normale** : secrétaires gèrent élèves/paiements, professeurs saisissent notes

### Code de modification de la table users

ALTER TABLE users MODIFY role ENUM('super_admin','school_admin','secretary','discipline','professor') NOT NULL;
ALTER TABLE users MODIFY school_id INT NULL;
