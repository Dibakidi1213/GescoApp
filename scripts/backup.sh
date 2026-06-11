#!/bin/bash
# Script de backup quotidien pour SQLite ou PostgreSQL

BACKUP_DIR="backups"
DATE=$(date +%Y-%m-%d_%H%M)
mkdir -p $BACKUP_DIR

echo "--- Début du backup ($DATE) ---"

# Cas SQLite
if [ -f "instance/jnc_kalasi.db" ]; then
    cp instance/jnc_kalasi.db "$BACKUP_DIR/jnc_kalasi_backup_$DATE.db"
    echo "[OK] Backup SQLite effectué"
fi

# Cas PostgreSQL (si DATABASE_URL est défini)
if [[ $DATABASE_URL == postgres* ]]; then
    pg_dump $DATABASE_URL > "$BACKUP_DIR/pg_backup_$DATE.sql"
    echo "[OK] Backup PostgreSQL effectué"
fi

# Compression et Nettoyage (Garder 30 jours)
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" -C $BACKUP_DIR .
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "--- Backup terminé ---"
