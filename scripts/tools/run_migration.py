import sqlite3

conn = sqlite3.connect('gescoapp.db')
with open('migration_deliberation.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

try:
    conn.executescript(sql)
    conn.commit()
    print("Migration successful")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
