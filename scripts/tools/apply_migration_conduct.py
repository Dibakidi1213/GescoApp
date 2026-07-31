import os
import sqlite3

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    conn = sqlite3.connect(os.path.join(PROJECT_ROOT, 'gescoapp.db'))
    cursor = conn.cursor()
    migration_path = os.path.join(PROJECT_ROOT, 'migrations', 'sql', 'migration_add_conduct_grades.sql')
    with open(migration_path, 'r') as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()
    print("Migration applied successfully.")
except Exception as e:
    print(f"Error applying migration: {e}")
finally:
    if conn:
        conn.close()
