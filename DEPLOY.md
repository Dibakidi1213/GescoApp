# Guide de Déploiement - PythonAnywhere

## 1. Préparation GitHub
- Créez un repository privé sur GitHub.
- Pushez votre code : `git push origin main`.

## 2. Configuration PythonAnywhere
1. Connectez-vous à votre compte.
2. Ouvrez un **Bash Console**.
3. Clonez le projet :
   ```bash
   git clone https://github.com/votre-user/JNC_KALASI.git
   cd jnc_kalasi
   ```
4. Lancez le script de setup :
   ```bash
   bash scripts/setup.sh
   ```

## 3. Configuration de l'App Web
1. Allez dans l'onglet **Web**.
2. Cliquez sur **Add a new web app**.
3. Choisissez **Manual Configuration** (Python 3.12).
4. Configurez les chemins :
   - **Source code**: `/home/votreusername/jnc_kalasi`
   - **Working directory**: `/home/votreusername/jnc_kalasi`
   - **Virtualenv**: `/home/votreusername/jnc_kalasi/venv`

## 4. Variables d'Environnement
Dans l'onglet Web, section "Environment variables" (ou via un fichier .env si vous utilisez python-dotenv) :
- `SECRET_KEY`: (Générez une clé complexe)
- `JWT_SECRET_KEY`: (Générez une clé complexe)
- `DATABASE_URL`: (Laissez vide pour SQLite ou configurez votre DB Postgres PythonAnywhere)

## 5. Configuration WSGI
Modifiez le fichier WSGI (`/var/www/votreusername_pythonanywhere_com_wsgi.py`) :
```python
import sys
import os

path = '/home/votreusername/jnc_kalasi'
if path not in sys.path:
    sys.path.append(path)

from app import create_app
application = create_app()
```

## 6. Base de Données
Si vous utilisez PostgreSQL sur PythonAnywhere :
1. Allez dans l'onglet **Databases**.
2. Créez une DB Postgres.
3. Notez l'URL (`postgresql://user:pass@host/db`).
4. Mettez à jour la variable `DATABASE_URL`.

## 7. Backups Automatiques
Allez dans l'onglet **Tasks** et ajoutez une tâche quotidienne :
```bash
/home/votreusername/jnc_kalasi/scripts/backup.sh
```
