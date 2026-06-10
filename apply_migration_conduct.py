import sqlite3

try:
    conn = sqlite3.connect('gescoapp.db')
    cursor = conn.cursor()
    with open('migration_add_conduct_grades.sql', 'r') as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()
    print("Migration applied successfully.")
except Exception as e:
    print(f"Error applying migration: {e}")
finally:
    if conn:
        conn.close()
